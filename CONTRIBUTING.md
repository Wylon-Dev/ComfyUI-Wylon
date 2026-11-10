# Contributing

[简体中文](CONTRIBUTING.zh-CN.md) · [README](README.md)

Use [Issues](https://github.com/wylon-cloud/comfyui-wylon/issues) for bugs and feature requests, and [private vulnerability reporting](https://github.com/wylon-cloud/comfyui-wylon/security/advisories/new) for security issues. Include plugin/host versions, OS, reproducible steps, expected/actual behavior and redacted logs. Keep API keys, private settings, signed asset URLs and proprietary media out of reports.

## Build from public source

The public source includes runtime code, TypeScript source and build materials. The runtime ZIP includes the compiled frontend and user documentation. Run these commands from the source root with Node.js 22.23.x, npm and Python 3.10+:

```sh
npm ci --ignore-scripts
npm run typecheck
npm run build
npm run package
```

For packaging, `PYTHON` selects an interpreter; otherwise the script uses `python` on Windows and `python3` on macOS/Linux. You may also invoke `python scripts/package.py` with your selected interpreter. The script writes `ComfyUI-Wylon-0.3.1.zip` and `Wylon-ComfyTV-Workflows-0.3.1.zip` beside the source root, with SHA-256 sidecars. Use its `--help` for destination options. Checksums detect changed files.

For Windows 10/11 x64 manual/venv, official portable and macOS installations, use the [README installation instructions](README.md#-install). See [contributor checks](docs/VERIFICATION.md) when preparing changes. Ordinary plugin installation needs no Node.js, Bash or GCC.

## Changes and versions

Preserve stable node IDs, native IMAGE/VIDEO/AUDIO ports, upstream SDK fields/status values, bilingual operational text and server-only credentials. Generation POSTs must never be retried automatically. Keep changes scoped and describe behavior changes and installation requirements clearly. See [API conventions](docs/API_CONVENTIONS.md).

Follow Semantic Versioning 2.0.0. Release tags use `vX.Y.Z`; prereleases use `vX.Y.Z-alpha.n`, `vX.Y.Z-beta.n` or `vX.Y.Z-rc.n`; release branches use `vX.Y`. Backward-compatible additions increment minor, fixes increment patch, and incompatible public API changes require major. Deprecated external endpoints remain for at least six months and two minor releases before removal in a new major.

Runtime archives exclude development tooling and the optional ComfyTV pack. Keep user data, dependencies, credentials, symlinks and Windows reparse points out of all release archives. Check relative documentation links in extracted archives; optional-pack links in plugin documents point to the canonical repository. Original contributions use [MIT](LICENSE); retain [third-party notices](THIRD_PARTY_NOTICES.md).
