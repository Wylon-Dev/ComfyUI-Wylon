# Third-party notices / 第三方声明

Original Wylon integration code, documentation and authored workflow examples are licensed under the [MIT License](LICENSE), copyright © 2026 Wylon-Dev. This grant covers material whose rights we hold; third-party material retains its own terms.

Wylon 原创集成代码、文档与自行编写的工作流示例采用 [MIT 许可证](LICENSE)，版权 © 2026 Wylon-Dev。本授权限于我们有权授权的内容；第三方内容保留原有条款。

## ComfyUI host / ComfyUI 宿主

This plugin imports ComfyUI's native Python APIs and frontend interfaces. ComfyUI is installed separately and its implementation is not bundled in this plugin archive. ComfyUI v0.44.0 is GPLv3: [upstream LICENSE](https://github.com/Comfy-Org/ComfyUI/blob/v0.44.0/LICENSE). The MIT grant for original plugin code does not relicense ComfyUI. Where a redistribution forms a GPL-covered combined work, the applicable GPL distribution and corresponding-source requirements continue to apply. That source includes the preferred frontend TypeScript and required build materials. The runtime install ZIP is not the complete development source; the source checkout contains `web_src/`, package metadata, lockfile and build scripts. Development source is available in the [project repository](https://github.com/wylon-cloud/comfyui-wylon). A GPL-covered redistribution must make the applicable corresponding source available to its recipients as required by GPL.

插件导入 ComfyUI 原生 Python API 与前端接口，安装包不包含宿主实现。ComfyUI v0.44.0 使用 GPLv3，参见上述上游许可证。原创插件采用 MIT 不会改变宿主许可；分发构成 GPL 覆盖的组合程序时，仍须遵守适用的 GPL 分发与对应源码要求，包括首选的 TypeScript 源码及必要构建材料。运行时 ZIP 不等于完整开发源码；源码检出目录包含 `web_src/`、包元数据、锁文件及构建脚本。开发源码位于[项目仓库](https://github.com/wylon-cloud/comfyui-wylon)；分发构成 GPL 覆盖的组合程序时，仍须按 GPL 要求向接收者提供适用的完整对应源码。

## Other dependencies and services / 其他依赖与服务

Python/Node dependencies, separately installed ComfyTV or other extensions, and their transitive or binary dependencies retain their own licenses. A dependency name in a manifest is not a grant to relicense that dependency. No host checkout, model weights, dependency tree or FFmpeg binary is bundled. Wylon/API service terms, model rights, generated-content rights and trademarks are not granted by this plugin's MIT license.

Python/Node 依赖、单独安装的 ComfyTV 或其他扩展，以及传递/二进制依赖均保留自身许可；清单列出依赖不代表获得重新许可权。安装包不捆绑宿主源码、模型权重、依赖目录或 FFmpeg 二进制。MIT 授权不代替 Wylon/API 服务条款，也不授予模型、生成内容或商标的权利。
