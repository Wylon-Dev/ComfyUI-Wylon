"""Async Wylon transport. Create calls are never retried automatically."""
import asyncio
import ipaddress
import json
import os
import re
import tempfile
import time
from pathlib import Path
from urllib.parse import quote, unquote, urljoin, urlsplit
import aiohttp
from yarl import URL
from .contracts import validate_media_url


def _redact(message, api_key=''):
    text = str(message)
    if api_key:
        text = text.replace(api_key, '[REDACTED]')
    text = re.sub(r'data:[^\s\"\'<>]+', '[MEDIA REDACTED]', text, flags=re.I)
    text = re.sub(r'https?://[^\s\"\'<>]+', '[URL REDACTED]', text, flags=re.I)
    text = re.sub(r'Bearer\s+[^\s\"\'<>]+', 'Bearer [REDACTED]', text, flags=re.I)
    return text[:2000]


class WylonError(RuntimeError):
    def __init__(self, message, *, api_key='', task_id=None, http_status: int | None = None):
        self.task_id = task_id
        self.http_status = http_status
        safe = _redact(message, api_key)
        if task_id:
            safe += ' (task_id=' + _redact(task_id, api_key) + ')'
        super().__init__(safe)


class _PublicResolver(aiohttp.resolver.ThreadedResolver):
    async def resolve(self, host, port=0, family=0):
        resolved = await super().resolve(host, port, family)
        if any(not ipaddress.ip_address(item['host']).is_global for item in resolved):
            raise OSError('Asset hostname resolved to a private address')
        return resolved


def _local_origin(url):
    try:
        parsed = urlsplit(url)
        host = parsed.hostname
        if parsed.scheme == 'http' and host and ipaddress.ip_address(host).is_loopback:
            return parsed.scheme, host, parsed.port or 80
    except ValueError:
        pass
    return None


def _check_interrupt(interrupt, task_id=None):
    # Host callbacks may raise their native interruption exception.
    if interrupt is not None and interrupt():
        raise WylonError('Operation interrupted; resume this task to retrieve its result', task_id=task_id)


async def _sleep(delay, interrupt=None, task_id=None):
    end = time.monotonic() + delay
    while time.monotonic() < end:
        _check_interrupt(interrupt, task_id)
        await asyncio.sleep(min(0.1, max(0, end - time.monotonic())))


async def _interruptible(operation, interrupt=None, task_id=None):
    pending = asyncio.ensure_future(operation)
    try:
        while not pending.done():
            _check_interrupt(interrupt, task_id)
            await asyncio.wait({pending}, timeout=0.1)
        _check_interrupt(interrupt, task_id)
        return pending.result()
    finally:
        if not pending.done():
            pending.cancel()
            await asyncio.gather(pending, return_exceptions=True)


