# Changelog

[简体中文](CHANGELOG.zh-CN.md)

## 0.3.1

- Fixes task ID validation to accept legitimate long `task-`, `mask-` and `risk-` identifiers while continuing to block credential-bearing task IDs before recording or querying them.

## 0.3.0

- Separates fixed H3 text/first-last-frame generation from fixed Ref2VA reference-media generation; preserves existing node IDs and native IMAGE/VIDEO/AUDIO contracts.
- Adds the sixth node, **Wylon Reference Video URL**, with a dedicated `WYLON_REFERENCE_VIDEO` connection to Ref2VA. It validates up to three public HTTPS URLs without credentials, uploading, downloading or generation; empty input permits image-only references.
- Makes image generation synchronous through `images/generations`, with model/prompt/size/negative-prompt controls and an empty compatibility task ID. Removes image mode/seed controls and free-form extra JSON controls from all nodes. Video retains API seed forwarding and a local next-run seed policy.
- Renames existing-task retrieval nodes to **Get Image/Video Task Result**, allows standalone retrieval, and retains GET support for historical asynchronous image tasks without creating, restarting or canceling cloud work.
- Adds English/Simplified Chinese native node catalogs and locale-aware interface text. Migrates compatible legacy graphs, including typed URL-source connections and remapped reference links; rejects meaningful removed settings or conflicting media roles rather than silently discarding them.
- Ships seven ordinary examples and the updated five-pair ComfyTV pack, including dedicated URL-source preset bindings. Runtime/source packages include native catalogs and the workflow-migration module.

- Validates provider task IDs before journaling or status queries and sanitizes errors and limits their length while preserving legitimate IDs for result retrieval.

## 0.2.0

- Adds canonical versioned configuration/models/tasks/results APIs, registered structured errors, RFC 3339 timestamps, bounded keyset pagination and a compatible frontend. Legacy routes retain deprecation headers. Protects both owned credential directory levels against symlink/junction redirection.

- Windows 10/11 x64 and macOS installation guides, portable/manual layouts, compatible credential persistence, Unicode paths and LF checksums. Packaging rejects Windows reparse points.
- Initial source distribution of five native ComfyUI nodes for Wylon image/video generation and task recovery, with a server-side credential panel and media previews.
- Supports Qwen Image 2512/2.1 and MiniMax H3/Ref2VA, native IMAGE/VIDEO/AUDIO interfaces, model-role validation and bounded media handling.
- Includes five example workflows and a separately packaged optional ComfyTV workflow pack. Toonflow-Wylon is maintained independently.
- Original Wylon material is MIT licensed; applicable third-party notices are retained.
