# GPT Image 2 调研与中转调用工作区

这个目录包含 GPT Image 2 的原生接口调研、开源项目源码，以及一个不依赖第三方 Python 包的 OpenAI 兼容生成脚本。完整调研见 [RESEARCH.md](RESEARCH.md)，克隆项目见 [research-repos/README.md](research-repos/README.md)。

## 1. 配置中转站

复制 `.env.example` 为 `.env`，然后填写：

```dotenv
GPT_IMAGE_API_URL=
GPT_IMAGE_API_KEY=
GPT_IMAGE_MODEL=gpt-image-2
```

`GPT_IMAGE_API_URL` 必须使用中转站提供的完整生成请求地址，例如：

```text
https://your-relay.example.com/v1/images/generations
```

不要只填写域名。OpenAI 原生兼容中转通常使用 `/v1/images/generations`，AceDataCloud 等平台代理使用自己的路径和返回格式，不能混用。

## 2. 调用

在本目录执行：

```text
python generate_image.py "一间有落地窗的安静书房，写实风格"
```

指定输出文件：

```text
python generate_image.py "一间有落地窗的安静书房，写实风格" outputs/study.png
```

脚本发送 JSON 请求：

```json
{
  "model": "gpt-image-2",
  "prompt": "...",
  "size": "1024x1024",
  "quality": "auto",
  "output_format": "png"
}
```

中转站需要接受 OpenAI 兼容的 `POST /images/generations` 请求，并返回类似下面的结构：

```json
{
  "data": [
    {"b64_json": "..."}
  ]
}
```

脚本只处理 `data[0].b64_json`。如果中转站返回图片 URL、异步任务 ID 或其他字段，不能静默兼容，需要按中转站文档明确改写响应解析逻辑。

## 3. 当前调研结论

- `gpt-image-2` 是 OpenAI 官方 SDK 已公开支持的模型名，另有固定快照 `gpt-image-2-2026-04-21`。
- 原生生成接口是 `POST /v1/images/generations`；编辑接口是 `POST /v1/images/edits`。
- 鉴权使用 `Authorization: Bearer <API_KEY>`。
- 原生 GPT Image 模型返回 `data[0].b64_json`，不返回临时图片 URL；某些中转站会改成 `data[0].url`。
- GPT Image 2 支持生成、最多 16 张参考图编辑、遮罩、1-10 张输出、流式部分图和自定义尺寸。
- GPT Image 2 不支持透明背景；`background=transparent` 会报错。
- 官方文档入口：[Image generation guide](https://developers.openai.com/api/docs/guides/image-generation)、[GPT Image 2 model page](https://developers.openai.com/api/docs/models/gpt-image-2)。

## 安全注意事项

- 真实 `.env` 已加入 `.gitignore`，不要把 API Key 提交到 Git。
- 不要把 API Key 放进命令行参数、截图或日志。
- 中转站若要求额外请求头，应在 `generate_image.py` 的 `headers` 中按其文档添加，并保持显式报错。
