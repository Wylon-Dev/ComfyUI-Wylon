<div align="center">

<h1>ComfyUI-Wylon</h1>
<p><strong>Wylon image and video generation, connected to your ComfyUI workflows.</strong></p>

[![Version](https://img.shields.io/badge/version-0.2.0-blue)](CHANGELOG.md)
[![MIT License](https://img.shields.io/github/license/wylon-cloud/comfyui-wylon)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![ComfyUI](https://img.shields.io/badge/ComfyUI-0.44.0-222222)](https://github.com/Comfy-Org/ComfyUI/tree/v0.44.0)
[![GitHub stars](https://img.shields.io/github/stars/wylon-cloud/comfyui-wylon?style=flat)](https://github.com/wylon-cloud/comfyui-wylon/stargazers)
[![Last commit](https://img.shields.io/github/last-commit/wylon-cloud/comfyui-wylon)](https://github.com/wylon-cloud/comfyui-wylon/commits/main)

**English** · [简体中文](README.zh-CN.md)

[Quick start](#-install) · [Example workflows](#-example-workflows) · [Usage guide](docs/USAGE.md) · [Report a bug](https://github.com/wylon-cloud/comfyui-wylon/issues)

</div>

Generate images with Qwen and videos with MiniMax H3 through the [Wylon API](https://wylon.cn), using native ComfyUI nodes. Connect results to the rest of your graph, keep video soundtracks, and resume accepted asynchronous tasks after interrupted waiting. **No local model weights are required.**

- 🖼️ **Image generation:** Qwen-Image-2512 and Qwen-Image-2.1, with model-specific size presets.
- 🎬 **Video generation:** text, first/last frames, or image/video/audio references through H3 and Ref2VA.
- 🔌 **Native media:** `IMAGE` and `VIDEO` outputs, native `IMAGE`/`AUDIO` reference inputs, plus task IDs and local file paths.
- 🔄 **Task recovery:** a task panel and two Resume nodes retrieve existing tasks without submitting a new generation.

Generation uses your Wylon account and is subject to its model access, usage charges and limits.

## 🧭 Choose your integration

| Integration | What it provides | Host / installation |
| --- | --- | --- |
| 🔌 **ComfyUI-Wylon** — this repository | Five Python nodes, API key configuration and a task panel | Install in **ComfyUI v0.44.0** |
| 🎞️ [**Toonflow-Wylon**](https://github.com/wylon-cloud/toonflow-wylon) | A standalone `wylon.ts` provider | Install in **Toonflow v2.0.10**; no ComfyUI required |
| 🧩 [**Wylon ComfyTV workflows**](https://github.com/wylon-cloud/comfyui-wylon/tree/main/comfytv-workflows) | Five workflows with paired ComfyTV presets | Optional pack; requires **ComfyTV v1.13.1 and ComfyUI-Wylon on the same ComfyUI server** |

The ComfyUI runtime ZIP includes the five ordinary example workflows below. The optional ComfyTV pack is distributed separately; its [installation guide](https://github.com/wylon-cloud/comfyui-wylon/blob/main/comfytv-workflows/README.md) explains where to copy the workflow/preset pairs.

## 📦 Install

You need a working **ComfyUI with the native V3 node/media API**, **Python 3.10+**, a Wylon API key and network access to Wylon and its result hosts. Host version: **ComfyUI v0.44.0**.

| Platform | Installation method |
| --- | --- |
| **Windows 10/11 x64** | Manual Python/venv or official ComfyUI Windows portable |
| **macOS** | ComfyUI source installation using its Python environment |

Use the Python interpreter that runs ComfyUI. The plugin ships compiled frontend files in `web/`; **ordinary installation needs neither Node.js nor npm**. Dependencies are `aiohttp`, Pillow, numpy and PyAV; ComfyUI supplies PyTorch and its host dependencies.

### Manual Python / virtual environment installation

On **macOS/Linux**, activate your ComfyUI environment and run from the **ComfyUI root**:

```sh
git clone https://github.com/wylon-cloud/comfyui-wylon.git custom_nodes/ComfyUI-Wylon
python -m pip install -r custom_nodes/ComfyUI-Wylon/requirements.txt
```

On **Windows 10/11 x64 with a manual/venv installation**, run from the **ComfyUI root** in PowerShell. This example uses a virtual environment named `.venv`; substitute the interpreter that starts your host if its path differs.

```powershell
git clone https://github.com/wylon-cloud/comfyui-wylon.git .\custom_nodes\ComfyUI-Wylon
.\.venv\Scripts\python.exe -m pip install -r .\custom_nodes\ComfyUI-Wylon\requirements.txt
```

### Official Windows portable installation

Run these commands in PowerShell from the **portable distribution root**, the folder containing `python_embeded` and `ComfyUI`:

```powershell
git clone https://github.com/wylon-cloud/comfyui-wylon.git .\ComfyUI\custom_nodes\ComfyUI-Wylon
.\python_embeded\python.exe -m pip install -r .\ComfyUI\custom_nodes\ComfyUI-Wylon\requirements.txt
```

### ZIP installation

1. Download the [source ZIP](https://github.com/wylon-cloud/comfyui-wylon/archive/refs/heads/main.zip).
2. Extract it, rename `comfyui-wylon-main` to `ComfyUI-Wylon`, and place that folder directly inside `ComfyUI/custom_nodes/`. The result must be `ComfyUI/custom_nodes/ComfyUI-Wylon/__init__.py`.
3. Run the dependency command above for your installation, then **restart ComfyUI and refresh the browser page**.

A locally built `ComfyUI-Wylon-0.2.0.zip` already contains the correctly named plugin folder. To build that runtime archive and the separate `Wylon-ComfyTV-Workflows-0.2.0.zip` from a source checkout, run `npm run package` (developer tooling) or `python scripts/package.py` with the selected Python; see [CONTRIBUTING](CONTRIBUTING.md) for build and validation steps.

## 🔑 Configure your API key

1. Obtain a Wylon API key from [Wylon](https://wylon.cn).
2. Open **Wylon → Wylon tasks** in ComfyUI, or click **Wylon configuration / API Key** at the bottom of a Wylon node.
3. Enter the key and click **Apply API key**. The panel shows the effective credential source and a separate connection check.
4. Optionally enable **Remember on this machine (private ComfyUI user configuration)** to retain the key after restarting.

The key stays on the server and is excluded from workflow inputs and generated metadata. Configuration applies to the **ComfyUI server process**, shared by users of that server. Opt-in persistence stores plaintext at `<ComfyUI user directory>/wylon/private/credentials.json`; use it on a trusted host.

For a server-managed setup, set `WYLON_API_KEY` before starting ComfyUI. For a Windows manual/venv installation, run from the ComfyUI root:

```powershell
$env:WYLON_API_KEY = 'your-key'
.\.venv\Scripts\python.exe main.py
```

For official portable, set the same variable from the portable distribution root, then launch your usual script, for example `.\run_nvidia_gpu.bat`. The variable applies to processes started from that PowerShell session.

Effective priority is **session → saved local → environment**. The default API base is `https://api.wylon.cn/v1`. See [credential setup, environment commands and removal](docs/USAGE.md#credentials-and-host-access) for details.

## 🚀 Your first generation

1. Load the [Qwen-Image-2.1 example](example_workflows/wylon-qwen-2-1.json) in ComfyUI, or add **Wylon Generate Image** from the **Wylon** node category.
2. Select a Qwen model, enter a prompt, and keep `mode=async` for task recovery. Use `server_default` or a size supported by the selected model.
3. Connect `IMAGE` to native **Preview Image** or **Save Image**, then queue the workflow.
4. For text-to-video, load the [H3 example](example_workflows/wylon-h3-text.json), keep `MiniMaxAI/MiniMax-H3` selected, and connect `VIDEO` to native **Save Video**.

Downloaded results are stored under `<ComfyUI output directory>/wylon/` (normally `ComfyUI/output/wylon/`). Native Save Image / Save Video can save additional copies. The **Wylon tasks** panel shows task information and recent local results.

## 🧪 Example workflows

Open a JSON file in ComfyUI or drag it onto the canvas. Supply your own media for connected loader nodes; example media and API keys are not bundled.

| Workflow | Start here for |
| --- | --- |
| [Qwen-Image-2512](example_workflows/wylon-qwen-2512.json) | Text-to-image with Qwen-Image-2512 |
| [Qwen-Image-2.1](example_workflows/wylon-qwen-2-1.json) | Text-to-image with Qwen-Image-2.1 |
| [H3 text-to-video](example_workflows/wylon-h3-text.json) | Video from a text prompt |
| [H3 first/last frames](example_workflows/wylon-h3-first-last.json) | Video guided by dedicated frame inputs |
| [Ref2VA references](example_workflows/wylon-ref2va.json) | Image/video/audio references; provide an image or video and disconnect unused loaders |

## 🧠 Models and native ports

| Model | Supported generation in this integration | Inputs / limits |
| --- | --- | --- |
| `Qwen/Qwen-Image-2512` | Text-to-image | Prompt and model-specific size; one image per request |
| `Qwen/Qwen-Image-2.1` | Text-to-image | Prompt and model-specific size; one image per request |
| `MiniMaxAI/MiniMax-H3` | Text-to-video, first/last-frame video | Optional native `first_frame` / `last_frame`, one image each |
| `MiniMaxAI/MiniMax-H3-Ref2VA` | Video with image/video/audio references | Up to **9 images, 3 video URLs, 3 audio clips**; requires at least one image or video |

Video output is **768p, 5–15 whole seconds**. Ref2VA does not accept the dedicated first/last-frame roles; audio alone is insufficient. Reference videos must be **public HTTPS URLs reachable by Wylon**, one per line in `video_urls`. Local paths, Base64 video, localhost/LAN URLs and automatic uploading are unsupported.

| Node | Stable node ID | Native media ports |
| --- | --- | --- |
| **Wylon Generate Image** | `WylonGenerateImage` | `IMAGE` output |
| **Wylon H3 Video** | `WylonH3Video` | `IMAGE` frame inputs → `VIDEO` output; defaults to H3 |
| **Wylon Ref2VA Video** | `WylonRef2VAVideo` | Native `IMAGE`/`AUDIO` references + video URLs → `VIDEO` output; defaults to Ref2VA |
| **Wylon Resume Image Task** | `WylonResumeImageTask` | Existing `task_id` → `IMAGE` output |
| **Wylon Resume Video Task** | `WylonResumeVideoTask` | Existing `task_id` → `VIDEO` output |

Both video nodes expose both models; select the model explicitly and connect its supported input roles. They never switch models automatically. Every generation/resume node also returns `task_id` and `file_path`; synchronous image generation returns no recoverable task ID. Native `VIDEO` retains the downloaded MP4's soundtrack.

See [models and media](docs/USAGE.md#models-and-media) for image sizes, clip duration/size limits, advanced parameters and native video component connections. Wylon's service documentation covers [image generation](https://portal.wylon.cn/zh/docs-generation-images.html) and [video generation](https://portal.wylon.cn/zh/docs-generation-videos.html).

## 🔄 Recovery and troubleshooting

Generation POSTs are **never retried automatically**. After a timeout, interruption or download failure, copy the accepted task ID from the panel/error into **Wylon Resume Image Task** or **Wylon Resume Video Task**. Resume queries the same task and downloads its result without creating another generation.

Stopping local waiting does not cancel cloud work. If creation times out **without a task ID**, check Wylon history and usage before resubmitting. Requeueing a Generate node creates a new task and may incur another charge.

| Symptom | First check |
| --- | --- |
| Nodes or Wylon menu missing | Correct folder nesting, host version and dependencies in ComfyUI's Python; restart and refresh |
| Key rejected or unexpected account | Effective key source in the panel; session/saved keys override the environment |
| Reference validation error | Selected model, connected roles, media counts and public HTTPS video URLs |
| Download or codec failure | Preserve the task ID; check network, disk space and PyAV, then use a Resume node if the result is still available |

More: [recovery and troubleshooting](docs/USAGE.md#recovery-and-troubleshooting) · [update and uninstall](docs/USAGE.md#update-and-uninstall).

## 🤝 Contribute and get help

Use [GitHub Issues](https://github.com/wylon-cloud/comfyui-wylon/issues) for bugs and installation problems. Include host/plugin versions, the workflow name, reproducible steps and a redacted error. For sensitive reports, follow [SECURITY.md](SECURITY.md).

Contributions are welcome: [development and checks](CONTRIBUTING.md) · [contributor checks](docs/VERIFICATION.md) · [changelog](CHANGELOG.md).

## ⭐ Community


<div align="center">

**Page views** · powered by [MoeCounter](https://github.com/journey-ad/Moe-Counter)

![Page views](https://count.getloli.com/@Wylon-Dev.ComfyUI-Wylon?theme=cat-girls-yay)

![Star History](https://api.star-history.com/svg?repos=wylon-cloud/comfyui-wylon&type=Date)

</div>

## 📄 License

[MIT](LICENSE) · [Third-party notices](THIRD_PARTY_NOTICES.md)
