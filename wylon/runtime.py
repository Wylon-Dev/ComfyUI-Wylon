"""ComfyUI execution lifecycle: journal first, poll, download, return native media."""
from __future__ import annotations

import asyncio
import base64
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import uuid

import folder_paths
from comfy_api.latest import InputImpl, io, ui

from .client import WylonClient, WylonError
from .credentials import get_store
from .contracts import IMAGE_MODELS, VIDEO_MODELS
from .journal import Journal, STATUSES
from .media import IMAGE_RESULT_LIMIT, load_image

API_BASE = 'https://api.wylon.cn/v1'
IMAGE_LIMIT = IMAGE_RESULT_LIMIT
VIDEO_LIMIT = 1024 * 1024 * 1024


def client() -> WylonClient:
    key = get_store().effective_key()
    if not key:
        raise ValueError('Configure an API key in the Wylon panel or set WYLON_API_KEY / 请在Wylon面板或服务端环境变量中配置密钥')
    return WylonClient(key, os.environ.get('WYLON_BASE_URL', API_BASE).strip())


def journal() -> Journal:
    return Journal(Path(folder_paths.get_user_directory()) / 'wylon')


def parse_extra(text: str) -> dict:
    if not isinstance(text, str) or len(text) > 65536:
        raise ValueError('Advanced parameters must be a JSON object under 64 KiB / 高级参数须为小于64 KiB的JSON对象')
    try:
        result = json.loads(text or '{}')
    except (json.JSONDecodeError, ValueError):
        raise ValueError('Invalid advanced JSON / 高级参数JSON格式错误') from None
    if not isinstance(result, dict):
        raise ValueError('Advanced parameters must be a JSON object / 高级参数必须为JSON对象')
    return result


def interrupt() -> None:
    import comfy.model_management
    comfy.model_management.throw_exception_if_processing_interrupted()


def status(node_id: str | None, state: str, started: float, task_id: str = '') -> None:
    server_module = sys.modules.get('server')
    instance = getattr(getattr(server_module, 'PromptServer', None), 'instance', None)
    if instance is not None and node_id is not None:
        instance.send_sync('wylon.status', {
            'node_id': str(node_id), 'status': state, 'task_id': task_id,
            'elapsed': round(time.monotonic() - started, 1),
        }, getattr(instance, 'client_id', None))


def _save_ui(path: Path, kind: str):
    root = Path(folder_paths.get_output_directory()).resolve()
    relative = path.resolve().relative_to(root)
    result = ui.SavedResult(relative.name, relative.parent.as_posix(), io.FolderType.output)
    return ui.PreviewVideo([result]) if kind == 'video' else ui.SavedImages([result])


