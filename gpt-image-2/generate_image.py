"""Generate one image through an OpenAI-compatible image API relay."""

from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT = BASE_DIR / "outputs/generated.png"


def load_dotenv(path: Path) -> None:
    """Load simple KEY=VALUE entries without adding a third-party dependency."""
    if not path.is_file():
        return
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"Invalid .env entry at line {line_number}: expected KEY=VALUE")
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def required_config(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required configuration: {name}. Fill it in .env.")
    return value


def generate_image(prompt: str, output_path: Path) -> None:
    api_url = required_config("GPT_IMAGE_API_URL")
    api_key = required_config("GPT_IMAGE_API_KEY")
    model = os.environ.get("GPT_IMAGE_MODEL", "").strip()
    if not model:
        raise RuntimeError("Missing required configuration: GPT_IMAGE_MODEL.")

    payload = {
        "model": model,
        "prompt": prompt,
        "size": os.environ.get("GPT_IMAGE_SIZE", "").strip(),
        "quality": os.environ.get("GPT_IMAGE_QUALITY", "").strip(),
        "output_format": os.environ.get("GPT_IMAGE_OUTPUT_FORMAT", "").strip(),
    }
    payload = {key: value for key, value in payload.items() if value}
    request = Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=120) as response:
            response_body = response.read()
    except HTTPError as error:
        error_body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Image API returned HTTP {error.code}: {error_body}") from error
    except URLError as error:
        raise RuntimeError(f"Could not reach image API at {api_url}: {error.reason}") from error

    try:
        result = json.loads(response_body.decode("utf-8"))
        encoded_image = result["data"][0]["b64_json"]
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, IndexError, TypeError) as error:
        raise RuntimeError(
            "Image API response did not contain data[0].b64_json; "
            "check relay response compatibility."
        ) from error

    try:
        image_bytes = base64.b64decode(encoded_image, validate=True)
    except (ValueError, TypeError) as error:
        raise RuntimeError("Image API returned invalid base64 image data.") from error

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(image_bytes)
    print(f"Saved image to {output_path}")


def resolve_output_path(raw_path: str | None) -> Path:
    if raw_path is None:
        return DEFAULT_OUTPUT
    output_path = Path(raw_path)
    return output_path if output_path.is_absolute() else BASE_DIR / output_path


def main() -> int:
    load_dotenv(Path(__file__).with_name(".env"))
    if len(sys.argv) < 2:
        raise RuntimeError('Usage: python generate_image.py "your image prompt" [output path]')
    output_path = resolve_output_path(sys.argv[2] if len(sys.argv) >= 3 else None)
    generate_image(sys.argv[1], output_path)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1) from error
