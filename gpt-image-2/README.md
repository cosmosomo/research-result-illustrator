# GPT Image 2 科研结果示意图工作区

本目录的唯一使用入口是 [research-result-illustrator](skills/research-result-illustrator/SKILL.md)。它以 `nature-figure` 的 Figure Contract、证据层级、Nature 版式和投稿 QA 为骨架，融合 GPT Image 2 的生成、编辑、遮罩、多参考图和提示词参考。默认流程先完成科研生图；原图回贴、来源记录和像素核验是按需启用的论文级能力。

调研材料仍保留在 [RESEARCH.md](RESEARCH.md)、[POPULAR_PROJECTS.md](POPULAR_PROJECTS.md) 和 [research-repos/README.md](research-repos/README.md)。

## 配置

真实调用 GPT Image 2 时，需要在 `.env` 填写：

```dotenv
GPT_IMAGE_GENERATE_URL=
GPT_IMAGE_EDIT_URL=
GPT_IMAGE_API_KEY=
```

其余必填协议参数已列在 `.env.example`，应按中转站文档确认。OpenAI 原生端点分别是：

```text
https://api.openai.com/v1/images/generations
https://api.openai.com/v1/images/edits
```

中转站必须填写它实际提供的完整端点，不能只填写域名。若编辑字段使用 `image[]` 或结果返回 `data[0].url`，应在 `.env` 显式配置，不能依赖自动猜测。

只有 `generate` 和 `edit` 需要 URL/API Key。数据图合成 `compose` 和来源验证 `verify` 完全离线，不需要任何密钥。

## 默认使用顺序

1. 科研智能体输出数据图和想表达的结论。
2. Skill 建立轻量 Figure Contract 和 GPT Image 提示词。
3. `preflight` 校验配置、提示词和参考图。
4. `generate` 或 `edit` 生成科研示意图。
5. 进行视觉检查并交付。

当论文投稿、归档或用户明确要求保留原始数据像素时，再使用 `compose` 把数据图回贴到预留区域，并用 `verify` 检查来源和像素。普通 `verify` 只报告问题；`verify --strict` 才会因不一致停止交付。

真实调用与拼接示例位于 [ischemia-repair-demo](examples/ischemia-repair-demo/)，包含可重复的合成数据、四子图、构图草案、最终提示词、GPT Image 2 输出和拼接成图。

数据图、数值、坐标轴、误差线、显著性标记和比例尺不能由 GPT Image 输出替代。

## 安全

- `.env` 已被 Git 忽略，不要提交或输出 API Key。
- Skill 不读取系统环境变量，也不使用默认 URL、备用模型或替代数据源。
- 网络调用有显式超时和进度事件，不会静默重试。
- 中转站返回格式与配置不一致时立即失败。
