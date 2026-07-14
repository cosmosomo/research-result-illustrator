# 已克隆开源项目索引

这些仓库使用 `git clone --depth 1` 克隆于 2026-07-15，只用于源码调研。它们保留各自 `.git` 历史，并被上层 `.gitignore` 排除；没有安装依赖、运行脚本或配置第三方凭据。

| 本地目录 | 上游仓库 | 固定提交 | 许可证 | 用途 | 结论 |
|---|---|---|---|---|---|
| `openai-imagegen-demo` | `openai/openai-imagegen-demo` | `d9304bb70a7a` | MIT | 官方 GPT Image 2 编辑、SSE、Next.js Demo | 直接作为原生接口基准 |
| `openai-skills` | `openai/skills` | `49f948faa925` | 各 Skill 独立 | 官方 imagegen Skill、提示词与模型清单 | 直接借鉴工作流，逐目录核对许可证 |
| `acedatacloud-skills` | `AceDataCloud/Skills` | `eefa33d15a28` | Apache-2.0 | 精确命中 GPT Image 2 的中转站 Skill | 仅用于 AceDataCloud 协议；需要平台 Token |
| `inference-sh-skills` | `inference-sh/skills` | `fbe0aa4ac8f4` | 未发现顶层许可证 | GPT Image 2 的 belt CLI Skill | 参考；需登录平台代理且许可不清晰 |
| `claude-scientific-skills` | `eturkes/claude-scientific-skills` | `2f4e5e44dde9` | MIT | 科研插图、科学写作、幻灯片和专业工具 Skills | 借鉴科研路由；脚本需单独审查 |
| `research-plugins` | `wentorai/research-plugins` | `bf44b3cd617f` | MIT | 图形摘要、论文图表、科学示意图指南 | 适合作为确定性科研制图参考 |
| `krea-skills` | `krea-ai/skills` | `b892dff95f47` | MIT | 创作、海报、编辑、角色连续性和视觉 QA | 借鉴工作流；运行依赖 Krea MCP 与凭据 |

## 推荐阅读顺序

1. `openai-imagegen-demo`：先理解真正的 GPT Image 2 原生编辑和流式事件。
2. `openai-skills/skills/.system/imagegen`：学习提示词结构、生成/编辑判定和输出 QA。
3. `acedatacloud-skills/skills/gpt-image-2`：对照中转站如何改变 URL、表单字段和返回格式。
4. `claude-scientific-skills` 与 `research-plugins`：建立“生成式概念图”和“确定性科研图表”的分流规则。
5. `krea-skills/krea-generate`：提取角色保持、连续编辑、海报文字和视觉验收流程。

## 风险说明

- 克隆不等于安装或信任。第三方 Skills 可能执行网络请求、读取 API Key、安装依赖或调用平台 CLI。
- `inference-sh-skills` 未发现顶层许可证，不应直接复制其内容到发布项目。
- `acedatacloud-skills`、`inference-sh-skills`、`krea-skills` 都依赖第三方服务；其价格、参数与返回格式不是 OpenAI 官方承诺。
- `claude-scientific-skills` 的生成脚本使用 OpenRouter，不是 GPT Image 2 原生实现；适合参考任务分类，不适合直接当本项目调用层。
- 未经进一步源码审查，不运行仓库中的安装脚本、更新脚本或远程命令。
