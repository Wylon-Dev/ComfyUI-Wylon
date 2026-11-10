"""Host endpoints. Configuration responses never include credential material."""
from __future__ import annotations

import json
from aiohttp import web
from .credentials import get_store


CONFIG_BODY_LIMIT = 16 * 1024
SETUP_INSTRUCTIONS = (
    'Enter an API key for this ComfyUI session; enable local saving only on a trusted server. '
    'Session overrides local storage, then WYLON_API_KEY. Clearing saved/session keys does not change the environment. '
    '/ 输入密钥仅供本次ComfyUI会话使用；仅在可信服务器上启用本地保存。优先级：会话、本地、环境变量。'
)


def _config_status():
    return {**get_store().status(), 'setup_instructions': SETUP_INSTRUCTIONS}


def _json_response(data, *, status=200):
    return web.json_response(data, status=status, headers={'Cache-Control': 'no-store'})


async def configuration(request):
    return _json_response(_config_status())


async def _config_body(request):
    # Require a browser-verifiable origin, even if ComfyUI has permissive CORS.
    if request.headers.get('Origin') != f'{request.scheme}://{request.host}' or request.headers.get('Sec-Fetch-Site', 'same-origin') not in ('same-origin', 'none'):
        raise web.HTTPForbidden(text='Configuration changes require a same-origin request')
    if request.content_type != 'application/json':
        raise web.HTTPUnsupportedMediaType(text='Use application/json')
    if request.content_length is not None and request.content_length > CONFIG_BODY_LIMIT:
        raise web.HTTPRequestEntityTooLarge(max_size=CONFIG_BODY_LIMIT, actual_size=request.content_length)
    body = bytearray()
    async for chunk in request.content.iter_chunked(4096):
        body.extend(chunk)
        if len(body) > CONFIG_BODY_LIMIT:
            raise web.HTTPRequestEntityTooLarge(max_size=CONFIG_BODY_LIMIT, actual_size=len(body))
    try:
        result = json.loads(body)
    except (ValueError, UnicodeError):
        raise web.HTTPBadRequest(text='Invalid JSON configuration') from None
    if not isinstance(result, dict):
        raise web.HTTPBadRequest(text='Configuration must be a JSON object')
    return result


async def configure(request):
    body = await _config_body(request)
    try:
        get_store().configure(body.get('api_key'), persist=body.get('persist', False))
    except ValueError as exc:
        return _json_response({'error': str(exc)}, status=400)
    except OSError:
        return _json_response({'error': 'Could not save credentials; check private user-directory permissions / 无法保存密钥，请检查用户目录权限'}, status=500)
    return _json_response(_config_status())


async def clear_configuration(request):
    body = await _config_body(request)
    try:
        get_store().clear(body.get('scope'))
    except ValueError as exc:
        return _json_response({'error': str(exc)}, status=400)
    except OSError:
        return _json_response({'error': 'Could not remove locally saved credentials / 无法删除本地密钥'}, status=500)
    return _json_response(_config_status())


async def _load_models():
    """Shared metadata loader preserves typed transport failures for canonical clients."""
    state = get_store().status()
    if not state['configured']:
        return {'configured': False, 'source': state['source'], 'models': []}
    from .runtime import client
    async with client() as api:
        result = await api.models()
    models = []
    for row in result.get('data', []):
        if not isinstance(row, dict) or not isinstance(row.get('id'), str):
            continue
        kind = row.get('type')
        if kind in ('image', 'video', 'text_to_video'):
            models.append({'id': row['id'], 'type': kind})
    return {'configured': True, 'source': state['source'], 'models': models}


async def connection(request):
    from .client import WylonError
    try:
        return _json_response(await _load_models())
    except (WylonError, ValueError):
        state = get_store().status()
        return _json_response({'configured': True, 'source': state['source'], 'models': [], 'error': 'Connection failed; check server key and Wylon availability / 连接失败，请检查服务端密钥及Wylon服务'}, status=502)


