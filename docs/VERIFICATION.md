# Contributor checks / 贡献检查指引

[Contributing](../CONTRIBUTING.md) · [贡献指南](../CONTRIBUTING.zh-CN.md) · [API conventions](API_CONVENTIONS.md) · [API 规范](API_CONVENTIONS.zh-CN.md)

## Prepare a change

Use the Python environment that starts ComfyUI and follow the source build commands in the contributing guide. Keep the native V3 node/media API, stable node IDs, media ports and existing workflow fields compatible. Review image/video model roles, reference limits and task recovery when changing generation behavior.

Check configuration changes with synthetic keys on a trusted development host. Confirm that keys stay out of workflows, responses and generated metadata; exercise session/local configuration and removal without changing the host environment. Use local or mocked provider responses for error and recovery checks. Generation POSTs must never retry automatically.

Before distributing an archive, inspect its contents and extracted folder layout, follow its documentation links and compare its SHA-256 sidecar. Include the license, third-party notices, compiled frontend and required user documents. Exclude credentials, private settings, user data, dependencies, symbolic links and Windows reparse points.

For media or installation changes, check the intended host interpreter, native IMAGE/VIDEO/AUDIO connections, video soundtracks, file cleanup, Unicode/space-containing paths and the appropriate manual or portable directory layout. Consult the [usage guide](USAGE.md) for model, media, credential and host-access requirements.

## 准备修改

使用启动 ComfyUI 的 Python 环境，按照贡献指南中的源码构建命令操作。保持原生 V3 节点/媒体 API、稳定节点 ID、媒体端口及既有工作流字段兼容。修改生成行为时，核对图像/视频模型角色、参考素材限制与任务恢复。

在可信开发宿主上使用合成密钥检查配置修改。确认工作流、响应和生成元数据不包含密钥；检查会话/本机配置及移除操作，不修改宿主环境变量。错误与恢复检查使用本地或模拟供应商响应，生成 POST 始终不得自动重试。

分发归档前，检查内容及解压目录结构、文档链接与 SHA-256 文件。归档须包含许可证、第三方声明、编译前端及必要用户文档，不得包含凭据、私有设置、用户数据、依赖目录、符号链接或 Windows reparse point。

修改媒体或安装流程时，检查目标宿主解释器、原生 IMAGE/VIDEO/AUDIO 连接、视频音轨、文件清理、中文/含空格路径及对应的手动或便携版目录结构。模型、媒体、凭据及宿主访问要求见[使用指南](USAGE.zh-CN.md)。
