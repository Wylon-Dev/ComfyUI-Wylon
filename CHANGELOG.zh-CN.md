# 变更记录

[English](CHANGELOG.md)

## 0.2.0

- 新增 canonical 版本化配置/模型/任务/结果 API、统一结构错误、RFC 3339 时间戳、有界 keyset 分页及配套前端；旧路由保留并添加废弃响应头；保护凭据两个自有目录层级，拦截符号链接/junction 重定向。

- 增加 Windows 10/11 x64 与 macOS 安装指南、便携版/手动目录说明、兼容的凭据持久化、中文路径及 LF 校验和；打包拒绝 Windows reparse point。
- 首次源码分发包含五个原生 ComfyUI 节点，支持 Wylon 生图、生视频、任务恢复、服务端凭据面板和媒体预览。
- 支持 Qwen Image 2512/2.1、MiniMax H3/Ref2VA、原生 IMAGE/VIDEO/AUDIO 接口、模型角色校验和有界媒体处理。
- 附带五个示例工作流及独立打包的可选 ComfyTV 工作流包；Toonflow-Wylon 独立维护。
- Wylon 原创内容采用 MIT，保留适用的第三方声明。
