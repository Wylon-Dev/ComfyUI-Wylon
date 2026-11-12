<div align="center">

<h1>ComfyUI-Wylon</h1>
<p><strong>将 Wylon 图像与视频生成接入你的 ComfyUI 工作流。</strong></p>

[![版本](https://img.shields.io/badge/version-0.3.1-blue)](CHANGELOG.zh-CN.md)
[![MIT 许可证](https://img.shields.io/github/license/wylon-cloud/comfyui-wylon)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![ComfyUI](https://img.shields.io/badge/ComfyUI-0.44.0-222222)](https://github.com/Comfy-Org/ComfyUI/tree/v0.44.0)
[![GitHub stars](https://img.shields.io/github/stars/wylon-cloud/comfyui-wylon?style=flat)](https://github.com/wylon-cloud/comfyui-wylon/stargazers)
[![最近提交](https://img.shields.io/github/last-commit/wylon-cloud/comfyui-wylon)](https://github.com/wylon-cloud/comfyui-wylon/commits/main)

[English](README.md) · **简体中文**

[快速安装](#-安装) · [示例工作流](#-示例工作流) · [使用指南](docs/USAGE.zh-CN.md) · [问题反馈](https://github.com/wylon-cloud/comfyui-wylon/issues)

</div>

通过 [Wylon API](https://wylon.cn)，在 ComfyUI 原生节点中使用 Qwen 生成图像、使用 MiniMax H3 生成视频。结果可继续接入其他节点，视频保留音轨，视频等待中断后可获取已受理任务的结果。**无需下载本地模型权重。**

- 🖼️ **图像生成：** 支持 Qwen-Image-2512 与 Qwen-Image-2.1，按模型提供尺寸预设。
- 🎬 **视频生成：** 通过 H3 与 Ref2VA 支持文生视频、首尾帧，以及图片、视频、音频参考。
- 🔌 **原生媒体：** 输出 `IMAGE`、`VIDEO`，接收原生 `IMAGE`/`AUDIO` 参考，同时返回任务 ID 与本地文件路径。
- 🔄 **任务恢复：** 任务面板与两个获取已有任务结果节点可查询已有任务，无需重新提交生成。

生成使用你的 Wylon 账户，受该账户的模型权限、计费和用量限制约束。

## 🧭 选择适合的集成

| 集成 | 提供内容 | 宿主与安装方式 |
| --- | --- | --- |
| 🔌 **ComfyUI-Wylon** — 本仓库 | 六个 Python 节点、API Key 配置与任务面板 | 安装到 **ComfyUI v0.44.0** |
| 🎞️ [**Toonflow-Wylon**](https://github.com/wylon-cloud/toonflow-wylon) | 独立的 `wylon.ts` 提供方 | 安装到 **Toonflow v2.0.10**；无需 ComfyUI |
| 🧩 [**Wylon ComfyTV 工作流**](https://github.com/wylon-cloud/comfyui-wylon/tree/main/comfytv-workflows) | 五套工作流与配对的 ComfyTV 预设 | 可选工作流包；要求 **ComfyTV v1.13.1 与 ComfyUI-Wylon 安装在同一 ComfyUI 服务器** |

ComfyUI 运行时 ZIP 包含下方五个生成示例和两个获取已有任务结果的示例工作流。可选 ComfyTV 工作流包独立分发，其[安装指南](https://github.com/wylon-cloud/comfyui-wylon/blob/main/comfytv-workflows/README.zh-CN.md)说明工作流与预设的复制位置。

## 📦 安装

需要可正常运行、支持**原生 V3 节点及媒体 API 的 ComfyUI**、**Python 3.10+**、Wylon API Key，以及到 Wylon 和结果素材主机的网络连接。宿主版本：**ComfyUI v0.44.0**。

| 平台 | 安装方式 |
| --- | --- |
| **Windows 10/11 x64** | 手动 Python/venv 安装，或官方 ComfyUI Windows 便携版 |
| **macOS** | 使用 ComfyUI 自身 Python 环境的源码安装 |

请使用运行 ComfyUI 的 Python 解释器。插件的 `web/` 已附带编译后的前端，**普通安装不需要 Node.js 或 npm**。依赖包括 `aiohttp`、Pillow、numpy 和 PyAV；PyTorch 及宿主依赖由 ComfyUI 提供。

### 手动 Python / 虚拟环境安装

**macOS/Linux** 先启用 ComfyUI 的环境，再在 **ComfyUI 根目录**执行：

```sh
git clone https://github.com/wylon-cloud/comfyui-wylon.git custom_nodes/ComfyUI-Wylon
python -m pip install -r custom_nodes/ComfyUI-Wylon/requirements.txt
```

**Windows 10/11 x64 手动/venv 安装**时，在 **ComfyUI 根目录**打开 PowerShell。以下假定虚拟环境名为 `.venv`；路径不同时，请替换为实际启动宿主的解释器。

```powershell
git clone https://github.com/wylon-cloud/comfyui-wylon.git .\custom_nodes\ComfyUI-Wylon
.\.venv\Scripts\python.exe -m pip install -r .\custom_nodes\ComfyUI-Wylon\requirements.txt
```

### 官方 Windows 便携版安装

在**便携发行版根目录**打开 PowerShell，也就是包含 `python_embeded` 和 `ComfyUI` 的目录，执行：

```powershell
git clone https://github.com/wylon-cloud/comfyui-wylon.git .\ComfyUI\custom_nodes\ComfyUI-Wylon
.\python_embeded\python.exe -m pip install -r .\ComfyUI\custom_nodes\ComfyUI-Wylon\requirements.txt
```

### ZIP 安装

1. 下载[源码 ZIP](https://github.com/wylon-cloud/comfyui-wylon/archive/refs/heads/main.zip)。
2. 解压，将 `comfyui-wylon-main` 重命名为 `ComfyUI-Wylon`，直接放入 `ComfyUI/custom_nodes/`。最终路径应为 `ComfyUI/custom_nodes/ComfyUI-Wylon/__init__.py`。
3. 根据安装方式执行上方依赖命令，然后**重启 ComfyUI 并刷新浏览器页面**。

本地构建的 `ComfyUI-Wylon-0.3.1.zip` 已包含正确命名的插件目录。在源码检出目录执行 `npm run package`（开发工具链）或使用选定 Python 执行 `python scripts/package.py`，可构建该运行时包与独立的 `Wylon-ComfyTV-Workflows-0.3.1.zip`；构建与检查步骤见[贡献指南](CONTRIBUTING.zh-CN.md)。

## 🔑 配置 API Key

1. 在 [Wylon](https://wylon.cn) 获取 API Key。
2. 打开 ComfyUI 的 **Wylon → Wylon tasks / Wylon 任务**，或点击 Wylon 生成/获取结果节点底部的 **Wylon 配置 / API Key**。
3. 输入 Key，点击**应用 API Key**。面板会分别展示有效配置来源与连接检查结果。
4. 如需重启后保留，可勾选**记住本机（保存到 ComfyUI 用户目录的私有配置）**。

Key 保留在服务端，不写入工作流输入或生成元数据。配置对整个 **ComfyUI 服务进程**生效，由该服务器的用户共享。选择本机保存后，Key 将以明文存放于 `<ComfyUI 用户目录>/wylon/private/credentials.json`，请在可信宿主上使用。

服务端也可在启动 ComfyUI 前设置 `WYLON_API_KEY`。Windows 手动/venv 安装可在 ComfyUI 根目录执行：

```powershell
$env:WYLON_API_KEY = '你的 Key'
.\.venv\Scripts\python.exe main.py
```

官方便携版在便携发行版根目录设置同一变量后，运行平时使用的启动脚本，例如 `.\run_nvidia_gpu.bat`。变量对该 PowerShell 会话启动的进程生效。

有效来源优先级为**会话 → 本机保存 → 环境变量**。默认 API 地址为 `https://api.wylon.cn/v1`。环境命令、来源切换和清除方式见[密钥配置与宿主访问](docs/USAGE.zh-CN.md#密钥与宿主访问)。

## 🚀 首次生成

1. 在 ComfyUI 中加载 [Qwen-Image-2.1 示例](example_workflows/wylon-qwen-2-1.json)，或从 **Wylon** 节点分类添加 **Wylon Generate Image**。
2. 选择 Qwen 模型并填写提示词；图像生成固定为同步请求。尺寸使用 `server_default` 或所选模型支持的预设。
3. 将 `IMAGE` 接入原生 **Preview Image** 或 **Save Image**，然后运行队列。
4. 文生视频可加载 [H3 示例](example_workflows/wylon-h3-text.json)，使用固定的 `MiniMaxAI/MiniMax-H3` 模型，将 `VIDEO` 接入原生 **Save Video**。

图像生成固定使用同步 `POST /v1/images/generations`，返回成品图片，不返回任务 ID。两个视频生成节点先提交 Wylon 异步任务，再持续等待成品；没有独立的“仅提交并返回 ID”节点。

下载结果位于 `<ComfyUI 输出目录>/wylon/`，通常为 `ComfyUI/output/wylon/`。原生 Save Image / Save Video 可另外保存副本。**Wylon 任务**面板展示任务信息和最近的本地结果。

## 🧪 示例工作流

在 ComfyUI 中打开 JSON 文件，或将其拖入画布。已连接的加载节点需要你提供媒体；示例不包含素材与 API Key。

| 工作流 | 适用场景 |
| --- | --- |
| [Qwen-Image-2512](example_workflows/wylon-qwen-2512.json) | 使用 Qwen-Image-2512 文生图 |
| [Qwen-Image-2.1](example_workflows/wylon-qwen-2-1.json) | 使用 Qwen-Image-2.1 文生图 |
| [H3 文生视频](example_workflows/wylon-h3-text.json) | 通过文字提示词生成视频 |
| [H3 首尾帧](example_workflows/wylon-h3-first-last.json) | 通过专用首尾帧端口引导视频 |
| [Ref2VA 多模态参考](example_workflows/wylon-ref2va.json) | 图片、视频和音频参考；须提供图片或视频，并断开未使用的加载节点 |

已有任务 ID 可用[获取图像任务结果](example_workflows/wylon-get-image-task-result.json)或[获取视频任务结果](example_workflows/wylon-get-video-task-result.json)示例。图片获取示例接受历史异步图片任务 ID，当前图片生成节点不能创建这类任务。粘贴已有 ID 后加入队列即可；它们独立于五套 ComfyTV 图/预设。获取节点可单独运行，也可将原生 `IMAGE`/`VIDEO` 接入其他节点。

## 🧠 模型与原生端口

| 模型 | 本集成支持的生成方式 | 输入与限制 |
| --- | --- | --- |
| `Qwen/Qwen-Image-2512` | 文生图 | 提示词与模型专属尺寸；每次请求一张图 |
| `Qwen/Qwen-Image-2.1` | 文生图 | 提示词与模型专属尺寸；每次请求一张图 |
| `MiniMaxAI/MiniMax-H3` | 文生视频、首尾帧视频 | 可选原生 `first_frame` / `last_frame`，每个端口一张图 |
| `MiniMaxAI/MiniMax-H3-Ref2VA` | 图片、视频、音频参考视频生成 | 最多 **9 张图、3 个视频 URL、3 段音频**；至少提供一张图或一个视频 |

视频输出为 **768p、5–15 整数秒**。Ref2VA 不接受专用首尾帧角色，也不支持仅音频参考。参考视频须为 **Wylon 可访问的公网 HTTPS URL**，在 **Wylon 参考视频链接**节点的 `urls` 控件中每行填写一个，再连接 Ref2VA 的 `reference_videos` 端口。不支持本地路径、Base64 视频、localhost/局域网 URL 或自动上传。

| 节点 | 稳定节点 ID | 原生媒体端口 |
| --- | --- | --- |
| **Wylon Generate Image** | `WylonGenerateImage` | 输出 `IMAGE` |
| **Wylon H3 Video** | `WylonH3Video` | `IMAGE` 首尾帧输入 → `VIDEO` 输出；固定 H3 |
| **Wylon Ref2VA Video** | `WylonRef2VAVideo` | 原生 `IMAGE`/`AUDIO` 参考及专用视频参考数据 → `VIDEO` 输出；固定 Ref2VA |
| **Wylon 参考视频链接** | `WylonReferenceVideoURL` | 公网 HTTPS URL → `WYLON_REFERENCE_VIDEO` 专用参考数据 |
| **Wylon 获取已有图片任务结果** | `WylonResumeImageTask` | 已有 `task_id` → `IMAGE` 输出 |
| **Wylon 获取已有视频任务结果** | `WylonResumeVideoTask` | 已有 `task_id` → `VIDEO` 输出 |

**Wylon 参考视频链接**只校验并封装 URL，不下载、上传或生成媒体，不读取 API Key，也不需要配置按钮。`urls` 为空时输出空参考数据，图像参考工作流仍可运行；Ref2VA 仍要求至少一张参考图片或一个参考视频。专用 `WYLON_REFERENCE_VIDEO` 连线与承载生成结果的原生 `VIDEO` 不同，连接本地视频输出不会自动上传。Ref2VA 没有 URL 文本控件。

两个视频节点分别固定模型且仅显示各自支持的输入：H3 用于文字/首尾帧，Ref2VA 用于参考素材，均不提供模型选择器。生成/获取结果节点保留 `task_id` 和 `file_path` 输出；图像生成的 `task_id` 始终为空以保持兼容，不具备按任务 ID 恢复的能力。原生 `VIDEO` 保留下载 MP4 的音轨。

图像尺寸、参考媒体时长/大小限制及原生视频组件连接方式见[模型与媒体](docs/USAGE.zh-CN.md#模型与媒体)。服务端能力请参阅 Wylon 的[图像生成文档](https://portal.wylon.cn/zh/docs-generation-images.html)与[视频生成文档](https://portal.wylon.cn/zh/docs-generation-videos.html)。

视频请求会在 API 支持范围内转发非负 `seed`；`-1` 表示省略。种子效果由模型支持决定，固定值不保证相同输出。`control_after_generate` 只调整下次运行的本地视频种子，不是 API 参数。图像生成没有模式、种子及种子策略控件。

## 🔄 恢复与故障排查

生成 POST **不会自动重试**。视频或已有历史图片任务超时、中断或下载失败后，从面板或错误信息中复制已受理的任务 ID，填入 **Wylon 获取已有图片任务结果** 或 **Wylon 获取已有视频任务结果**。获取已有任务结果通过 GET 查询同一个任务并下载结果，不创建、重启或取消云端任务。

生成节点失败后不会向下游传递 `task_id` 输出，须手工从任务面板或错误信息复制 ID 到获取节点。

停止本地等待不会取消云端任务。创建超时且**没有任务 ID**时，请先核查 Wylon 历史记录与用量，再决定是否重新提交。再次运行 Generate 节点会发送新的生成请求，可能再次计费。

| 现象 | 优先检查 |
| --- | --- |
| 找不到节点或 Wylon 菜单 | 目录层级、宿主版本、依赖是否装在 ComfyUI 的 Python 中；重启并刷新 |
| Key 无效或账户与预期不符 | 面板中的有效来源；会话/本机保存的 Key 优先于环境变量 |
| 参考输入校验失败 | 节点固定模型、连接的角色、媒体数量及公网 HTTPS 视频 URL |
| 下载或编解码失败 | 检查网络、磁盘空间及 PyAV；已有任务 ID 时请保留，并在结果仍可用时使用获取已有任务结果节点 |

更多说明：[恢复与故障排查](docs/USAGE.zh-CN.md#恢复与故障排查) · [更新与卸载](docs/USAGE.zh-CN.md#更新与卸载)。

## 🤝 参与贡献与获取帮助

安装问题和缺陷请提交 [GitHub Issues](https://github.com/wylon-cloud/comfyui-wylon/issues)，附上宿主/插件版本、工作流名称、复现步骤及脱敏错误。敏感报告请按照[安全说明](SECURITY.zh-CN.md)处理。

欢迎贡献：[开发与检查](CONTRIBUTING.zh-CN.md) · [贡献检查指引](docs/VERIFICATION.md) · [变更记录](CHANGELOG.zh-CN.md)。

## ⭐ 社区


<div align="center">

**访问计数** · 由 [MoeCounter](https://github.com/journey-ad/Moe-Counter) 提供

![访问计数](https://count.getloli.com/@Wylon-Dev.ComfyUI-Wylon?theme=cat-girls-yay)

![Star History](https://api.star-history.com/svg?repos=wylon-cloud/comfyui-wylon&type=Date)

</div>

## 📄 许可证

[MIT](LICENSE) · [第三方声明](THIRD_PARTY_NOTICES.md)
