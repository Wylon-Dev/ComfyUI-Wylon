# Security and sensitive reports

[简体中文](SECURITY.zh-CN.md) · [README](README.md)

Report vulnerabilities through [GitHub private vulnerability reporting](https://github.com/wylon-cloud/comfyui-wylon/security/advisories/new). Include affected plugin/host versions, impact, a minimal reproduction and redacted logs. Use [repository Issues](https://github.com/wylon-cloud/comfyui-wylon/issues) for ordinary bugs and feature requests; keep credentials and exploit-sensitive details out of public reports.

Do not attach API keys, complete signed URLs, proprietary media or private host settings. If a key was exposed, revoke/rotate it with Wylon, remove saved/session/environment copies, and review account usage. Removing a Git commit or file does not revoke a key.

The key is server-side, shared by the ComfyUI server process's users. Opt-in local saving stores plaintext in the host user directory with POSIX directory/file modes 0700/0600; Windows requires suitable ACLs. Session mode avoids persistent storage but is not user-account isolation. Same-origin checks on credential changes are not host authentication. Operate only on trusted hosts with appropriate access controls; backups containing saved keys require the same protection.

`WYLON_BASE_URL` receives the configured credential. Only use a trusted API endpoint. Generation sends prompts and supplied references to Wylon; account/provider terms and retention are outside this plugin. Result asset requests omit the API Authorization header. Before connecting, the client rejects provider-result and redirect URLs containing the active API key in the raw URL, canonical request URL or bounded repeated percent-decoded forms. Journals omit prompts, input media and signed URLs, but retain task IDs/model/status metadata; workflows and host outputs may still contain private user content.

Before sharing a workflow, log, screenshot or archive, inspect it for private content. Packaging allowlists and secret-pattern checks cannot prove arbitrary files contain no sensitive data. See [usage](docs/USAGE.md) for key removal, data locations and preserving/removing files deliberately during uninstall.
