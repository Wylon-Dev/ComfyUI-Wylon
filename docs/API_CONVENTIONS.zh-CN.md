# API 规范

[English](API_CONVENTIONS.md) · [使用指南](USAGE.zh-CN.md)

ComfyUI-Wylon 0.3.0 的自有 HTTP API 遵循提供的服务规范：路径与 JSON 字段使用 snake_case、美式英语，集合使用复数。本插件不新增数据库、Kafka、对象存储或 gRPC 服务。

## 自有接口

- `GET /v1/wylon/configuration`：只返回凭据状态，不返回密钥。
- `PATCH /v1/wylon/configuration`：传入 `api_key`，可选布尔 `persist`（默认 false）；仅修改密钥，不替换宿主其他配置。密钥必填，保存设置只作用于这次提供的密钥。
- `DELETE /v1/wylon/configuration`：传入 `scope`（`session`、`local` 或 `all`）；环境变量仍由宿主进程管理。
- `GET /v1/wylon/models`：配置状态/source 与分页 `models`；可按 `type` 过滤，`order_by=id asc|desc`。
- `GET /v1/wylon/tasks`：分页 `tasks`；可按 `kind`、`status`、`updated_after` 过滤，`order_by=updated_at asc|desc`。
- `GET /v1/wylon/results`：分页本地 `results`；可按 `kind`、`created_after` 过滤，`order_by=created_at asc|desc`。

列表接受 `page_size`（默认 20，范围 1–100）及 `page_token`；响应包含复数集合字段及 `next_page_token`，末页为空。opaque keyset token 绑定集合、过滤与排序，不使用 offset，不包含凭据，也不提供快照隔离。相同时间按任务 ID/文件名排序；并发修改排序字段可能影响后续页。时间戳及时间过滤必须为带时区的 RFC 3339，响应统一为 UTC `Z`；界面按用户本地时区显示，只取有界第一页：100 个模型、12 个任务、24 个结果。未知或重复列表参数被拒绝。

配置修改要求浏览器同源请求、JSON body，最大 16 KiB。配置密钥只通过 JSON body 提交；上游认证使用 `Authorization: Bearer ...`，认证 token 不得放进 query。面板共享宿主进程账户，认证和隔离由宿主访问控制提供。

## 注册错误码

canonical handler 返回 `{ "error": { "message": "...", "type": "...", "param": null, "code": "..." } }`。不返回凭据或原始供应商异常。统一注册清单位于 `wylon/api.py`：

- HTTP 400、`invalid_request_error`：`invalid_value`、`missing_required_parameter`、`unknown_parameter`、`invalid_json`、`invalid_page_token`、`unsupported_content_type`、`request_body_too_large`、`invalid_request`、`provider_invalid_request`。
- HTTP 401、`authentication_error`：`invalid_api_key`。
- HTTP 403、`permission_error`：`origin_not_allowed`、`provider_permission_denied`。
- HTTP 404、`not_found_error`：`provider_resource_not_found`。
- HTTP 409、`conflict_error`：`provider_conflict`。
- HTTP 422、`unprocessable_entity_error`：`provider_unprocessable_entity`。
- HTTP 429、`rate_limit_error`：`provider_rate_limit_exceeded`。
- HTTP 500、`api_error`：`credential_storage_error`、`credential_removal_error`、`internal_error`、`provider_error`。
- HTTP 503、`service_unavailable_error`：`provider_connection_failed`。

模型列表失败仅按明确的 HTTP 传输元数据分类，使用固定脱敏消息，不返回供应商响应细节。上游 400/401/403/404/409/422/429/500/503 保留规范 status/type；网络失败、HTTP 408、重定向、502/504 及其他上游 5xx 映射为 503，其他上游 4xx 映射为 400；格式错误的上游成功响应映射为 503。不得从人类可读异常文本推断状态。旧 `/wylon/models` 保留 HTTP 502 与字符串 error 原响应格式。

新业务码须注册并审阅文档。客户端先按 HTTP status，再按 type/code 分类；错误属于可重试类型不代表可以自动重放生成 POST，生成请求始终不自动重试。只读轮询采用有界退避。

## 兼容例外及演进

ComfyUI 自有接口（`/view`、websocket 传输）、稳定 Wylon 节点 ID、IMAGE/VIDEO/AUDIO 端口、工作流字段、上游 Wylon/SDK 字段、模型 ID 及状态拼写保留原契约。`cancelled`、`downloaded` 等上游状态不强制改为新的自有枚举值；本次没有引入自有公开枚举。视频异步生成及已有任务获取沿用供应商 task 协议，不创建额外 operation 服务。

现有六个 `/wylon/*` method/path 组合保留原响应，包括配置 POST 及旧状态码；均返回 `Deprecation: true`、`Sunset: Mon, 10 May 2027 00:00:00 GMT` 与 successor Link。Sunset 只是最早日期，不会自动移除：从 0.2.0 公告起至少保留六个月及两个 minor 版本，且仅能在新 major 中移除；如果实际发布日期延后，应顺延最早日期。

遵循 SemVer 2.0.0：正式 tag `vX.Y.Z`；预发布 `vX.Y.Z-alpha.n`、`-beta.n` 或 `-rc.n`；发布分支 `vX.Y`。兼容新增递增 minor，修复递增 patch；删除/重命名公开 endpoint 或 field、修改类型/语义、收紧校验及修改默认值须递增 major 并走废弃流程。仓库：[wylon-cloud/comfyui-wylon](https://github.com/wylon-cloud/comfyui-wylon)。
