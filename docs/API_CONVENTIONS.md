# API conventions

[简体中文](API_CONVENTIONS.zh-CN.md) · [Usage](USAGE.md)

ComfyUI-Wylon 0.2.0 follows the supplied service conventions for its own HTTP API. Names and JSON fields use snake_case and US English; collections are plural. No database, Kafka, object store or gRPC service is introduced.

## Owned routes

- `GET /v1/wylon/configuration`: credential status only; never returns a key.
- `PATCH /v1/wylon/configuration`: apply `api_key` with optional boolean `persist` (default false). This changes the key without replacing unrelated host configuration. The key is required; persistence applies only to the supplied key.
- `DELETE /v1/wylon/configuration`: clear `scope` (`session`, `local` or `all`). The environment remains controlled by the host process.
- `GET /v1/wylon/models`: configured/source metadata and paginated `models`; optional `type` filter; `order_by=id asc|desc`.
- `GET /v1/wylon/tasks`: paginated `tasks`; optional `kind`, `status`, `updated_after`; `order_by=updated_at asc|desc`.
- `GET /v1/wylon/results`: paginated local `results`; optional `kind`, `created_after`; `order_by=created_at asc|desc`.

Lists accept `page_size` (default 20, 1–100) and `page_token`. Responses have the plural collection and `next_page_token`, empty on the last page. Opaque keyset tokens are scoped to collection, filters and order; they are not offsets, credentials or snapshots. Task/result ties use ID/filename. Concurrent changes to an ordering field can affect subsequent pages. Timestamps and timestamp filters use RFC 3339 with a timezone; responses normalize to UTC `Z`. The UI displays viewer-local time and bounded first pages: 100 models, 12 tasks, 24 results. Unknown or duplicate list parameters are rejected.

Configuration mutations require same-origin browser headers and JSON bodies capped at 16 KiB. A key is supplied only in the JSON configuration body; upstream authentication uses `Authorization: Bearer ...`. Authentication tokens never belong in query parameters. This panel shares the host process account; host access controls provide authentication and isolation.

## Registered errors

Canonical handlers return `{ "error": { "message": "...", "type": "...", "param": null, "code": "..." } }`. Error messages never include credentials or raw provider exceptions. The authoritative code registry is `wylon/api.py`:

- HTTP 400, `invalid_request_error`: `invalid_value`, `missing_required_parameter`, `unknown_parameter`, `invalid_json`, `invalid_page_token`, `unsupported_content_type`, `request_body_too_large`, `invalid_request`, `provider_invalid_request`.
- HTTP 401, `authentication_error`: `invalid_api_key`.
- HTTP 403, `permission_error`: `origin_not_allowed`, `provider_permission_denied`.
- HTTP 404, `not_found_error`: `provider_resource_not_found`.
- HTTP 409, `conflict_error`: `provider_conflict`.
- HTTP 422, `unprocessable_entity_error`: `provider_unprocessable_entity`.
- HTTP 429, `rate_limit_error`: `provider_rate_limit_exceeded`.
- HTTP 500, `api_error`: `credential_storage_error`, `credential_removal_error`, `internal_error`, `provider_error`.
- HTTP 503, `service_unavailable_error`: `provider_connection_failed`.

Model-list failures are classified only from explicit HTTP transport metadata, using fixed messages without provider response details. Upstream 400/401/403/404/409/422/429/500/503 retain their standard status/type. Network failures, HTTP 408, redirects, 502/504 and other upstream 5xx map to 503; other upstream 4xx map to 400. Invalid successful provider responses map to 503. Human-readable exception text never determines the status. Legacy `/wylon/models` retains HTTP 502 and its original string-error shape.

New business codes require registry/documentation review. Clients classify by HTTP status, then type/code. A retryable error classification does not authorize replaying generation POSTs: those never retry automatically. Read-only polling uses bounded backoff.

## Compatibility exceptions and evolution

ComfyUI-owned routes (`/view`, websocket transport), stable Wylon node IDs, IMAGE/VIDEO/AUDIO ports, workflow fields, and upstream Wylon/SDK field names, model IDs and status spellings retain their contracts. Upstream statuses such as `cancelled` and `downloaded` are not renamed to new owned enum values. No new owned public enum is introduced. Wylon async generation/resume follows the provider task protocol; this plugin does not invent an operation service.

The six existing `/wylon/*` method/path combinations keep their original shapes, including legacy POST configuration and status codes. All carry `Deprecation: true`, `Sunset: Mon, 10 May 2027 00:00:00 GMT`, and a successor Link. Sunset is the earliest date, not automatic removal: aliases stay for at least six months after the 0.2.0 announcement and two minor releases, and can be removed only in a new major. A delayed release must move that earliest date forward.

Follow SemVer 2.0.0: `vX.Y.Z`, prereleases `vX.Y.Z-alpha.n`, `-beta.n` or `-rc.n`, release branches `vX.Y`. Compatible additions use minor; fixes use patch. Removing/renaming public endpoints or fields, changing types/meaning, narrowing validation or changing defaults requires a major version and the deprecation process. Repository: [wylon-cloud/comfyui-wylon](https://github.com/wylon-cloud/comfyui-wylon).