def task_records():
    from .runtime import journal
    return journal().iter_records()


def task_history():
    from .runtime import journal
    return journal().list()


async def recent_tasks(request):
    keys = ('id', 'kind', 'model', 'status', 'updated_at')
    tasks = [{key: row.get(key, '') for key in keys} for row in task_history()[:100]]
    return web.json_response({'tasks': tasks})


def register_routes():
    from server import PromptServer
    from .results import recent_results
    server = PromptServer.instance
    if getattr(server, '_wylon_routes_registered', False):
        return
    for method, path, handler in (
        ('get', '/v1/wylon/models', models_v1),
        ('get', '/v1/wylon/tasks', tasks_v1),
        ('get', '/v1/wylon/results', results_v1),
        ('get', '/v1/wylon/configuration', configuration),
        ('patch', '/v1/wylon/configuration', configure_v1),
        ('delete', '/v1/wylon/configuration', clear_configuration_v1),
    ):
        getattr(server.routes, method)(path)(_canonical(handler))
    for method, path, handler, successor in (
        ('get', '/wylon/models', connection, '/v1/wylon/models'),
        ('get', '/wylon/tasks', recent_tasks, '/v1/wylon/tasks'),
        ('get', '/wylon/results', recent_results, '/v1/wylon/results'),
        ('get', '/wylon/config', configuration, '/v1/wylon/configuration'),
        ('post', '/wylon/config', configure, '/v1/wylon/configuration'),
        ('delete', '/wylon/config', clear_configuration, '/v1/wylon/configuration'),
    ):
        getattr(server.routes, method)(path)(_legacy(handler, successor))
    server._wylon_routes_registered = True


# Canonical owned API. Legacy routes above retain their original response shapes.
from .api import APIError, error_response, provider_error, paginate, query_parameters, rfc3339, time_key


def _canonical(handler):
    async def serve(request):
        try:
            return await handler(request)
        except APIError as error:
            return error_response(error)
        except web.HTTPException as error:
            code = {403: 'origin_not_allowed', 413: 'request_body_too_large',
                    415: 'unsupported_content_type'}.get(error.status, 'invalid_request')
            return error_response(APIError(error.reason, code))
        except Exception:
            # Never serialize provider exceptions or credential-bearing filesystem errors.
            return error_response(APIError('The server could not process the request', 'internal_error'))
    return serve


def _legacy(handler, successor):
    async def serve(request):
        try:
            response = await handler(request)
        except web.HTTPException as error:
            response = error
        response.headers.update({'Deprecation': 'true', 'Sunset': 'Mon, 10 May 2027 00:00:00 GMT',
                                 'Link': f'<{successor}>; rel="successor-version"'})
        return response
    return serve


def _unknown_fields(body, allowed):
    unknown = set(body) - allowed
    if unknown:
        field = sorted(unknown)[0]
        # The property name is only diagnostic if it is a normal field identifier.
        import re
        parameter = field if re.fullmatch(r'[a-z][a-z0-9_]{0,63}', field) else None
        raise APIError('Unknown configuration parameter', 'unknown_parameter', parameter)


async def configure_v1(request):
    try:
        body = await _config_body(request)
    except web.HTTPBadRequest:
        raise APIError('Configuration must be a JSON object', 'invalid_json') from None
    _unknown_fields(body, {'api_key', 'persist'})
    if 'api_key' not in body:
        raise APIError('api_key is required', 'missing_required_parameter', 'api_key')
    if 'persist' in body and type(body['persist']) is not bool:
        raise APIError('persist must be a boolean', 'invalid_value', 'persist')
    try:
        get_store().configure(body['api_key'], persist=body.get('persist', False))
    except ValueError:
        raise APIError('api_key must contain 8–4096 printable ASCII characters without whitespace', 'invalid_value', 'api_key') from None
    except OSError:
        raise APIError('Could not save credentials; check private user-directory permissions', 'credential_storage_error') from None
    return _json_response(_config_status())


