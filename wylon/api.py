"""Owned HTTP contracts: registered errors and bounded keyset pagination."""
from __future__ import annotations

import base64
import hashlib
import heapq
import json
import re
from datetime import datetime, timezone
from collections.abc import Callable, Iterable
from aiohttp import web

# Public error codes are registered here; do not return provider messages or keys.
ERROR_CODES = {
    'invalid_value': ('invalid_request_error', 400),
    'missing_required_parameter': ('invalid_request_error', 400),
    'unknown_parameter': ('invalid_request_error', 400),
    'invalid_json': ('invalid_request_error', 400),
    'invalid_page_token': ('invalid_request_error', 400),
    'origin_not_allowed': ('permission_error', 403),
    'unsupported_content_type': ('invalid_request_error', 400),
    'request_body_too_large': ('invalid_request_error', 400),
    'credential_storage_error': ('api_error', 500),
    'credential_removal_error': ('api_error', 500),
    'provider_connection_failed': ('service_unavailable_error', 503),
    'invalid_request': ('invalid_request_error', 400),
    'internal_error': ('api_error', 500),
    'provider_invalid_request': ('invalid_request_error', 400),
    'invalid_api_key': ('authentication_error', 401),
    'provider_permission_denied': ('permission_error', 403),
    'provider_resource_not_found': ('not_found_error', 404),
    'provider_conflict': ('conflict_error', 409),
    'provider_unprocessable_entity': ('unprocessable_entity_error', 422),
    'provider_rate_limit_exceeded': ('rate_limit_error', 429),
    'provider_error': ('api_error', 500),
}


class APIError(Exception):
    def __init__(self, message: str, code: str, param: str | None = None):
        super().__init__(message)
        self.error_type, self.status = ERROR_CODES[code]
        self.code = code
        self.param = param


def provider_error(http_status: int | None) -> APIError:
    """Classify explicit transport metadata; never infer status from provider text."""
    errors = {
        400: ('The provider rejected the model-list request', 'provider_invalid_request'),
        401: ('The provider rejected the configured API key', 'invalid_api_key'),
        403: ('The configured account cannot access the provider model list', 'provider_permission_denied'),
        404: ('The requested provider resource was not found', 'provider_resource_not_found'),
        409: ('The provider reported a resource conflict', 'provider_conflict'),
        422: ('The provider could not process the model-list request', 'provider_unprocessable_entity'),
        429: ('The provider rate limit was exceeded', 'provider_rate_limit_exceeded'),
        500: ('The provider could not process the request', 'provider_error'),
    }
    if http_status in errors:
        message, code = errors[http_status]
    elif http_status is not None and 400 <= http_status < 500 and http_status != 408:
        message, code = errors[400]
    else:
        message, code = 'Connection failed; check server credentials and Wylon availability', 'provider_connection_failed'
    return APIError(message, code)


def json_response(data, *, status=200):
    return web.json_response(data, status=status, headers={'Cache-Control': 'no-store'})


def error_response(error: APIError):
    return json_response({'error': {'message': str(error), 'type': error.error_type,
                                   'param': error.param, 'code': error.code}}, status=error.status)


def timestamp(value: str) -> datetime:
    if not isinstance(value, str) or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}[Tt][0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?(?:[Zz]|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])', value):
        raise ValueError('Timestamp must use RFC 3339')
    value = value.upper()
    date = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if date.tzinfo is None:
        raise ValueError('Timestamp requires a timezone')
    return date.astimezone(timezone.utc)


def rfc3339(value: str) -> str:
    return timestamp(value).isoformat().replace('+00:00', 'Z')


def time_key(value: str) -> int:
    date = timestamp(value)
    delta = date - datetime(1970, 1, 1, tzinfo=timezone.utc)
    return (delta.days * 86400 + delta.seconds) * 1000000 + delta.microseconds


def query_parameters(request, allowed: set[str]) -> dict[str, str]:
    query = request.query
    for name in query:
        if name not in allowed:
            # Only echo identifier-shaped parameter names, never arbitrary text.
            parameter = name if re.fullmatch(r'[a-z][a-z0-9_]{0,63}', name) else None
            raise APIError('Unknown query parameter', 'unknown_parameter', parameter)
        if len(query.getall(name)) != 1:
            raise APIError('A query parameter may appear only once', 'invalid_value', name)
    return dict(query)


def paginate(rows: Iterable[dict], *, resource: str, query: dict[str, str],
             key: Callable, key_types: tuple[type, ...], default_order: str,
             filters: dict[str, str] | None = None) -> dict:
    size_text = query.get('page_size', '20')
    if not re.fullmatch(r'[0-9]{1,3}', size_text) or not 1 <= int(size_text) <= 100:
        raise APIError('page_size must be an integer from 1 to 100', 'invalid_value', 'page_size')
    size = int(size_text)
    sort_field, default_direction = default_order.split(' ')
    order = query.get('order_by', default_order)
    if order not in (f'{sort_field} asc', f'{sort_field} desc'):
        raise APIError('Unsupported order_by value', 'invalid_value', 'order_by')
    descending = order.endswith(' desc')
    scope = hashlib.sha256(json.dumps([resource, order, filters or {}], sort_keys=True).encode()).hexdigest()
    cursor = None
    token = query.get('page_token', '')
    if token:
        try:
            if len(token) > 2048 or not re.fullmatch(r'[A-Za-z0-9_-]+', token):
                raise ValueError()
            value = json.loads(base64.urlsafe_b64decode(token + '=' * (-len(token) % 4)))
            if not isinstance(value, dict) or set(value) != {'scope', 'key'} or value['scope'] != scope:
                raise ValueError()
            bookmark = value['key']
            if not isinstance(bookmark, list) or len(bookmark) != len(key_types):
                raise ValueError()
            for part, expected in zip(bookmark, key_types):
                if type(part) is not expected or (isinstance(part, str) and len(part) > 300) or (type(part) is int and abs(part) > 2**63 - 1):
                    raise ValueError()
            cursor = tuple(bookmark)
        except (ValueError, TypeError, KeyError, OverflowError):
            raise APIError('Invalid page_token for this collection and query', 'invalid_page_token', 'page_token') from None
    def candidates():
        for row in rows:
            current = key(row)
            if cursor is None or (current < cursor if descending else current > cursor):
                yield row
    # Keep only one page and a sentinel in memory, not an offset or an entire gallery.
    select = heapq.nlargest if descending else heapq.nsmallest
    selected = select(size + 1, candidates(), key=key)
    page = selected[:size]
    next_token = ''
    if len(selected) > size:
        value = {'scope': scope, 'key': list(key(page[-1]))}
        next_token = base64.urlsafe_b64encode(json.dumps(value, separators=(',', ':')).encode()).decode().rstrip('=')
    return {resource: page, 'next_page_token': next_token}
