# GPT Image 2 使用方法调研

调研时间：2026-07-15。结论依据 OpenAI 官方 SDK、官方 Demo、官方 Skills，以及已克隆的社区项目。平台封装参数只代表该平台，不能当作 OpenAI 原生协议。热门项目的 Star、体量、许可和风险分层见 [POPULAR_PROJECTS.md](POPULAR_PROJECTS.md)。

## 核心结论

OpenAI 官方公开的模型名为：

- `gpt-image-2`：滚动版本，适合跟随最新能力。
- `gpt-image-2-2026-04-21`：固定快照，适合需要可复现行为的生产环境。

OpenAI 官方模型清单将 `gpt-image-2` 定位为当前最佳图像生成与编辑质量；`gpt-image-1.5` 是成本更低的图像生成与编辑选项。

## 原生 OpenAI 兼容协议

### 文生图

请求：`POST {BASE_URL}/images/generations`。官方 BASE URL 为 `https://api.openai.com/v1`；中转站应提供它自己的完整地址。

```json
{
  "model": "gpt-image-2",
  "prompt": "一座雨夜里的未来图书馆，电影感广角构图",
  "size": "1536x1024",
  "quality": "high",
  "output_format": "png",
  "n": 1
}
```

请求头：

```text
Authorization: Bearer <API_KEY>
Content-Type: application/json
```

GPT Image 原生响应中的图片位于 `data[0].b64_json`，需要 Base64 解码后写入文件。当前目录的 `generate_image.py` 已实现这条路径。

### 图片编辑与多图合成

请求：`POST {BASE_URL}/images/edits`。官方 SDK 接受 PNG、WebP、JPEG，每张小于 50 MB，最多 16 张输入图。

核心参数：

- `image`：一张或多张输入图。
- `prompt`：描述修改内容，并明确列出必须保持不变的元素。
- `mask`：可选 PNG 遮罩；透明区域表示待编辑区域，尺寸需与第一张图一致。
- `input_fidelity`：`low` 或 `high`，高保真适合人物、产品和标识保持。

官方 Node SDK 示例位于 `research-repos/openai-imagegen-demo` 的完整应用中；该项目还演示了把输入图作为 Data URL 发送给 `/images/edits`。

### 流式生成

设置 `stream: true` 后可接收 SSE。`partial_images` 可设为 0-3；官方 Demo 处理 `image_edit.partial_image` 和 `image_edit.completed` 事件。这适合网页实时预览，不是普通命令行脚本的必要功能。

## 参数边界

| 参数 | GPT Image 2 原生规则 |
|---|---|
| `quality` | `low`、`medium`、`high`、`auto` |
| `n` | 1-10 |
| `output_format` | `png`、`jpeg`、`webp` |
| `size` | 标准尺寸或自定义 `WIDTHxHEIGHT` |
| 自定义尺寸 | 宽高均需被 16 整除，宽高比在 1:3 到 3:1 之间 |
| 最大尺寸 | 最高 3840x2160；超过 2560x1440 属实验范围，还受像素/边长限制 |
| `background` | `opaque` 或 `auto`；不支持 `transparent` |
| Prompt 长度 | 最多 32000 字符 |
| 编辑输入 | 最多 16 张；PNG/WebP/JPEG；每张小于 50 MB |

## 中转站兼容性判断

填入密钥之前，应向中转站确认下面五项：

1. 完整生成 URL 和完整编辑 URL，不能只确认域名。
2. 模型名是 `gpt-image-2`，还是平台自定义别名。
3. 生成返回 `data[].b64_json` 还是 `data[].url`。
4. 编辑使用 JSON Data URL、multipart `image`，还是 multipart `image[]`。
5. 是否支持 `stream`、任意尺寸、`input_fidelity`、遮罩和多图输入。

当前 `generate_image.py` 只接受原生兼容的 `data[0].b64_json`。如果中转站返回 URL，脚本会明确报错，不会悄悄改走其他数据流。

## 三种已验证调用形态

| 来源 | 调用方式 | 返回 | 结论 |
|---|---|---|---|
| OpenAI 原生 | `/v1/images/generations`、`/v1/images/edits` | `b64_json` | 首选协议基准 |
| AceDataCloud Skill | `/openai/images/generations`、`/openai/images/edits` | 图片 URL | 中转平台封装，仅在使用该平台时采用 |
| inference.sh Skill | `belt app run openai/gpt-image-2` | CLI 平台结果 | 需要 belt 登录，不是 OpenAI 兼容 HTTP 接口 |

AceDataCloud 的编辑接口使用 multipart 重复字段 `image[]`；inference.sh 使用 `images` URL 数组以及独立 `width`/`height`。这些字段不能复制进 OpenAI 原生请求。

## 科研与创作工作流建议

科研场景应区分“生成式概念图”和“精确数据图”：

- GPT Image 2 适合图形摘要草图、实验概念插画、封面图、演示背景。
- 统计图、流程图、分子结构、网络图和论文定量图应使用 Matplotlib、RDKit、NetworkX、Mermaid、TikZ 等确定性工具。
- 投稿前核对期刊尺寸，位图至少 300 DPI；不要让生成模型虚构实验数据、标签或比例尺。

创作场景最值得复用的是连续编辑：先确定角色基准图，再通过 `/images/edits` 生成视角、服装、场景和海报变体，并在每次提示词中重复角色身份、比例、材质和必须保持的特征。文字较多的封面或海报需要逐字指定文案并进行人工校对。

## 主要证据位置

- 官方完整 Demo：`research-repos/openai-imagegen-demo/README.md`
- 官方 GPT Image 2 编辑和 SSE：`research-repos/openai-imagegen-demo/app/api/photobooth/route.ts`
- 官方模型常量：`research-repos/openai-imagegen-demo/lib/constants.ts`
- 官方 Image Skill：`research-repos/openai-skills/skills/.system/imagegen/`
- AceDataCloud 中转 Skill：`research-repos/acedatacloud-skills/skills/gpt-image-2/SKILL.md`
- inference.sh Skill：`research-repos/inference-sh-skills/tools/image/gpt-image/SKILL.md`
- 可运行 GPT Image 2 Skill：`research-repos/gpt-image2-skill/skills/gpt-image/`
- 工业提示词 Style Skill：`research-repos/awesome-gpt-image-2-freestyle/agents/skills/gpt-image-2-style-library/`
- 8K+ 提示词语料：`research-repos/awesome-gpt-image-2-youmind/README_zh.md`
- 科研制图 Skill：`research-repos/nature-skills/skills/nature-figure/`
- GPT Image 2 科研图生成/编辑：`research-repos/autofigure-edit/autofigure2.py`
- 创作配图提示词：`research-repos/guizang-ppt-skill/references/image-prompts.md`

## 官方在线来源

- [GPT Image 2 model](https://developers.openai.com/api/docs/models/gpt-image-2)
- [Image generation guide](https://developers.openai.com/api/docs/guides/image-generation)
- [OpenAI Python SDK image model type](https://github.com/openai/openai-python/blob/main/src/openai/types/image_model.py)
- [OpenAI Node SDK generation/edit example](https://github.com/openai/openai-node/blob/master/examples/picture.ts)
- [OpenAI ImageGen Demo](https://github.com/openai/openai-imagegen-demo)
