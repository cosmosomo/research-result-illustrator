# GPT Image 2 中转调用模板

这个目录提供一个不依赖第三方 Python 包的、OpenAI 兼容图像生成调用模板。它不会保存真实密钥，也不会在缺少配置时使用默认地址或伪造数据。

## 1. 配置中转站

复制 `.env.example` 为 `.env`，然后填写：

```dotenv
GPT_IMAGE_API_URL=
GPT_IMAGE_API_KEY=
GPT_IMAGE_MODEL=gpt-image-2
```

`GPT_IMAGE_API_URL` 使用中转站提供的完整请求地址，例如通常是：

```text
https://your-relay.example.com/v1/images/generations
```

不要把 URL 写成只包含域名的地址，除非中转站文档明确要求这样填写。若中转站使用了不同的路径或模型别名，以中转站的接口文档为准。

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

- 图像生成的核心调用方式是 `POST /images/generations`。
- 鉴权使用 `Authorization: Bearer <API_KEY>`。
- `prompt` 用于描述要生成的图像；`size`、`quality`、`output_format` 作为可选参数发送。
- GPT Image 2 的具体可用尺寸、质量档位和模型别名可能由 OpenAI 账户或中转站分别控制，因此没有在代码中硬编码额外参数。
- 官方文档入口：[Image generation guide](https://developers.openai.com/api/docs/guides/image-generation)、[GPT Image 2 model page](https://developers.openai.com/api/docs/models/gpt-image-2)。

## 安全注意事项

- 真实 `.env` 已加入 `.gitignore`，不要把 API Key 提交到 Git。
- 不要把 API Key 放进命令行参数、截图或日志。
- 中转站若要求额外请求头，应在 `generate_image.py` 的 `headers` 中按其文档添加，并保持显式报错。
