# ComfyUI-Wylon usage

[简体中文](USAGE.zh-CN.md) · [README](../README.md)

## Platform and interpreter selection

For Windows 10/11 x64 and macOS installation methods, see the [README platform table](../README.md#-install). Ordinary installs need no Node.js/npm, Bash or GCC.

| Installation | Interpreter for plugin dependencies | Command location |
| --- | --- | --- |
| Windows manual/venv | The Python that starts ComfyUI, for example `.\.venv\Scripts\python.exe` | ComfyUI root |
| Official Windows portable | `.\python_embeded\python.exe` | Portable distribution root, containing the inner `ComfyUI` folder |
| macOS / Linux source install | ComfyUI's active Python environment | ComfyUI root |

Follow the [installation commands](../README.md#-install) for your layout. Installing dependencies into an unrelated system Python does not make them available to ComfyUI.

## Credentials and host access

Open **Wylon → Wylon tasks** or a node's **Wylon configuration / API Key** button. Apply a key for the current server process, optionally selecting **Remember on this machine (private ComfyUI user configuration)**. Applying with saving also sets the session key. The connection check queries the model list; it does not generate media or prove account access to every generation model.

The effective source is session, then saved local, then `WYLON_API_KEY`. The session is the ComfyUI process lifetime, not a browser tab or individual login. Users who can operate that host can use its configured account and change configuration. Same-origin configuration checks do not provide user authentication or account isolation. Use a trusted host with appropriate network/access controls.

Saved credentials are plaintext at `<ComfyUI user directory>/wylon/private/credentials.json`; the normal path is `ComfyUI/user/wylon/private/credentials.json`. On POSIX the directory/file modes are 0700/0600. Windows users should check the server account's directory ACLs; POSIX mode calls alone do not establish equivalent Windows access isolation. Backups of this directory also contain the key. The plugin does not place keys in workflows, node inputs or generated metadata.

Use the panel to clear the session key and/or delete the saved local key. Deleting local storage alone can leave a session key active. Clearing both does not unset the environment key; remove that environment setting and restart the host to remove it. Restart clears session memory but retains saved local credentials.

Environment alternative, from the ComfyUI root with its Python interpreter, macOS/Linux:

```sh
export WYLON_API_KEY='your-key'
python main.py
```

Windows manual/venv, from the ComfyUI root in PowerShell (replace `.venv` if your environment has another name):

```powershell
$env:WYLON_API_KEY = 'your-key'
.\.venv\Scripts\python.exe main.py
```

Official Windows portable, from its distribution root in PowerShell:

```powershell
$env:WYLON_API_KEY = 'your-key'
.\run_nvidia_gpu.bat
```

Use your usual portable launch script; the example above is the NVIDIA launcher. The variable is inherited by processes started from that PowerShell session. To clear it from that session, run `Remove-Item Env:WYLON_API_KEY` and restart ComfyUI.

These are placeholders, not actual credentials. The examples above work in runtime installs; `.env` files are not loaded automatically. A source checkout also includes `.env.example` as a variable reference; it is omitted from the runtime archive. Default API root: `https://api.wylon.cn/v1`. `WYLON_BASE_URL` overrides it for a trusted test environment and receives the configured key; do not point it at an untrusted endpoint. HTTPS is required except loopback HTTP for local tests. Restart to apply environment changes.

## Models and media

- **Wylon Generate Image** (`WylonGenerateImage`): `Qwen/Qwen-Image-2512` or `Qwen/Qwen-Image-2.1`; `IMAGE`, `task_id`, `file_path` outputs. Async is recoverable. Sync has no task ID/recovery and ignores the node's seed control.
- **Wylon H3 Video** (`WylonH3Video`): defaults to `MiniMaxAI/MiniMax-H3`. **Wylon Ref2VA Video** (`WylonRef2VAVideo`): defaults to `MiniMaxAI/MiniMax-H3-Ref2VA`. Both offer the same selectable models and output `VIDEO`, `task_id`, `file_path`.
- **Wylon Resume Image Task** (`WylonResumeImageTask`) and **Wylon Resume Video Task** (`WylonResumeVideoTask`): query/download an existing matching task ID without creating a generation.

The selected model determines accepted roles. H3 accepts text and optional `first_frame`/`last_frame` native IMAGE inputs, one image each. Ref2VA rejects first/last-frame roles and requires at least one reference image or video. Connect `image_0` / `audio_0` to grow native IMAGE/AUDIO sockets. Put public HTTPS video URLs in `video_urls`, one per line. Audio references need an image or video. Incompatible combinations produce a bilingual validation error before submission; model choice is never automatic.

Video output is native VIDEO backed by the downloaded MP4 and retains its soundtrack without eagerly decoding all frames. Connect to native Save Video. For VideoHelperSuite, use native **Get Video Components** and route its IMAGE, AUDIO and fps outputs into VHS Video Combine. No audio track means no audio component.

Current constraints:

- Video generation: integer 5–15 seconds, 768p. Ratios: 21:9, 16:9, 4:3, 1:1, 3:4, 9:16. `server_default` omits ratio; `adaptive` also omits ratio but is accepted only for H3 with a first/last frame.
- Ref2VA: up to 9 images, 3 video clips, 3 audio clips. Native image batches count toward the image limit.
- Reference images: each dimension 300–5760 pixels, aspect ratio 0.4–2.5, Wylon documents 30 MB per image; the plugin also enforces a 30 MiB encoded-data cap. Native tensors are encoded as PNG; each first/last-frame input accepts exactly one image.
- Reference audio: 2–15 seconds per clip, Wylon documents 15 MB per clip; the plugin also enforces a 15 MiB encoded-WAV cap. Total duration is at most 15 seconds. Native AUDIO is encoded as PCM WAV.
- Output downloads: the plugin enforces a 64 MiB cap per image and a 1 GiB cap per video, separate from the reference-input limits. Retrying or resuming the same oversized result does not bypass these caps.
- Reference video: API constraint 2–15 seconds per clip, up to 50 MB each and 15 seconds total. Remote formats, frame rates, duration and file size are validated by Wylon; the plugin validates the URL, not every remote media attribute.

Reference video requires public HTTPS reachable by Wylon, without embedded credentials or fragments. No automatic upload is included. Local MP4 files, Base64 video, localhost, LAN/private addresses and expiring URLs that lapse before Wylon fetches them will fail. This also applies when an optional ComfyTV workflow supplies the URL.

Image size presets depend on the selected model; `server_default` omits size. Qwen-Image-2512 offers 1328×1328, 1664×928, 928×1664, 1104×1472 and 1584×1056. Qwen-Image-2.1 offers 1536×2752, 1696×2528, 1792×2400, 2048×2048, 2400×1792, 2528×1696 and 2752×1536. V1 produces one image per request. Seed `-1` omits seed; image seed is async-only. Negative prompts and accepted optional fields are forwarded; server acceptance does not establish their visual effect or determinism for every model.

`extra_parameters` must be a JSON object under 64 KiB. Only allowlisted API fields are accepted; authentication, model/routing and core request fields cannot be overridden. Image compatibility fields such as `n`, `stream`, `partial_images` and `output_format` are constrained to 1, false, 0 and png respectively. Unsupported API capabilities do not become available by adding a JSON field. Consult the current Wylon contract when using advanced parameters.

## Recovery and troubleshooting

Generation POSTs have no automatic retries. Read-only status queries use bounded retries/backoff, with local polling up to 15 minutes. An accepted async ID is journaled before polling under `<ComfyUI user directory>/wylon/`. Records contain ID, media kind, model, status and timestamp, excluding prompts, inputs, credentials and signed asset URLs.

After interrupted waiting, timeout or download failure, copy the ID from the panel or error into the matching Resume node. Recovery requires the correct account and a result that has not expired. It may download another local copy. Stopping ComfyUI/local waiting does not cancel cloud work. No cloud cancellation action is supplied. If no ID was received after a create timeout, check Wylon's console/history and usage before an explicit resubmission to avoid duplicate paid work.

- **Nodes/menu absent:** check the server startup import error, exact folder nesting, dependency interpreter and supported host baseline. Restart the server and refresh the page after installation/update.
- **Key missing/invalid:** check the panel's effective source; a session or saved local key overrides an environment key. Connection success only verifies the model-list request.
- **Cannot save/delete key:** verify the host service account can access the actual user directory; do not loosen permissions for other users as a workaround.
- **HTTP 429:** check account rate/concurrency limits and existing tasks. Let the relevant limit clear before deciding to submit again.
- **Model/reference validation:** explicitly select H3 for frame roles or Ref2VA for reference media. Verify counts, audio length and the public video URL; do not relabel local file paths as URLs.
- **Expired/failed task:** inspect the reported Wylon status. Download successful results promptly; querying cannot restore an expired asset. If you manually request new generation, it is a new potentially paid task.
- **Codec/download error:** verify disk space, network reachability and PyAV in the actual host environment. Preserve the task ID; for a transient failure, try the resume node with the correct account while the result remains available. If the error reports the output download limit (64 MiB per image / 1 GiB per video), retrying or resuming will not bypass it. Querying cannot restore an expired result; manually requesting another generation is a new potentially paid task.
- **Configuration blocked behind a proxy:** configuration mutations require a browser same-origin request. Ensure the proxy preserves a consistent browser/server origin; do not disable checks to work around it.

Results download to `<ComfyUI output directory>/wylon/`, normally `ComfyUI/output/wylon/`. The panel shows recent local results. Asset downloads do not receive the API key. Native Save Image/Save Video can create additional files in user-selected output locations.

## Update and uninstall

Before changing the installation, record the current plugin/host versions, stop ComfyUI (close its terminal/server process on Windows so loaded files can be replaced), and back up personal workflows/customizations and the existing plugin folder outside `custom_nodes/`. Back up host user/output data according to your local policy; user-directory backups include plaintext saved keys.

For an archive update, replace only `custom_nodes/ComfyUI-Wylon` with the newly extracted plugin folder, restore deliberate customizations after reviewing changes, then run the dependency installation command from the README with the host interpreter. Restart and check the Wylon panel before running a paid generation. Do not keep a second loadable old copy under `custom_nodes/`. For source checkouts, use your normal version-control process after preserving local edits.

Uninstall by stopping ComfyUI, removing only `custom_nodes/ComfyUI-Wylon`, and restarting. This leaves host user data, workflows and outputs intact. To remove credentials, clear session/local keys in the panel before uninstall, and remove the environment setting; alternatively, with the host stopped, deliberately delete only `wylon/private/credentials.json` from the actual user directory. Journals and downloaded media remain unless you choose to remove them after backing them up. Do not delete the entire ComfyUI user/output directories. Removing the plugin or journals does not cancel or delete remote Wylon tasks.

## API references

[Image generation guide](https://portal.wylon.cn/zh/docs-generation-images.html) · [Video generation guide](https://portal.wylon.cn/zh/docs-generation-videos.html)

The shipped capability file describes the implemented contract. Wylon can change model/account capabilities; consult its current documentation for service-side behavior.

[Owned HTTP API conventions and registered error codes](API_CONVENTIONS.md).