async def execute_media(cls, kind: str, payload: dict | None = None, *, mode: str = 'async', task_id: str = '') -> io.NodeOutput:
    started = time.monotonic()
    node_id = getattr(cls.hidden, 'unique_id', None)
    model = payload.get('model', '') if payload else ''
    history = journal()
    known_id = task_id
    if task_id and not model:
        previous = next((row for row in history.list() if row['id'] == task_id), None)
        model = previous['model'] if previous else ''
    path = None
    active_key = ''
    terminal_state = ''

    def update(task: dict):
        nonlocal model, terminal_state
        remote_model = task.get('model')
        if remote_model is not None and remote_model != '':
            if not isinstance(remote_model, str) or remote_model not in (IMAGE_MODELS if kind == 'image' else VIDEO_MODELS):
                raise ValueError('Invalid remote model for task kind / 远程任务模型无效')
        state = 'expired' if task.get('file_status') == 'expired' else task.get('status', 'unknown')
        if not isinstance(state, str) or state not in STATUSES:
            raise ValueError('Invalid remote task status / 远程任务状态无效')
        model = remote_model or model
        if state in ('failed', 'cancelled', 'expired'):
            terminal_state = state
        if model:
            history.record(known_id, kind, model, state)
        status(node_id, state, started, known_id)

    try:
        api = client()
        active_key = api.api_key
        async with api:
            interrupt()
            if payload is not None:
                status(node_id, 'submitting', started)
                if kind == 'image' and mode == 'sync':
                    final = await api.generate_sync(payload)
                else:
                    initial = await api.create(payload)
                    known_id = initial.get('id', '')
                    if not isinstance(known_id, str) or not known_id:
                        raise ValueError('Wylon accepted no usable task ID; check console before retrying / 未返回任务ID，请先核实控制台')
                    try:
                        update({**initial, 'status': initial.get('status', 'queued')})
                    except Exception:
                        raise RuntimeError(f'Task created but local journal failed; resume task {known_id} / 任务已创建但记录失败，请保存任务ID') from None
                    final = await api.wait(known_id, kind, timeout=900, on_status=update, interrupt=interrupt)
            else:
                # Read-only recovery; never creates a new generation.
                final = await api.wait(known_id, kind, timeout=900, on_status=update, interrupt=interrupt)
            status(node_id, 'downloading', started, known_id)
            output = Path(folder_paths.get_output_directory()) / 'wylon'
            output.mkdir(parents=True, exist_ok=True)
            path = output / (uuid.uuid4().hex + ('.mp4' if kind == 'video' else '.png'))
            if kind == 'image':
                data = final.get('data')
                if not isinstance(data, list) or not data or not isinstance(data[0], dict):
                    raise ValueError('Wylon image result has no image / 生图结果缺少图片')
                item = data[0]
                if item.get('url'):
                    await api.download(item['url'], path, IMAGE_LIMIT, interrupt=interrupt)
                    media = load_image(path)
                elif item.get('b64_json'):
                    encoded = item['b64_json']
                    if not isinstance(encoded, str) or len(encoded) > IMAGE_LIMIT * 4 // 3 + 4:
                        raise ValueError('Image result exceeds download limit / 图片结果过大')
                    try:
                        raw = base64.b64decode(encoded, validate=True)
                    except (ValueError, TypeError):
                        raise ValueError('Invalid Base64 image response / 图片Base64无效') from None
                    if len(raw) > IMAGE_LIMIT:
                        raise ValueError('Image result exceeds download limit / 图片结果过大')
                    interrupt()
                    fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '-', suffix='.part', dir=output)
                    try:
                        with os.fdopen(fd, 'wb') as stream:
                            stream.write(raw)
                            stream.flush()
                            os.fsync(stream.fileno())
                        media = load_image(Path(temporary))
                        interrupt()
                        os.replace(temporary, path)
                    finally:
                        Path(temporary).unlink(missing_ok=True)
                else:
                    raise ValueError('Wylon image result has no URL or Base64 / 图片结果无可用数据')
            else:
                url = (final.get('content') or {}).get('video_url')
                if not isinstance(url, str) or not url:
                    raise ValueError('Wylon video result has no URL / 视频结果缺少下载地址')
                await api.download(url, path, VIDEO_LIMIT, interrupt=interrupt)
                media = InputImpl.VideoFromFile(str(path))
                media.get_dimensions()  # Probe, without decoding all video frames.
            if known_id and model:
                history.record(known_id, kind, model, 'downloaded')
            status(node_id, 'downloaded', started, known_id)
            return io.NodeOutput(media, known_id, str(path), ui=_save_ui(path, kind))
    except (Exception, asyncio.CancelledError) as exc:
        state = terminal_state or ('interrupted' if isinstance(exc, asyncio.CancelledError) or 'Interrupt' in type(exc).__name__ else 'error')
        if known_id and model:
            try:
                history.record(known_id, kind, model, state)
            except Exception:
                pass
        try:
            status(node_id, state, started, known_id)
        except Exception:
            pass
        if path is not None:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
        if isinstance(exc, asyncio.CancelledError):
            raise
        # Include recoverable ID even for host interrupts, download or codec errors.
        if known_id:
            safe = WylonError(str(exc), api_key=active_key)
            raise RuntimeError(f'{safe} [task_id={known_id}; use a Wylon Resume node / 可使用恢复节点]') from None
        if active_key and active_key in str(exc):
            raise WylonError(str(exc), api_key=active_key) from None
        raise