async def clear_configuration_v1(request):
    try:
        body = await _config_body(request)
    except web.HTTPBadRequest:
        raise APIError('Configuration must be a JSON object', 'invalid_json') from None
    _unknown_fields(body, {'scope'})
    if 'scope' not in body:
        raise APIError('scope is required', 'missing_required_parameter', 'scope')
    try:
        get_store().clear(body['scope'])
    except ValueError:
        raise APIError('scope must be session, local, or all', 'invalid_value', 'scope') from None
    except OSError:
        raise APIError('Could not remove locally saved credentials', 'credential_removal_error') from None
    return _json_response(_config_status())


async def models_v1(request):
    query = query_parameters(request, {'page_size', 'page_token', 'order_by', 'type'})
    selected_type = query.get('type', '')
    if selected_type and selected_type not in ('image', 'video', 'text_to_video'):
        raise APIError('Unsupported model type', 'invalid_value', 'type')
    # Validate pagination before a remote model-list call, even for an empty account.
    arguments = dict(resource='models', query=query, key=lambda row: (row['id'],),
                     key_types=(str,), default_order='id asc', filters={'type': selected_type})
    paginate([], **arguments)
    from .client import WylonError
    try:
        result = await _load_models()
    except WylonError as error:
        raise provider_error(error.http_status) from None
    except ValueError:
        raise provider_error(None) from None
    rows = (row for row in result['models'] if not selected_type or row['type'] == selected_type)
    page = paginate(rows, **arguments)
    return _json_response({'configured': result['configured'], 'source': result['source'], **page})


async def tasks_v1(request):
    from .journal import STATUSES
    query = query_parameters(request, {'page_size', 'page_token', 'order_by', 'status', 'kind', 'updated_after'})
    selected_status, selected_kind = query.get('status', ''), query.get('kind', '')
    if selected_status and selected_status not in STATUSES:
        raise APIError('Unsupported task status', 'invalid_value', 'status')
    if selected_kind and selected_kind not in ('image', 'video'):
        raise APIError('Unsupported task kind', 'invalid_value', 'kind')
    after = _after(query, 'updated_after')
    def rows():
        for record in task_records():
            if selected_status and record.get('status') != selected_status or selected_kind and record.get('kind') != selected_kind:
                continue
            try:
                updated_at = rfc3339(record['updated_at'])
                if after is not None and time_key(updated_at) <= after:
                    continue
                yield {**{key: record.get(key, '') for key in ('id', 'kind', 'model', 'status')}, 'updated_at': updated_at}
            except (ValueError, TypeError, KeyError, OverflowError):
                continue
    page = paginate(rows(), resource='tasks', query=query,
                    key=lambda row: (time_key(row['updated_at']), row['id']), key_types=(int, str),
                    default_order='updated_at desc', filters={key: query.get(key, '') for key in ('status', 'kind', 'updated_after')})
    return _json_response(page)


def _after(query, name):
    if name not in query:
        return None
    try:
        return time_key(query[name])
    except (ValueError, TypeError, OverflowError):
        raise APIError(f'{name} must be an RFC 3339 timestamp with a timezone', 'invalid_value', name) from None


async def results_v1(request):
    from .results import result_entries
    query = query_parameters(request, {'page_size', 'page_token', 'order_by', 'kind', 'created_after'})
    kind = query.get('kind', '')
    if kind and kind not in ('image', 'video'):
        raise APIError('Unsupported result kind', 'invalid_value', 'kind')
    after = _after(query, 'created_after')
    def rows():
        for row in result_entries():
            if kind and row['kind'] != kind:
                continue
            row = {**row, 'created_at': rfc3339(row['created_at'])}
            if after is None or time_key(row['created_at']) > after:
                yield row
    page = paginate(rows(), resource='results', query=query,
                    key=lambda row: (time_key(row['created_at']), row['filename']), key_types=(int, str),
                    default_order='created_at desc', filters={key: query.get(key, '') for key in ('kind', 'created_after')})
    return _json_response(page)
