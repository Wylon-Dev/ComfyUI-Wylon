<div align="center">

<h1>Wylon ComfyTV 工作流</h1>
<p><strong>可直接导入 ComfyTV 的 Wylon 图像与视频工作流。</strong></p>

[![版本](https://img.shields.io/badge/version-0.3.2-blue)](manifest.json)
[![MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![ComfyTV](https://img.shields.io/badge/ComfyTV-1.13.1-222222)](https://github.com/jtydhr88/ComfyTV/tree/v1.13.1)

[English](README.md) · **简体中文**

</div>

在 ComfyTV 阶段中使用 Qwen 生成图像、使用 MiniMax H3 生成视频。本可选工作流包提供**五个 ComfyUI 工作流与五个配套 ComfyTV 预设**，包含阶段提示词及视频种子绑定、原生保存结果读取，以及可选参考分支裁剪。

## 🧩 需要安装什么

| 组件 | 作用 | 安装位置 |
| --- | --- | --- |
| [**ComfyUI-Wylon**](https://github.com/wylon-cloud/comfyui-wylon/blob/main/README.zh-CN.md#-安装) | Python 生成/恢复节点、API Key 配置与任务面板 | 插件安装到 `ComfyUI/custom_nodes/ComfyUI-Wylon/` |
| **本工作流包** | ComfyTV 工作流与 `_preset.json` 绑定 | 成对 JSON 文件复制到 ComfyTV 用户工作流目录 |

**ComfyTV 与 ComfyUI-Wylon 必须运行在同一台 ComfyUI 服务器。** 本包复用该服务器的节点和凭据，无需额外节点副本、npm 安装或本地模型权重。

宿主版本：**ComfyUI v0.44.0 + ComfyTV v1.13.1 + ComfyUI-Wylon v0.3.2**。[清单](manifest.json)记录文件配对、节点 ID 及兼容信息。

| 平台 | ComfyUI 安装方式 |
| --- | --- |
| Windows 10/11 x64 | 手动/venv 或官方 Windows 便携版 |
| macOS | ComfyUI 源码安装 |

下方 Windows 复制说明使用文件资源管理器或 PowerShell，无需 Bash/GCC。

两种 Windows 安装都使用同一服务器及工作流目录规则。便携版中的 `<ComfyUI>` 指**内层 `ComfyUI` 目录**，不是外层发行版根目录。

## 📦 从源码目录或 ZIP 安装

1. 在同一服务器上，分别按照说明安装 [ComfyUI-Wylon](https://github.com/wylon-cloud/comfyui-wylon/blob/main/README.zh-CN.md#-安装) 和 [ComfyTV](https://github.com/jtydhr88/ComfyTV/tree/v1.13.1)。
2. 从[仓库源码目录](https://github.com/wylon-cloud/comfyui-wylon/tree/main/comfytv-workflows)获取本包，或下载并解压[仓库源码 ZIP](https://github.com/wylon-cloud/comfyui-wylon/archive/refs/heads/main.zip)。源码检出或解压后，工作流包位于 `comfytv-workflows/`。
3. 先备份目标目录中的同名文件，再复制下列源目录中的**内容**；目标目录不存在时可创建：

   | 工作流包源目录 | ComfyUI 服务器上的目标目录 |
   | --- | --- |
   | `workflows/image/` | `<ComfyUI>/user/comfytv/workflows/image/` |
   | `workflows/video/` | `<ComfyUI>/user/comfytv/workflows/video/` |

4. 将每个工作流 `.json` 与配套 `_preset.json` 放在一起，然后重启 ComfyUI 或在 ComfyTV 中重新扫描工作流。

Windows 可使用文件资源管理器：打开包内 `workflows`，将 JSON 文件复制到上方对应的目标文件夹。也可在**工作流包根目录**（源码中的 `comfytv-workflows` 或解压后的独立包）运行 PowerShell：

```powershell
$ComfyUIRoot = 'C:\AI\ComfyUI'
New-Item -ItemType Directory -Force -Path "$ComfyUIRoot\user\comfytv\workflows\image", "$ComfyUIRoot\user\comfytv\workflows\video" | Out-Null
Copy-Item .\workflows\image\*.json "$ComfyUIRoot\user\comfytv\workflows\image\"
Copy-Item .\workflows\video\*.json "$ComfyUIRoot\user\comfytv\workflows\video\"
```

将 `$ComfyUIRoot` 替换为实际宿主路径，例如便携版的 `C:\AI\ComfyUI_windows_portable\ComfyUI`。

如需本地构建，在**仓库根目录**使用开发工具链（Node.js 22.23.x、npm 与 Python）运行 `npm run package`，或用选定 Python 执行 `python scripts/package.py`，会生成独立的 `Wylon-ComfyTV-Workflows-0.3.2.zip`。解压后的包根目录为 `Wylon-ComfyTV-Workflows`，按上方步骤复制文件即可。构建详情见[贡献指南](https://github.com/wylon-cloud/comfyui-wylon/blob/main/CONTRIBUTING.zh-CN.md)。

工作流包放入 ComfyTV 用户工作流目录；只有 ComfyUI-Wylon 插件放入 `custom_nodes`。

## 🔑 配置并开始生成

1. 在 ComfyUI 打开 **Wylon → Wylon tasks / Wylon 任务**，应用 Wylon API Key。也可在 ComfyUI 服务器环境中设置 `WYLON_API_KEY`，然后重启服务。本集成使用 Wylon API Key，无需登录 Comfy 账号。
2. 在 ComfyTV 的**图像**或**视频**阶段选择对应 Wylon 工作流。
3. 填写阶段提示词、选择支持的参数，并提供必需媒体后运行。首次可选择任一 Qwen 图像工作流或 H3 文生视频。
4. 在 ComfyTV 中查看保存结果。图像工作流以原生 `SaveImage` 结束；视频工作流以原生 `SaveVideo` 结束，保留返回音轨。预设读取保存节点的 `ui_save_url`。

Key 由 ComfyUI-Wylon 插件配置，在该服务器进程内共享。可选本机保存会将明文 Key 存入 ComfyUI 用户目录；本包不包含凭据。详见[密钥配置与移除](https://github.com/wylon-cloud/comfyui-wylon/blob/main/docs/USAGE.zh-CN.md#密钥与宿主访问)。

## 🗂️ 随包工作流

每行的**两个文件都需要复制**。包中不附示例媒体。

| 工作流 | 工作流文件 | ComfyTV 预设 | 必需输入 |
| --- | --- | --- | --- |
| 🖼️ Qwen-Image-2512 | [JSON](workflows/image/wylon-qwen-2512.json) | [预设](workflows/image/wylon-qwen-2512_preset.json) | 提示词 |
| 🖼️ Qwen-Image-2.1 | [JSON](workflows/image/wylon-qwen-2-1.json) | [预设](workflows/image/wylon-qwen-2-1_preset.json) | 提示词 |
| 🎬 H3 文生视频 | [JSON](workflows/video/wylon-h3-text.json) | [预设](workflows/video/wylon-h3-text_preset.json) | 提示词 |
| 🎞️ H3 首尾帧 | [JSON](workflows/video/wylon-h3-first-last.json) | [预设](workflows/video/wylon-h3-first-last_preset.json) | 提示词与首图；第二张图可选，作为尾帧 |
| 🎧 H3 Ref2VA | [JSON](workflows/video/wylon-ref2va.json) | [预设](workflows/video/wylon-ref2va_preset.json) | 提示词，及至少一张图或一个公网视频 URL；音频可选 |

首尾帧预设会在第二张图缺失时移除尾帧分支。Ref2VA 会在提交前移除未使用的图像/音频分支。直接在 ComfyUI 打开工作流时，请断开未使用的 `LoadImage`/`LoadAudio` 分支，或为每个已连接的加载节点选择真实文件。

## ⚙️ 参数与媒体限制

| 设置 | 行为 |
| --- | --- |
| 提示词 / 视频种子 | 阶段提示词 → `prompt`；视频阶段种子 → `seed`，未设置时随机生成 int31；图像阶段不绑定种子 |
| 图像生成 / 尺寸 | 同步 `images/generations`，不返回任务 ID；选择模型支持的尺寸或 `server_default` |
| 视频时长 | 阶段 `duration_s` → **5–15 整数秒** |
| 视频比例 | 阶段 `aspect_ratio`，默认 `16:9`；另支持 `21:9`、`4:3`、`1:1`、`3:4`、`9:16` |
| 视频分辨率 | 固定 **768p**，不受 ComfyTV 显示分辨率选择器影响 |
| 负向提示词 | 在工作流或侧栏编辑 `negative_prompt` |

- **H3**（`MiniMaxAI/MiniMax-H3`）支持文字及专用首尾帧角色；**Ref2VA**（`MiniMaxAI/MiniMax-H3-Ref2VA`）支持图像、视频和音频参考。两个节点分别固定对应模型，无模型选择器。
- Ref2VA 最多接受 **9 张图、3 个视频 URL 和 3 段音频**。必须提供图像或视频，不支持仅音频参考，也不接受专用首尾帧角色。
- **参考视频须使用 Wylon 可访问的公网 HTTPS URL。** 在 ComfyTV 侧栏将 **Wylon 参考视频链接**节点的 `urls` 设为字面值，每行一个 URL，最多三个；随包绑定默认为空 `literal:`。预设绑定此源节点，其专用输出连接到 Ref2VA 的 `reference_videos` 端口。自定义阶段选项也可使用 `option:<参数名>`。本地 `/view` 链接、ComfyTV 视频连线、上传文件名、Base64 和文件路径均不能用作参考视频。本包不提供自动上传。
- 空 URL 源输出空参考数据，可仅使用图片参考；Ref2VA 仍要求图片或视频。URL 源只校验 URL，不读取凭据、不下载、不上传、不生成，也不计费。专用 `WYLON_REFERENCE_VIDEO` 连接不能用原生生成结果 `VIDEO` 代替。Ref2VA 没有 URL 文本控件。
- 提示词中的参考命名遵循 Wylon API。本包不将 ComfyTV 的 `@image_N`、`@video_N`、`@audio_N` 标记转换为模型标签；混合音视频输入应遵循 Wylon 的参考编号规则。

参考媒体时长、文件大小和支持的参数，详见插件[模型与媒体指南](https://github.com/wylon-cloud/comfyui-wylon/blob/main/docs/USAGE.zh-CN.md#模型与媒体)。

图像生成固定同步，不返回任务 ID，没有模式或种子控件。视频生成使用异步 API 并等待成品；在 API 支持范围内转发非负视频种子，`-1` 省略种子，效果由模型决定。`control_after_generate` 只是本地下次运行的视频种子策略，不是 API 参数。

## 🔄 恢复、更新与排错

生成 POST 不会自动重试。视频或历史异步图片任务请保留 **Wylon 任务**面板或错误中的已受理任务 ID，然后在 ComfyUI 使用 **Wylon 获取已有图片任务结果** 或 **Wylon 获取已有视频任务结果** 查询同一个任务。获取操作使用 GET，不创建、重启或取消云端任务。Generate 失败后不能向下游传递任务 ID，须手工复制面板/错误中的 ID。普通获取示例属于插件，不在本五套配对包内。再次运行 Generate 节点会发送新的生成请求，可能再次计费。停止本地等待不会取消云端任务。创建超时且没有 ID 时，请先核查 Wylon 历史与用量，再决定是否重新提交。

| 问题 | 检查内容 |
| --- | --- |
| 工作流未出现 | 是否安装在同一服务器、图像/视频目录是否正确、文件是否配对；重新扫描 |
| 加载器在生成前报错 | 是否提供必需首帧；直接在 ComfyUI 运行时是否断开未使用加载器 |
| Ref2VA 校验失败 | 是否至少有图像/视频、模型与角色是否匹配、参考数量及公网 HTTPS URL |
| 视频尺寸与阶段选择器不同 | 服务输出固定为 768p |

**更新：** 备份自行编辑的工作流/预设与生成媒体，只替换上方列出的十个 JSON 文件，保持配对后重新扫描。不要将签名参考 URL 保存在共享工作流或预设中。

**卸载：** 从 ComfyTV 用户工作流目录移除这十个 JSON 文件并重新扫描。ComfyUI-Wylon、ComfyTV、服务器凭据和已有结果分别管理；移除工作流不会取消远程任务。

## 🤝 支持与贡献

问题请提交到 [ComfyUI-Wylon Issues](https://github.com/wylon-cloud/comfyui-wylon/issues)，附工作流包/插件/宿主版本、工作流名称、复现步骤和脱敏错误。敏感报告请按照[安全说明](https://github.com/wylon-cloud/comfyui-wylon/blob/main/SECURITY.zh-CN.md)处理。

开发指引：[贡献指南](https://github.com/wylon-cloud/comfyui-wylon/blob/main/CONTRIBUTING.zh-CN.md) · [贡献检查指引](https://github.com/wylon-cloud/comfyui-wylon/blob/main/docs/VERIFICATION.md)。

上游参考：[ComfyTV v1.13.1 自定义工作流](https://github.com/jtydhr88/ComfyTV/blob/v1.13.1/docs/custom-workflows.zh.md)。

## 📄 许可证

[MIT](LICENSE) · [第三方声明](THIRD_PARTY_NOTICES.md)
