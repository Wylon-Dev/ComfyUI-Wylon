# ComfyUI-Wylon 使用说明

[English](USAGE.md) · [README](../README.zh-CN.md)

## 平台与解释器选择

Windows 10/11 x64 与 macOS 的安装方式见 [README 平台表](../README.zh-CN.md#-安装)。普通安装不需要 Node.js/npm、Bash 或 GCC。

| 安装方式 | 安装插件依赖使用的解释器 | 命令所在目录 |
| --- | --- | --- |
| Windows 手动/venv | 实际启动 ComfyUI 的 Python，例如 `.\.venv\Scripts\python.exe` | ComfyUI 根目录 |
| 官方 Windows 便携版 | `.\python_embeded\python.exe` | 便携发行版根目录，内含 `ComfyUI` 目录 |
| macOS / Linux 源码安装 | ComfyUI 已启用的 Python 环境 | ComfyUI 根目录 |

根据目录结构执行 [README 安装命令](../README.zh-CN.md#-安装)。将依赖装入其他系统 Python 不会使 ComfyUI 自动获得这些依赖。

## 密钥与宿主访问

打开 **Wylon → Wylon tasks / Wylon 任务**或节点底部的 **Wylon 配置 / API Key**，应用本次服务进程的 Key，可选“记住本机（保存到 ComfyUI 用户目录的私有配置）”。选择保存也会设置会话 Key。连接验证查询模型列表，不生成媒体，也不证明账户可调用所有生成模型。

优先级为会话、本机保存、`WYLON_API_KEY`。会话指 ComfyUI 进程生命周期，不是浏览器标签页或独立登录。能操作该宿主的用户可使用已配置账户并修改配置；同源检查不提供用户鉴权或账户隔离。请使用可信宿主及适当的网络/访问控制。

本机凭据以明文存于 `<ComfyUI 用户目录>/wylon/private/credentials.json`，通常为 `ComfyUI/user/wylon/private/credentials.json`。POSIX 目录/文件权限为 0700/0600。Windows 应检查服务账户目录 ACL；仅调用 POSIX 权限接口不代表实现等同的 Windows 访问隔离。该目录的备份也包含密钥。插件不把 Key 写入工作流、节点输入或生成元数据。

在面板清除会话 Key 和/或删除本机 Key。仅删除本机保存可能仍有会话 Key 生效；清除二者也不会移除环境变量。移除环境设置并重启才能去掉该来源。重启清除会话内存，保留本机凭据。

环境变量方案：macOS/Linux 在 ComfyUI 根目录使用宿主 Python：

```sh
export WYLON_API_KEY='你的 Key'
python main.py
```

Windows 手动/venv 安装，在 ComfyUI 根目录使用 PowerShell（环境名不同时请替换 `.venv`）：

```powershell
$env:WYLON_API_KEY = '你的 Key'
.\.venv\Scripts\python.exe main.py
```

官方 Windows 便携版，在便携发行版根目录使用 PowerShell：

```powershell
$env:WYLON_API_KEY = '你的 Key'
.\run_nvidia_gpu.bat
```

请使用平时的便携版启动脚本；上例为 NVIDIA 启动器。环境变量由该 PowerShell 会话启动的进程继承。从当前会话移除可运行 `Remove-Item Env:WYLON_API_KEY`，然后重启 ComfyUI。

以上均为占位符。上述示例可用于运行时安装包；插件不会自动加载 `.env`。源码检出目录另含变量参考文件 `.env.example`，运行时安装包不包含该文件。默认 API 根地址为 `https://api.wylon.cn/v1`。`WYLON_BASE_URL` 可指定可信测试环境，该端点会收到 Key，请勿指向不可信端点。须用 HTTPS，仅本地测试允许回环 HTTP。变更环境变量后重启。

## 模型与媒体

- **Wylon Generate Image**（`WylonGenerateImage`）：`Qwen/Qwen-Image-2512` 或 `Qwen/Qwen-Image-2.1`，输出 `IMAGE`、`task_id`、`file_path`。异步可恢复；同步没有任务 ID/恢复能力，并忽略节点 seed 控件。
- **Wylon H3 Video**（`WylonH3Video`）默认 `MiniMaxAI/MiniMax-H3`；**Wylon Ref2VA Video**（`WylonRef2VAVideo`）默认 `MiniMaxAI/MiniMax-H3-Ref2VA`。二者模型选项相同，输出 `VIDEO`、`task_id`、`file_path`。
- **Wylon Resume Image Task**（`WylonResumeImageTask`）和 **Wylon Resume Video Task**（`WylonResumeVideoTask`）：查询/下载对应媒体类型的已有任务，不创建生成。

所选模型决定输入角色。H3 支持文字及可选 `first_frame`/`last_frame` 原生 IMAGE，各一张。Ref2VA 拒绝首尾帧角色，且至少需要参考图片或视频。连接 `image_0` / `audio_0` 后原生 IMAGE/AUDIO 端口按需增加；`video_urls` 每行填一个公网 HTTPS URL。参考音频须同时有图片或视频。冲突组合会在提交前给出双语报错，模型不会自动切换。

视频输出是下载 MP4 支撑的原生 VIDEO，保留音轨，不提前解码全部帧。可接原生 Save Video。使用 VideoHelperSuite 时，先接原生 **Get Video Components**，将 IMAGE、AUDIO、fps 接 VHS Video Combine。无音轨则无音频分量。

当前限制：

- 视频生成：整数 5–15 秒，768p。比例为 21:9、16:9、4:3、1:1、3:4、9:16。`server_default` 省略比例；`adaptive` 也省略比例，但仅允许 H3 且有首/尾帧。
- Ref2VA：最多 9 张图片、3 段视频、3 段音频。原生图片批次中的每张图片均计数。
- 参考图片：每边 300–5760 像素，宽高比 0.4–2.5，Wylon 文档规定每张最大 30 MB，插件另限制编码数据不超过 30 MiB。原生张量编码为 PNG，首尾帧端口各只接收一张。
- 参考音频：每段 2–15 秒，Wylon 文档规定每段最大 15 MB，插件另限制编码 WAV 不超过 15 MiB；总时长不超过 15 秒。原生 AUDIO 编码为 PCM WAV。
- 输出下载：插件强制限制每张图片不超过 64 MiB、每个视频不超过 1 GiB，与参考输入限制分别计算。重试或恢复同一个超大结果不会绕过这些上限。
- 参考视频：API 限制每段 2–15 秒、最大 50 MB，总时长 15 秒。远程格式、帧率、时长和大小由 Wylon 校验；插件只校验 URL，不核实所有远程媒体属性。

参考视频须为 Wylon 可访问的公网 HTTPS，不含内嵌凭据或片段。没有自动上传服务。本地 MP4、Base64 视频、localhost、局域网/私有地址及 Wylon 获取前已过期的 URL 均不可用。可选 ComfyTV 工作流提供的 URL 同样受限。

生图尺寸按模型选择，`server_default` 省略尺寸。Qwen-Image-2512 提供 1328×1328、1664×928、928×1664、1104×1472、1584×1056。Qwen-Image-2.1 提供 1536×2752、1696×2528、1792×2400、2048×2048、2400×1792、2528×1696、2752×1536。V1 每次生成一张。Seed=-1 省略，生图 seed 仅异步使用。负向提示词和允许的可选字段按接口传递；服务接受不代表每个模型都有对应视觉效果或确定性。

`extra_parameters` 须为小于 64 KiB 的 JSON 对象。只接受白名单 API 字段，不能覆盖鉴权、模型/路由和核心请求字段。图片兼容字段 `n`、`stream`、`partial_images`、`output_format` 分别限于 1、false、0、png。添加 JSON 字段不会开启 API 未支持的能力。使用高级字段时核对当前 Wylon 契约。

## 恢复与故障排查

生成 POST 不自动重试。只读状态查询有有限重试与退避，本地轮询最长 15 分钟。异步 ID 返回后，先在 `<ComfyUI 用户目录>/wylon/` 记录，再轮询。记录仅含 ID、媒体类型、模型、状态和时间，不含提示词、输入、凭据或签名素材 URL。

等待中断、超时或下载失败后，从面板或报错复制 ID 到对应 Resume 节点。恢复需要正确账户及尚未过期的结果，可能再下载一份本地文件。停止 ComfyUI/本地等待不会取消云端工作；未提供云端取消操作。创建超时且没有 ID 时，先核查 Wylon 控制台/历史及用量，再明确决定是否重提，避免重复付费。

- **节点/菜单不显示：**检查服务端导入报错、目录嵌套、安装依赖的解释器和宿主基线。安装/更新后重启服务并刷新页面。
- **Key 缺失/无效：**检查面板实际来源；会话/本机 Key 优先于环境变量。连接成功仅验证模型列表请求。
- **无法保存/删除 Key：**确认服务账户可访问实际用户目录，不要通过向其他用户放宽权限来绕过。
- **HTTP 429：**检查账户频率/并发限制与已有任务，等待对应限制解除后再决定是否提交。
- **模型/参考报错：**首尾帧明确选 H3，参考媒体明确选 Ref2VA。检查数量、音频时长和公网视频 URL，不要把本地路径改名冒充 URL。
- **任务失败/过期：**查看 Wylon 返回状态，及时下载成功结果；查询无法恢复已过期素材。手动重新生成是新的可能付费任务。
- **编解码/下载错误：**检查磁盘空间、网络及宿主环境的 PyAV。保留 ID；临时故障可在结果仍可用时，使用正确账户通过恢复节点重试获取。若报错指出超过输出下载上限（每张图片 64 MiB / 每个视频 1 GiB），重试或恢复不会绕过限制。查询无法恢复已过期结果；手动重新生成是新的可能付费任务。
- **代理后配置被拦截：**配置修改须为浏览器同源请求。确保代理保留一致的浏览器/服务端来源，不要关闭检查。

结果下载到 `<ComfyUI 输出目录>/wylon/`，通常为 `ComfyUI/output/wylon/`。面板展示最近本地结果。素材下载不发送 API Key。原生 Save Image/Save Video 可能另外保存到用户指定位置。

## 更新与卸载

变更前记录插件/宿主版本，停止 ComfyUI（Windows 上关闭其终端/服务进程，便于替换已加载的文件），把个人工作流、自定义内容和旧插件目录备份到 `custom_nodes/` 外。按本地策略备份宿主用户/输出数据；用户目录备份包含明文 Key。

安装包更新时，仅替换 `custom_nodes/ComfyUI-Wylon` 为新包目录，检查变更后恢复有意保留的自定义内容，再使用宿主解释器执行 README 的依赖安装命令。重启并检查面板后再运行付费生成。不要把旧副本留在 `custom_nodes/` 中供重复加载。源码检出应在保留本地修改后按常规版本控制流程更新。

卸载时停止 ComfyUI，仅移除 `custom_nodes/ComfyUI-Wylon` 后重启。宿主用户数据、工作流和输出仍会保留。移除凭据时，可在卸载前清除面板会话/本机 Key 并移除环境设置；或停止宿主后明确删除实际用户目录中的 `wylon/private/credentials.json`。任务记录和下载媒体将保留，除非你备份后主动删除。不要删除整个 ComfyUI 用户/输出目录。移除插件或记录不会取消或删除远程 Wylon 任务。

## API 参考

[图片生成指南](https://portal.wylon.cn/zh/docs-generation-images.html) · [视频生成指南](https://portal.wylon.cn/zh/docs-generation-videos.html)

随包能力文件说明已实现契约。Wylon 可调整模型/账户能力，服务端行为请核查其当前文档。

[自有 HTTP API 规范与注册错误码](API_CONVENTIONS.zh-CN.md)。
