# 贡献指南

[English](CONTRIBUTING.md) · [README](README.zh-CN.md)

缺陷及功能建议使用 [Issues](https://github.com/wylon-cloud/comfyui-wylon/issues)，安全问题使用[私密漏洞报告](https://github.com/wylon-cloud/comfyui-wylon/security/advisories/new)。请附插件/宿主版本、系统、复现步骤、预期/实际结果及脱敏日志，不要公开 API Key、私有设置、签名素材 URL 或专有媒体。

## 从公开源码构建

公开源码包含运行时、TypeScript 源码及构建材料。运行时 ZIP 包含编译前端及用户文档。在源码根目录使用 Node.js 22.23.x、npm 和 Python 3.10+：

```sh
npm ci --ignore-scripts
npm run typecheck
npm run build
npm run package
```

打包时可用 `PYTHON` 指定解释器；默认 Windows 使用 `python`，macOS/Linux 使用 `python3`。也可直接用选定解释器执行 `python scripts/package.py`。脚本在源码根目录旁生成 `ComfyUI-Wylon-0.3.2.zip` 与 `Wylon-ComfyTV-Workflows-0.3.2.zip`，分别附 SHA-256 文件；目标选项见 `--help`。校验和用于检测文件变化。

Windows 10/11 x64 手动/venv、官方便携版及 macOS 安装方式见 [README 安装说明](README.zh-CN.md#-安装)。准备修改时参阅[贡献检查指引](docs/VERIFICATION.md)。普通插件安装无需 Node.js、Bash 或 GCC。

## 修改与版本

保留稳定节点 ID、原生 IMAGE/VIDEO/AUDIO 端口、上游 SDK 字段/状态、双语操作文本与仅服务端持有的凭据。生成 POST 不得自动重试。保持修改聚焦，在变更说明中清楚描述行为变更及安装要求，参见 [API 规范](docs/API_CONVENTIONS.zh-CN.md)。

遵循 Semantic Versioning 2.0.0：正式 tag 为 `vX.Y.Z`；预发布为 `vX.Y.Z-alpha.n`、`vX.Y.Z-beta.n` 或 `vX.Y.Z-rc.n`；发布分支为 `vX.Y`。兼容新增递增 minor，修复递增 patch；不兼容的公开 API 修改须递增 major。对外废弃接口至少保留六个月及两个 minor 版本，随后才能在新 major 中移除。

运行时包不含开发工具及可选 ComfyTV 包；发布归档不得包含用户数据、依赖目录、凭据、符号链接或 Windows reparse point。检查解压后的文档相对链接；插件文档对独立工作流包使用 canonical 仓库链接。原创贡献采用 [MIT](LICENSE)，保留[第三方声明](THIRD_PARTY_NOTICES.md)。
