# 已克隆开源项目索引

这些仓库使用浅克隆保存于本目录，只用于源码调研。大图库使用 partial clone + sparse checkout，仅下载 Skill、提示词、代码和文档。它们保留各自 `.git`，被上层 `.gitignore` 排除；没有安装依赖、运行脚本或配置第三方凭据。

## 热门聚焦项目

| 本地目录 | 上游仓库 | Star | 固定提交 | 许可证 | 本地体量 |
|---|---|---:|---|---|---:|
| `nature-skills` | `Yuan1z0825/nature-skills` | 28,607 | `b98b53ef5e8f` | Apache-2.0 | 451 KB |
| `guizang-ppt-skill` | `op7418/guizang-ppt-skill` | 21,326 | `82fe5ae129e8` | AGPL-3.0 | 4.2 MB |
| `awesome-gpt-image-2-freestyle` | `freestylefly/awesome-gpt-image-2` | 8,402 | `60b6e1d3ddaf` | MIT | 1.6 MB |
| `awesome-gpt-image-2-youmind` | `YouMind-OpenLab/awesome-gpt-image-2` | 8,208 | `02e16e940c62` | CC BY 4.0 | 2.4 MB |
| `autofigure-edit` | `ResearAI/AutoFigure-Edit` | 3,962 | `a14889f82b9e` | MIT | 20 MB |
| `gpt-image2-skill` | `wuyoscar/GPT-Image2-Skill` | 3,736 | `e48b023f3876` | MIT | 851 KB |

Star 数记录于 2026-07-15。实际研究入口见上层 `POPULAR_PROJECTS.md`。

## 官方与协议参考

| 本地目录 | 上游仓库 | 固定提交 | 用途 |
|---|---|---|---|
| `openai-imagegen-demo` | `openai/openai-imagegen-demo` | `d9304bb70a7a` | OpenAI 官方 GPT Image 2 编辑与 SSE Demo |
| `openai-skills` | `openai/skills` | `49f948faa925` | OpenAI 官方 imagegen Skill 与模型资料 |
| `acedatacloud-skills` | `AceDataCloud/Skills` | `eefa33d15a28` | AceDataCloud 中转协议参考，不代表原生协议 |
| `inference-sh-skills` | `inference-sh/skills` | `fbe0aa4ac8f4` | inference.sh CLI 封装参考，不代表原生协议 |

## 推荐阅读顺序

1. `openai-imagegen-demo`：确认 GPT Image 2 原生协议。
2. `gpt-image2-skill`：理解生成、编辑、遮罩、多参考图和提示词路由。
3. `autofigure-edit`：研究科研图生成、参考图编辑和中转地址配置。
4. `nature-skills/skills/nature-figure`：研究论文图的证据逻辑和质量门槛。
5. 两个 `awesome-gpt-image-2-*`：检索风格与提示词模式。
6. `guizang-ppt-skill/references/image-prompts.md`：提取创作配图的构图和落位规则。

## 操作边界

- 克隆不等于安装或信任。
- 不运行 `awesome-gpt-image-2-freestyle` 的安装脚本；它会替换用户级 Skill 目录。
- 不直接运行 `gpt-image2-skill` 的远程 `uvx` fallback；先固定提交并审查完整 CLI 源码。
- 不直接启动 `autofigure-edit` 服务；它包含外部 API 调用和子进程执行。
- 更新 sparse 仓库时应继续保持现有 sparse-checkout，避免拉取大批预览图。
