# 安全与敏感报告

[English](SECURITY.md) · [README](README.zh-CN.md)

安全漏洞请通过 [GitHub 私密漏洞报告](https://github.com/wylon-cloud/comfyui-wylon/security/advisories/new) 提交，包含受影响的插件/宿主版本、影响、最小复现步骤及脱敏日志。普通缺陷和功能建议使用[仓库 Issues](https://github.com/wylon-cloud/comfyui-wylon/issues)；不要在公开报告中填写凭据或敏感利用细节。

不要附 API Key、完整签名 URL、专有媒体或私有宿主设置。若 Key 泄露，在 Wylon 撤销/轮换，移除会话/本机/环境副本，并核查账户用量。删除 Git 提交或文件不会撤销 Key。

Key 位于服务端，由 ComfyUI 服务进程的用户共享。可选本机保存将明文写入宿主用户目录，POSIX 目录/文件权限为 0700/0600；Windows 需适当 ACL。会话模式避免持久化，不提供用户账户隔离。配置修改的同源检查不是宿主鉴权。只在可信宿主上运行并设置适当访问控制；包含 Key 的备份也需同等保护。

`WYLON_BASE_URL` 会收到已配置凭据，仅可指向可信 API。生成会向 Wylon 发送提示词及提供的参考素材，账户/服务条款与保留策略不由本插件决定。结果素材请求不携带 API Authorization 请求头。连接前，客户端会检查供应商结果 URL 及每次重定向 URL 的原始形式、规范化请求形式和有界重复百分号解码形式，拒绝其中包含当前 API Key 的地址。任务记录省略提示词、输入媒体和签名 URL，但保留 ID/模型/状态等元数据；工作流及宿主输出仍可能包含私人内容。

分享工作流、日志、截图或安装包前请检查私人内容。打包白名单和密钥模式检查无法证明任意文件都不含敏感数据。[使用说明](docs/USAGE.zh-CN.md)说明移除 Key、数据位置及卸载时主动保留/删除文件的方法。
