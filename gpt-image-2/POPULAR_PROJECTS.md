# GPT Image 热门聚焦项目调研

统计时间：2026-07-15。Star 会持续变化，表中数值只用于说明本次筛选依据。

## 筛选标准

- 排除大型聊天前端、通用 Agent 平台、模型网关和封闭插件生态。
- 仓库必须聚焦 GPT Image、提示词、科研制图或创作配图。
- 优先 1,000+ Star；官方源码不受 Star 门槛限制。
- 能通过 partial clone 和 sparse checkout 跳过预览图、大模型和发布包。
- 必须能在源码中区分真实 API 调用、Skill 工作流和纯提示词语料。

## 已克隆热门项目

| 项目 | Star | 本地体量 | 类型 | 与 GPT Image 2 的关系 | 结论 |
|---|---:|---:|---|---|---|
| `Yuan1z0825/nature-skills` | 28,607 | 451 KB | 科研制图 Skill | `nature-figure` 明确提供 GPT Image 2/OpenRouter 示意图路由 | 科研工作流首选参考 |
| `op7418/guizang-ppt-skill` | 21,326 | 4.2 MB | 创作/PPT Skill | 提供信息图、流程图、UI、纪实图等配图提示词 | 创作构图参考，不是 API 实现 |
| `freestylefly/awesome-gpt-image-2` | 8,402 | 1.6 MB | Style Skill/模板库 | GPT Image 2 工业模板与分类 Skill | 提示词工程首选参考 |
| `YouMind-OpenLab/awesome-gpt-image-2` | 8,208 | 2.4 MB | 提示词语料库 | 大规模 GPT Image 2 案例和中文提示词 | 适合检索案例，不是调用层 |
| `ResearAI/AutoFigure-Edit` | 3,962 | 20 MB | 科研图生成与编辑 | 真实调用 `client.images.generate/edit`，默认支持 `gpt-image-2` | 最值得研究的科研实现 |
| `wuyoscar/GPT-Image2-Skill` | 3,736 | 851 KB | Skill/CLI | 生成、编辑、遮罩、多参考图，默认 `gpt-image-2` | 最完整的聚焦 Skill 参考 |

以上六个仓库的上游总大小约 860 MB，主要来自预览图。本地使用 partial clone/sparse checkout 后约 29 MB；连同 OpenAI 官方和中转协议参考，整个 `research-repos` 约 41 MB。

## 实现价值

### 真实 API 实现

- `AutoFigure-Edit`：可在 OpenAI 生成和编辑之间按是否存在参考图自动切换，显式设置 `quality="high"`、`output_format="png"`，并给外部 HTTP 调用设置 120-300 秒超时。
- `GPT-Image2-Skill`：提供 generate/edit/inpaint/multi-reference 路由、尺寸和质量策略、提示词分类、输出路径约定。
- `openai-imagegen-demo`：虽然只有 58 Star，但它是 OpenAI 官方 GPT Image 2 Demo，仍是协议真实性最高的基准。

### 提示词与质量流程

- `awesome-gpt-image-2-freestyle`：按产品、海报、UI、信息图、角色和历史场景分类，适合把自然语言需求结构化。
- `awesome-gpt-image-2-youmind`：样本量大，适合检索相似案例，但不能把案例数量当作 API 质量保证。
- `nature-skills`：明确区分生成式科研示意图与 Python/R 定量图，强调结论、证据链、导出和审稿风险。
- `guizang-ppt-skill`：强调先定图片槽位和比例，再生成素材；提示词避免把页眉、页脚、标题栏生成进图片。

## 安全与许可结论

| 项目 | 许可证 | 风险 | 使用建议 |
|---|---|---|---|
| `nature-skills` | Apache-2.0 | API 脚本会访问 OpenRouter | 借鉴 Skill；真实调用前单独审查配置 |
| `guizang-ppt-skill` | AGPL-3.0 | 强 Copyleft | 可阅读和内部参考；复制代码前评估许可影响 |
| `awesome-gpt-image-2-freestyle` | MIT | 安装脚本会删除并替换目标 Skill 目录 | 不执行安装脚本，只读模板和 Skill |
| `awesome-gpt-image-2-youmind` | CC BY 4.0 | 主要是内容语料 | 使用内容需保留署名 |
| `AutoFigure-Edit` | MIT | 多个外部 API、Web 服务和子进程执行 | 参考实现；部署前需完整威胁建模 |
| `GPT-Image2-Skill` | MIT | launcher 可通过 `uvx` 临时拉取远程仓库并执行 | 不直接运行 fallback；应固定版本并审查 CLI 源码 |

## 明确排除

没有克隆或纳入主样本：Open WebUI、LobeChat、Cherry Studio、Dify、Eliza、LiteLLM、Excalidraw。这些项目要么体量过大，要么 GPT Image 只是庞大生态中的一个功能，不符合本次“轻量、聚焦、可独立研究”的要求。

另外没有完整下载几个热门提示词库的预览图和图库资产。它们仍是标准 Git clone，只是通过 sparse checkout 保留了本次调研需要的源码和文本。