class WylonClient:
    def __init__(self, api_key, base_url='https://api.wylon.cn/v1', timeout=60):
        if not isinstance(api_key, str) or not api_key.strip():
            raise WylonError('Configure API Key in the Wylon panel or set WYLON_API_KEY / 请在Wylon配置面板填写API Key，或设置服务器环境变量WYLON_API_KEY')
        parsed = urlsplit(base_url)
        if parsed.username is not None or parsed.password is not None or parsed.query or parsed.fragment or (parsed.scheme != 'https' and not _local_origin(base_url)):
            raise WylonError('API base URL must be HTTPS (loopback HTTP is allowed for local testing)')
        if not parsed.hostname or timeout <= 0:
            raise WylonError('Invalid API base URL or timeout')
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._session = None

    async def __aenter__(self):
        self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout), trust_env=False)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._session is not None:
            await self._session.close()
            self._session = None

    async def _request(self, method, path, payload=None, task_id=None, response_limit=1024 * 1024, *, timeout=None):
        if self._session is None:
            raise WylonError('Use WylonClient as an async context manager', task_id=task_id)
        request_options = {} if timeout is None else {'timeout': aiohttp.ClientTimeout(total=timeout)}
        for attempt in range(3 if method == 'GET' else 1):
            try:
                async with self._session.request(method, self.base_url + path, json=payload, headers={'Authorization': 'Bearer ' + self.api_key}, allow_redirects=False, **request_options) as response:
                    if method == 'GET' and response.status in (408, 429, 500, 502, 503, 504) and attempt < 2:
                        await _sleep(0.2 * (2 ** attempt))
                        continue
                    chunks = []
                    size = 0
                    async for chunk in response.content.iter_chunked(65536):
                        size += len(chunk)
                        if size > response_limit:
                            raise WylonError('API response exceeded safe size limit', task_id=task_id,
                                             http_status=response.status if response.status >= 300 else None)
                        chunks.append(chunk)
                    try:
                        result = json.loads(b''.join(chunks))
                    except (ValueError, UnicodeError):
                        if response.status < 300:
                            raise WylonError(f'API returned invalid JSON (HTTP {response.status})', task_id=task_id) from None
                        result = {}
                    if response.status >= 300:
                        detail = result.get('error', {}) if isinstance(result, dict) else {}
                        message = detail.get('message', 'Request failed') if isinstance(detail, dict) else str(detail)
                        raise WylonError(f'HTTP {response.status}: {message}', api_key=self.api_key,
                                         task_id=task_id, http_status=response.status)
                    if not isinstance(result, dict):
                        raise WylonError('API returned an invalid response object', task_id=task_id)
                    return result
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                if method == 'GET' and attempt < 2:
                    await _sleep(0.2 * (2 ** attempt))
                    continue
                raise WylonError(f'API connection failed: {exc}', api_key=self.api_key, task_id=task_id) from None

    async def create(self, payload):
        return await self._request('POST', '/contents/generations/tasks', payload)

    async def generate_sync(self, payload):
        return await self._request('POST', '/images/generations', payload, response_limit=96 * 1024 * 1024, timeout=180)

    async def get_task(self, task_id):
        if not isinstance(task_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,200}', task_id):
            raise WylonError('Invalid task ID')
        return await self._request('GET', '/contents/generations/tasks/' + quote(task_id, safe='') + '?detail=true', task_id=task_id)

    async def models(self):
        return await self._request('GET', '/models')

    async def wait(self, task_id, kind, timeout=900, on_status=None, interrupt=None):
        if kind not in ('image', 'video'):
            raise WylonError('Invalid task kind', task_id=task_id)
        deadline = time.monotonic() + timeout
        interval = 1.0
        while True:
            _check_interrupt(interrupt, task_id)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise WylonError('Polling timed out; use Wylon Get Task Result later', task_id=task_id)
            try:
                task = await asyncio.wait_for(_interruptible(self.get_task(task_id), interrupt, task_id), timeout=remaining)
            except asyncio.TimeoutError:
                raise WylonError('Polling timed out; use Wylon Get Task Result later', task_id=task_id) from None
            if task.get('id') != task_id:
                raise WylonError('Task identity does not match the requested task ID', task_id=task_id)
            remote_kind = task.get('type')
            if remote_kind != kind:
                if remote_kind in ('image', 'video'):
                    raise WylonError(f'Task is {remote_kind}; use Wylon Get {remote_kind.title()} Task Result', task_id=task_id)
                raise WylonError('Task media kind is missing or unsupported; expected ' + kind, task_id=task_id)
            if on_status is not None:
                on_status(task)
            _check_interrupt(interrupt, task_id)
            status = task.get('status')
            if task.get('file_status') == 'expired' or status in ('failed', 'cancelled', 'expired'):
                error = task.get('error', {})
                message = error.get('message', '') if isinstance(error, dict) else str(error)
                raise WylonError(f'Task {status}; {message}', api_key=self.api_key, task_id=task_id)
            if status == 'succeeded':
                if task.get('file_status') == 'available':
                    return task
                if not task.get('file_status'):
                    raise WylonError('Task succeeded but result availability is missing; use Wylon Get Task Result later', task_id=task_id)
            if status not in ('queued', 'running', 'succeeded'):
                raise WylonError('Unknown task status', task_id=task_id)
            await _sleep(min(interval, max(0, deadline - time.monotonic())), interrupt, task_id)
            interval = min(5.0, interval * 1.5)

    def _check_asset_url_credential(self, url):
        # Check before parsers can discard controls, including redirect Locations.
        if not isinstance(url, str) or any(ord(c) < 32 or ord(c) == 127 for c in url):
            raise WylonError('Unsafe asset URL')
        # URL uses the same canonicalization as aiohttp's request builder. Inspect
        # decoded copies only: signed URLs must reach transport without rewriting.
        for candidate in (url, str(URL(url))):
            for depth in range(4):
                if self.api_key in candidate:
                    raise WylonError('Unsafe asset URL')
                if depth < 3:
                    candidate = unquote(candidate)

    def _validate_asset_url(self, url):
        self._check_asset_url_credential(url)
        # Only an explicitly configured loopback API may download from that same origin.
        local = _local_origin(self.base_url)
        parsed = urlsplit(url)
        if local and _local_origin(url) == local and parsed.username is None and parsed.password is None and not parsed.fragment:
            return
        validate_media_url(url, 'video')

    async def download(self, url, dest, max_bytes, interrupt=None):
        if type(max_bytes) is not int or max_bytes <= 0:
            raise WylonError('Download byte limit must be positive')
        target = Path(dest)
        temporary = None
        try:
            self._validate_asset_url(url)
            _check_interrupt(interrupt)
            target.parent.mkdir(parents=True, exist_ok=True)
            connector = aiohttp.TCPConnector(resolver=_PublicResolver())
            async with aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(total=max(120, self.timeout)), trust_env=False, auto_decompress=False, headers={'Accept-Encoding': 'identity'}) as session:
                for redirects in range(6):
                    self._validate_asset_url(url)
                    response = await _interruptible(session.get(url, allow_redirects=False), interrupt)
                    async with response:
                        if response.status in (301, 302, 303, 307, 308):
                            if redirects == 5 or not response.headers.get('Location'):
                                raise WylonError('Asset redirect limit reached')
                            location = response.headers['Location']
                            self._check_asset_url_credential(location)
                            url = urljoin(url, location)
                            continue
                        if response.status != 200:
                            raise WylonError(f'Asset download failed (HTTP {response.status})')
                        if response.headers.get('Content-Encoding', 'identity').lower() != 'identity':
                            raise WylonError('Compressed asset transport is unsupported; request identity encoding')
                        if response.content_length is not None and response.content_length > max_bytes:
                            raise WylonError('Asset exceeds download byte limit')
                        fd, temporary = tempfile.mkstemp(prefix='.' + target.name + '-', suffix='.part', dir=target.parent)
                        size = 0
                        with os.fdopen(fd, 'wb') as stream:
                            while True:
                                chunk = await _interruptible(response.content.read(65536), interrupt)
                                if not chunk:
                                    break
                                _check_interrupt(interrupt)
                                size += len(chunk)
                                if size > max_bytes:
                                    raise WylonError('Asset exceeds download byte limit')
                                stream.write(chunk)
                            stream.flush()
                            os.fsync(stream.fileno())
                        _check_interrupt(interrupt)
                        os.replace(temporary, target)
                        return target
                raise WylonError('Asset redirect limit reached')
        except (aiohttp.ClientError, asyncio.TimeoutError, OSError, ValueError) as exc:
            raise WylonError(f'Asset download failed: {exc}', api_key=self.api_key) from None
        finally:
            if temporary is not None:
                Path(temporary).unlink(missing_ok=True)
