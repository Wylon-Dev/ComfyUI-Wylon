<div align="center">

<h1>Wylon ComfyTV Workflows</h1>
<p><strong>Ready-to-import Wylon image and video workflows for ComfyTV.</strong></p>

[![Version](https://img.shields.io/badge/version-0.2.0-blue)](manifest.json)
[![MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![ComfyTV](https://img.shields.io/badge/ComfyTV-1.13.1-222222)](https://github.com/jtydhr88/ComfyTV/tree/v1.13.1)

**English** · [简体中文](README.zh-CN.md)

</div>

Use Qwen image generation and MiniMax H3 video generation in ComfyTV stages. This optional pack supplies **five ComfyUI graphs and five matching ComfyTV presets**, with stage prompt/seed bindings, native saved-media results and optional reference-branch pruning.

## 🧩 What to install

| Component | Role | Installation |
| --- | --- | --- |
| [**ComfyUI-Wylon**](https://github.com/wylon-cloud/comfyui-wylon#-install) | Python generation/resume nodes, API key setup and task panel | Install the plugin in `ComfyUI/custom_nodes/ComfyUI-Wylon/` |
| **This workflow pack** | ComfyTV graphs and their `_preset.json` bindings | Copy the paired JSON files into ComfyTV's user workflow folders |

**ComfyTV and ComfyUI-Wylon must run on the same ComfyUI server.** This pack reuses that server's nodes and credentials. It needs no additional node copies, npm installation or local model weights.

Host versions: **ComfyUI v0.44.0 + ComfyTV v1.13.1 + ComfyUI-Wylon v0.2.0**. The [manifest](manifest.json) records the file pairs, node IDs and compatibility details.

| Platform | ComfyUI installation method |
| --- | --- |
| Windows 10/11 x64 | Manual/venv or official Windows portable |
| macOS | ComfyUI source installation |

The Windows copy instructions below use File Explorer or PowerShell and require no Bash/GCC.

Use the same server and workflow paths for either Windows layout. For portable, `<ComfyUI>` means its **inner `ComfyUI` folder**, not the outer distribution root.

## 📦 Install from source or ZIP

1. Install [ComfyUI-Wylon](https://github.com/wylon-cloud/comfyui-wylon#-install) and [ComfyTV](https://github.com/jtydhr88/ComfyTV/tree/v1.13.1) on the same server, following their own instructions.
2. Get this directory from the [repository source](https://github.com/wylon-cloud/comfyui-wylon/tree/main/comfytv-workflows), or download and extract the [repository source ZIP](https://github.com/wylon-cloud/comfyui-wylon/archive/refs/heads/main.zip). In a source checkout/extraction, the pack is under `comfytv-workflows/`.
3. Back up any same-named destination files. Copy the **contents** of these two source folders, creating destination folders if needed:

   | Pack source | Destination on the ComfyUI server |
   | --- | --- |
   | `workflows/image/` | `<ComfyUI>/user/comfytv/workflows/image/` |
   | `workflows/video/` | `<ComfyUI>/user/comfytv/workflows/video/` |

4. Keep each graph `.json` beside its matching `_preset.json`. Restart ComfyUI or rescan workflows in ComfyTV.

On Windows you can use File Explorer: open the pack's `workflows` folder and copy the JSON files into the matching destination folders above. Or run this in PowerShell from the **pack root** (`comfytv-workflows` in source, or the extracted standalone pack):

```powershell
$ComfyUIRoot = 'C:\AI\ComfyUI'
New-Item -ItemType Directory -Force -Path "$ComfyUIRoot\user\comfytv\workflows\image", "$ComfyUIRoot\user\comfytv\workflows\video" | Out-Null
Copy-Item .\workflows\image\*.json "$ComfyUIRoot\user\comfytv\workflows\image\"
Copy-Item .\workflows\video\*.json "$ComfyUIRoot\user\comfytv\workflows\video\"
```

Replace `$ComfyUIRoot` with the real host path; for example `C:\AI\ComfyUI_windows_portable\ComfyUI` for portable.

For a local build, run `npm run package` from the **repository root** using the developer toolchain (Node.js 22.23.x + npm and Python), or invoke `python scripts/package.py` with your selected Python. It produces the separate `Wylon-ComfyTV-Workflows-0.2.0.zip`; after extraction, the pack root is `Wylon-ComfyTV-Workflows`. Apply the same folder-copy steps above. Build details are in [CONTRIBUTING](https://github.com/wylon-cloud/comfyui-wylon/blob/main/CONTRIBUTING.md).

The workflow pack belongs in ComfyTV's user workflow folders. Only the ComfyUI-Wylon plugin belongs in `custom_nodes`.

## 🔑 Configure and generate

1. In ComfyUI, open **Wylon → Wylon tasks** and apply your Wylon API key. Alternatively set `WYLON_API_KEY` in the ComfyUI server's environment and restart it. This uses a Wylon API key; no Comfy account login is required.
2. In ComfyTV, select a Wylon workflow in an **Image** or **Video** stage.
3. Enter the stage prompt, choose supported options and supply the required media before queueing. Start with either Qwen image workflow or H3 text-to-video.
4. Open the saved result in ComfyTV. Image graphs end at native `SaveImage`; video graphs end at native `SaveVideo` and retain returned soundtracks. Presets read the save node's `ui_save_url`.

Keys are configured by the ComfyUI-Wylon plugin and shared by that server process. Optional local persistence stores plaintext in the ComfyUI user directory; this pack contains no credentials. See [key setup and removal](https://github.com/wylon-cloud/comfyui-wylon/blob/main/docs/USAGE.md#credentials-and-host-access).

## 🗂️ Included workflows

Copy **both files** in each row. Example media is not bundled.

| Workflow | Graph | ComfyTV preset | Required input |
| --- | --- | --- | --- |
| 🖼️ Qwen-Image-2512 | [JSON](workflows/image/wylon-qwen-2512.json) | [Preset](workflows/image/wylon-qwen-2512_preset.json) | Prompt |
| 🖼️ Qwen-Image-2.1 | [JSON](workflows/image/wylon-qwen-2-1.json) | [Preset](workflows/image/wylon-qwen-2-1_preset.json) | Prompt |
| 🎬 H3 text-to-video | [JSON](workflows/video/wylon-h3-text.json) | [Preset](workflows/video/wylon-h3-text_preset.json) | Prompt |
| 🎞️ H3 first/last frames | [JSON](workflows/video/wylon-h3-first-last.json) | [Preset](workflows/video/wylon-h3-first-last_preset.json) | Prompt and first image; second image is optional last frame |
| 🎧 H3 Ref2VA | [JSON](workflows/video/wylon-ref2va.json) | [Preset](workflows/video/wylon-ref2va_preset.json) | Prompt and at least one image or public video URL; audio is optional |

The first/last-frame preset removes the last-frame branch when the second image is absent. Ref2VA removes unused image/audio branches before submission. When opening a graph directly in ComfyUI, disconnect unused `LoadImage`/`LoadAudio` branches or select real files for every connected loader.

## ⚙️ Options and media limits

| Setting | Behavior |
| --- | --- |
| Prompt / seed | Stage prompt → `prompt`; stage seed → `seed`, with a random int31 when unset |
| Image mode / size | Keep `mode=async` for seed support and recovery; choose a model-supported size or `server_default` |
| Video duration | Stage `duration_s` → **5–15 whole seconds** |
| Video ratio | Stage `aspect_ratio`; default `16:9`; also supports `21:9`, `4:3`, `1:1`, `3:4`, `9:16` |
| Video resolution | Fixed at **768p**, independently of ComfyTV's display resolution selector |
| Advanced fields | Edit negative prompts and `extra_parameters` JSON in the workflow/sidebar; default JSON is `{}` |

- **H3** (`MiniMaxAI/MiniMax-H3`) supports text and dedicated first/last-frame roles. **Ref2VA** (`MiniMaxAI/MiniMax-H3-Ref2VA`) supports reference images, video and audio. Presets select the corresponding model; changing it also requires matching input roles.
- Ref2VA accepts at most **9 images, 3 video URLs and 3 audio inputs**. An image or video is required; audio alone is unsupported. It does not accept the dedicated first/last-frame roles.
- **Reference videos use public HTTPS URLs reachable by Wylon.** Edit `video_urls` in the ComfyTV sidebar as a literal, one URL per line; the supplied binding starts as empty `literal:`. A custom stage option may use `option:<your_key>`. Local `/view` links, ComfyTV video wires, uploaded filenames, Base64 and filesystem paths cannot supply a reference video. No automatic upload is provided.
- Reference naming in prompts follows the Wylon API. The pack does not translate ComfyTV `@image_N`, `@video_N` or `@audio_N` markers into model tags. Use Wylon reference ordering rules for mixed audio/video inputs.

See the plugin's [media limits and model guide](https://github.com/wylon-cloud/comfyui-wylon/blob/main/docs/USAGE.md#models-and-media) for reference durations, file sizes and supported parameters.

## 🔄 Recovery, updates and troubleshooting

Generation POSTs are never retried automatically. Preserve an accepted task ID from **Wylon tasks** or the error, then run **Wylon Resume Image Task** or **Wylon Resume Video Task** in ComfyUI to retrieve that same task. Requeueing a Generate node creates another task and may incur another charge. Stopping local waiting does not cancel cloud work. If creation times out without an ID, check Wylon history and usage before resubmitting.

| Problem | Check |
| --- | --- |
| Workflow not listed | Same-server setup, correct image/video folders and both paired files; rescan workflows |
| Loader fails before generation | Required first frame supplied; unused loaders disconnected when running directly in ComfyUI |
| Ref2VA validation fails | At least one image/video, correct model/roles, reference counts and public HTTPS URLs |
| Video size differs from stage selector | Service output is fixed at 768p |

**Update:** back up edited graphs/presets and generated media, replace only the ten JSON files listed above, keep each pair together, and rescan. Keep signed reference URLs out of shared workflows and presets.

**Uninstall:** remove those ten JSON files from the ComfyTV user workflow folders and rescan. ComfyUI-Wylon, ComfyTV, server credentials and existing results are managed separately. Removing workflows does not cancel remote tasks.

## 🤝 Support and contribution

Report bugs in [ComfyUI-Wylon Issues](https://github.com/wylon-cloud/comfyui-wylon/issues) with the pack/plugin/host versions, workflow name, reproducible steps and redacted errors. For sensitive reports, follow [SECURITY.md](https://github.com/wylon-cloud/comfyui-wylon/blob/main/SECURITY.md).

Development guidance: [CONTRIBUTING](https://github.com/wylon-cloud/comfyui-wylon/blob/main/CONTRIBUTING.md) · [Contributor checks](https://github.com/wylon-cloud/comfyui-wylon/blob/main/docs/VERIFICATION.md).

Upstream: [ComfyTV v1.13.1 custom workflows](https://github.com/jtydhr88/ComfyTV/blob/v1.13.1/docs/custom-workflows.md).

## 📄 License

[MIT](LICENSE) · [Third-party notices](THIRD_PARTY_NOTICES.md)
