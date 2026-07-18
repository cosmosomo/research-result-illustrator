"""Generate GPT Image 2 schematics and compose immutable research charts."""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import mimetypes
import sys
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from contextlib import ExitStack
from io import BytesIO
from pathlib import Path
from typing import Callable, TypeVar
from urllib.parse import urlparse

import httpx
from PIL import Image


T = TypeVar("T")
SUPPORTED_INPUT_FORMATS = {".png", ".jpg", ".jpeg", ".webp"}
OUTPUT_SUFFIXES = {"png": {".png"}, "jpeg": {".jpg", ".jpeg"}, "webp": {".webp"}}
COMMON_CONFIG_KEYS = (
    "GPT_IMAGE_API_KEY",
    "GPT_IMAGE_MODEL",
    "GPT_IMAGE_TIMEOUT_SECONDS",
    "GPT_IMAGE_SIZE",
    "GPT_IMAGE_QUALITY",
    "GPT_IMAGE_OUTPUT_FORMAT",
    "GPT_IMAGE_RESPONSE_MODE",
)


class UserError(RuntimeError):
    """A reproducible configuration or input error."""


def emit_event(event: str, **context: object) -> None:
    payload = {"event": event, "time": time.strftime("%Y-%m-%dT%H:%M:%S%z"), **context}
    print(json.dumps(payload, ensure_ascii=False), file=sys.stderr, flush=True)


def resolved_path(raw_path: str) -> Path:
    return Path(raw_path).expanduser().resolve()


def read_config(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise UserError(f"Configuration file does not exist: {path}")
    config: dict[str, str] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise UserError(f"Invalid configuration at {path}:{line_number}; expected KEY=VALUE")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key:
            raise UserError(f"Empty configuration key at {path}:{line_number}")
        if key in config:
            raise UserError(f"Duplicate configuration key {key} at {path}:{line_number}")
        config[key] = value
    return config


def require_config(config: dict[str, str], keys: tuple[str, ...]) -> None:
    missing = [key for key in keys if not config.get(key, "").strip()]
    if missing:
        raise UserError(f"Missing required configuration values: {', '.join(missing)}")


def validate_url(name: str, value: str) -> None:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise UserError(f"{name} must be a complete HTTP(S) URL")
    if parsed.username or parsed.password:
        raise UserError(f"{name} must not contain credentials")


def safe_url(value: str) -> str:
    parsed = urlparse(value)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


def validate_common_config(config: dict[str, str]) -> float:
    require_config(config, COMMON_CONFIG_KEYS)
    try:
        timeout_seconds = float(config["GPT_IMAGE_TIMEOUT_SECONDS"])
    except ValueError as error:
        raise UserError("GPT_IMAGE_TIMEOUT_SECONDS must be numeric") from error
    if not 1 <= timeout_seconds <= 600:
        raise UserError("GPT_IMAGE_TIMEOUT_SECONDS must be between 1 and 600")
    if config["GPT_IMAGE_QUALITY"] not in {"low", "medium", "high", "auto"}:
        raise UserError("GPT_IMAGE_QUALITY must be low, medium, high, or auto")
    if config["GPT_IMAGE_OUTPUT_FORMAT"] not in OUTPUT_SUFFIXES:
        raise UserError("GPT_IMAGE_OUTPUT_FORMAT must be png, jpeg, or webp")
    if config["GPT_IMAGE_RESPONSE_MODE"] not in {"b64_json", "url"}:
        raise UserError("GPT_IMAGE_RESPONSE_MODE must be b64_json or url")
    return timeout_seconds


def read_prompt(path: Path) -> str:
    if not path.is_file():
        raise UserError(f"Prompt file does not exist: {path}")
    prompt = path.read_text(encoding="utf-8").strip()
    if not prompt:
        raise UserError(f"Prompt file is empty: {path}")
    if len(prompt) > 32_000:
        raise UserError("Prompt exceeds the 32000-character GPT Image limit")
    return prompt


def validate_reference(path: Path) -> None:
    if not path.is_file():
        raise UserError(f"Reference image does not exist: {path}")
    if path.suffix.lower() not in SUPPORTED_INPUT_FORMATS:
        raise UserError(f"Unsupported reference format for {path}; use PNG, JPEG, or WebP")
    if path.stat().st_size >= 50 * 1024 * 1024:
        raise UserError(f"Reference image must be smaller than 50 MB: {path}")
    try:
        with Image.open(path) as image:
            image.verify()
    except Exception as error:
        raise UserError(f"Reference image is invalid: {path}: {error}") from error


def validate_mask(mask_path: Path, first_reference: Path) -> None:
    if mask_path.suffix.lower() != ".png" or not mask_path.is_file():
        raise UserError("Mask must be an existing PNG file")
    if mask_path.stat().st_size >= 4 * 1024 * 1024:
        raise UserError("Mask must be smaller than 4 MB")
    try:
        with Image.open(first_reference) as reference, Image.open(mask_path) as mask:
            if reference.size != mask.size:
                raise UserError("Mask dimensions must match the first reference image")
            if "A" not in mask.getbands():
                raise UserError("Mask must contain an alpha channel")
            if mask.getchannel("A").getextrema()[0] != 0:
                raise UserError("Mask must contain fully transparent pixels to identify the edit region")
    except UserError:
        raise
    except Exception as error:
        raise UserError(f"Mask validation failed: {error}") from error


def validate_output_path(output_path: Path, output_format: str) -> None:
    if output_path.suffix.lower() not in OUTPUT_SUFFIXES[output_format]:
        allowed = ", ".join(sorted(OUTPUT_SUFFIXES[output_format]))
        raise UserError(f"Output path extension must match {output_format}: {allowed}")
    output_path.parent.mkdir(parents=True, exist_ok=True)


def run_with_heartbeat(label: str, operation: Callable[[], T]) -> T:
    emit_event("external_call_started", operation=label)
    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(operation)
        while True:
            try:
                result = future.result(timeout=10)
                emit_event(
                    "external_call_completed",
                    operation=label,
                    elapsed_seconds=round(time.monotonic() - started, 1),
                )
                return result
            except FutureTimeoutError:
                emit_event(
                    "external_call_progress",
                    operation=label,
                    elapsed_seconds=round(time.monotonic() - started, 1),
                )
            except Exception as error:
                emit_event(
                    "external_call_failed",
                    operation=label,
                    elapsed_seconds=round(time.monotonic() - started, 1),
                    error_type=type(error).__name__,
                    error=str(error),
                )
                raise


def checked_response(response: httpx.Response, url: str) -> dict[str, object]:
    diagnostic_url = safe_url(url)
    if not response.is_success:
        raise UserError(
            f"Image API returned HTTP {response.status_code} from {diagnostic_url}: {response.text[:2000]}"
        )
    try:
        payload = response.json()
    except json.JSONDecodeError as error:
        raise UserError(f"Image API returned invalid JSON from {diagnostic_url}") from error
    if not isinstance(payload, dict):
        raise UserError("Image API response must be a JSON object")
    return payload


def extract_image_bytes(
    payload: dict[str, object], response_mode: str, timeout_seconds: float
) -> bytes:
    data = payload.get("data")
    if not isinstance(data, list) or not data or not isinstance(data[0], dict):
        raise UserError("Image API response does not contain data[0]")
    item = data[0]
    if response_mode == "b64_json":
        encoded = item.get("b64_json")
        if not isinstance(encoded, str) or not encoded:
            raise UserError("Image API response does not contain data[0].b64_json")
        try:
            return base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error) as error:
            raise UserError("Image API returned invalid base64 image data") from error

    image_url = item.get("url")
    if not isinstance(image_url, str) or not image_url:
        raise UserError("Image API response does not contain data[0].url")
    validate_url("response image URL", image_url)

    def download() -> httpx.Response:
        with httpx.Client(timeout=httpx.Timeout(timeout_seconds), follow_redirects=True) as client:
            return client.get(image_url)

    response = run_with_heartbeat("download_image", download)
    if not response.is_success:
        raise UserError(
            f"Image download returned HTTP {response.status_code} from {safe_url(image_url)}"
        )
    return response.content


def detect_image_format(image_bytes: bytes) -> str:
    try:
        with Image.open(BytesIO(image_bytes)) as image:
            detected = (image.format or "").lower()
            image.verify()
    except Exception as error:
        raise UserError(f"API response is not a valid image: {error}") from error
    return "jpeg" if detected == "jpg" else detected


def atomic_write_bytes(path: Path, content: bytes) -> None:
    temporary_path = path.with_name(f".{path.name}.tmp")
    temporary_path.write_bytes(content)
    temporary_path.replace(path)


def save_api_image(image_bytes: bytes, output_path: Path, expected_format: str) -> None:
    detected_format = detect_image_format(image_bytes)
    if detected_format != expected_format:
        raise UserError(
            f"Image API returned {detected_format or 'unknown'} but configuration requires {expected_format}"
        )
    atomic_write_bytes(output_path, image_bytes)
    emit_event("image_saved", path=str(output_path), bytes=len(image_bytes))


def preflight_network(
    mode: str,
    config_path: Path,
    prompt_path: Path,
    reference_paths: list[Path],
    mask_path: Path | None,
    output_path: Path | None,
) -> tuple[dict[str, str], str, float]:
    config = read_config(config_path)
    prompt = read_prompt(prompt_path)

    if mode == "generate":
        require_config(config, COMMON_CONFIG_KEYS + ("GPT_IMAGE_GENERATE_URL",))
        validate_url("GPT_IMAGE_GENERATE_URL", config["GPT_IMAGE_GENERATE_URL"])
        if reference_paths or mask_path:
            raise UserError("Generate mode does not accept references or a mask")
    elif mode == "edit":
        require_config(
            config,
            COMMON_CONFIG_KEYS
            + ("GPT_IMAGE_EDIT_URL", "GPT_IMAGE_EDIT_IMAGE_FIELD", "GPT_IMAGE_INPUT_FIDELITY"),
        )
        validate_url("GPT_IMAGE_EDIT_URL", config["GPT_IMAGE_EDIT_URL"])
        if config["GPT_IMAGE_EDIT_IMAGE_FIELD"] not in {"image", "image[]"}:
            raise UserError("GPT_IMAGE_EDIT_IMAGE_FIELD must be image or image[]")
        if config["GPT_IMAGE_INPUT_FIDELITY"] not in {"low", "high"}:
            raise UserError("GPT_IMAGE_INPUT_FIDELITY must be low or high")
        if not reference_paths:
            raise UserError("Edit mode requires at least one reference image")
        if len(reference_paths) > 16:
            raise UserError("Edit mode supports at most 16 reference images")
        for reference_path in reference_paths:
            validate_reference(reference_path)
        if mask_path:
            validate_mask(mask_path, reference_paths[0])
    else:
        raise UserError(f"Unknown network mode: {mode}")

    timeout_seconds = validate_common_config(config)
    if output_path:
        validate_output_path(output_path, config["GPT_IMAGE_OUTPUT_FORMAT"])
    emit_event(
        "preflight_passed",
        mode=mode,
        config=str(config_path),
        prompt=str(prompt_path),
        references=[str(path) for path in reference_paths],
        mask=str(mask_path) if mask_path else None,
    )
    return config, prompt, timeout_seconds


def generate_image(config: dict[str, str], prompt: str, timeout_seconds: float) -> bytes:
    url = config["GPT_IMAGE_GENERATE_URL"]
    request_body = {
        "model": config["GPT_IMAGE_MODEL"],
        "prompt": prompt,
        "size": config["GPT_IMAGE_SIZE"],
        "quality": config["GPT_IMAGE_QUALITY"],
        "output_format": config["GPT_IMAGE_OUTPUT_FORMAT"],
        "n": 1,
    }

    def request() -> httpx.Response:
        with httpx.Client(timeout=httpx.Timeout(timeout_seconds)) as client:
            return client.post(
                url,
                headers={"Authorization": f"Bearer {config['GPT_IMAGE_API_KEY']}"},
                json=request_body,
            )

    payload = checked_response(run_with_heartbeat("generate_image", request), url)
    return extract_image_bytes(payload, config["GPT_IMAGE_RESPONSE_MODE"], timeout_seconds)


def edit_image(
    config: dict[str, str],
    prompt: str,
    timeout_seconds: float,
    reference_paths: list[Path],
    mask_path: Path | None,
) -> bytes:
    url = config["GPT_IMAGE_EDIT_URL"]

    def request() -> httpx.Response:
        with ExitStack() as stack:
            files: list[tuple[str, tuple[str, object, str]]] = []
            field_name = config["GPT_IMAGE_EDIT_IMAGE_FIELD"]
            for reference_path in reference_paths:
                handle = stack.enter_context(reference_path.open("rb"))
                mime_type = mimetypes.guess_type(reference_path.name)[0] or "application/octet-stream"
                files.append((field_name, (reference_path.name, handle, mime_type)))
            if mask_path:
                mask_handle = stack.enter_context(mask_path.open("rb"))
                files.append(("mask", (mask_path.name, mask_handle, "image/png")))
            form_data = {
                "model": config["GPT_IMAGE_MODEL"],
                "prompt": prompt,
                "size": config["GPT_IMAGE_SIZE"],
                "quality": config["GPT_IMAGE_QUALITY"],
                "output_format": config["GPT_IMAGE_OUTPUT_FORMAT"],
                "input_fidelity": config["GPT_IMAGE_INPUT_FIDELITY"],
                "n": "1",
            }
            with httpx.Client(timeout=httpx.Timeout(timeout_seconds)) as client:
                return client.post(
                    url,
                    headers={"Authorization": f"Bearer {config['GPT_IMAGE_API_KEY']}"},
                    data=form_data,
                    files=files,
                )

    payload = checked_response(run_with_heartbeat("edit_image", request), url)
    return extract_image_bytes(payload, config["GPT_IMAGE_RESPONSE_MODE"], timeout_seconds)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def pixel_hash(image: Image.Image) -> str:
    normalized = image.convert("RGBA")
    digest = hashlib.sha256()
    digest.update(f"{normalized.width}x{normalized.height}:RGBA".encode("ascii"))
    digest.update(normalized.tobytes())
    return digest.hexdigest()


def parse_chart_spec(spec: str) -> tuple[Path, tuple[int, int, int, int]]:
    try:
        raw_path, raw_box = spec.rsplit("@", 1)
        x, y, width, height = (int(part) for part in raw_box.split(","))
    except (ValueError, TypeError) as error:
        raise UserError(f"Invalid chart specification {spec!r}; expected PATH@X,Y,W,H") from error
    if min(x, y) < 0 or width <= 0 or height <= 0:
        raise UserError(f"Invalid chart box in {spec!r}; coordinates must be non-negative and size positive")
    path = resolved_path(raw_path)
    validate_reference(path)
    return path, (x, y, width, height)


def render_chart_panel(chart_path: Path, width: int, height: int) -> Image.Image:
    with Image.open(chart_path) as source:
        chart = source.convert("RGBA")
    chart.thumbnail((width, height), Image.Resampling.LANCZOS)
    panel = Image.new("RGBA", (width, height), "white")
    offset = ((width - chart.width) // 2, (height - chart.height) // 2)
    panel.alpha_composite(chart, dest=offset)
    return panel.convert("RGB").convert("RGBA")


def atomic_save_png(image: Image.Image, path: Path) -> None:
    temporary_path = path.with_name(f".{path.stem}.tmp.png")
    image.save(temporary_path, format="PNG", optimize=False)
    temporary_path.replace(path)


def compose_figure(
    schematic_path: Path,
    chart_specs: list[str],
    output_path: Path,
    manifest_path: Path,
) -> None:
    validate_reference(schematic_path)
    if output_path.suffix.lower() != ".png":
        raise UserError("Composite output must be PNG to preserve exact chart-region pixels")
    if manifest_path.suffix.lower() != ".json":
        raise UserError("Provenance manifest must use a .json extension")
    if not chart_specs:
        raise UserError("Compose requires at least one --chart specification")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with Image.open(schematic_path) as source:
            canvas = source.convert("RGBA")
    except Exception as error:
        raise UserError(f"Could not read schematic image {schematic_path}: {error}") from error

    panel_records: list[dict[str, object]] = []
    for index, spec in enumerate(chart_specs, 1):
        chart_path, (x, y, width, height) = parse_chart_spec(spec)
        if x + width > canvas.width or y + height > canvas.height:
            raise UserError(f"Chart box exceeds schematic canvas for {chart_path}")
        panel = render_chart_panel(chart_path, width, height)
        canvas.alpha_composite(panel, dest=(x, y))
        panel_records.append(
            {
                "panel": index,
                "source_path": str(chart_path),
                "source_sha256": sha256_file(chart_path),
                "box": {"x": x, "y": y, "width": width, "height": height},
                "rendered_pixel_sha256": pixel_hash(panel),
            }
        )

    final_image = canvas.convert("RGB")
    atomic_save_png(final_image, output_path)
    manifest = {
        "schema_version": 1,
        "schematic_path": str(schematic_path),
        "schematic_sha256": sha256_file(schematic_path),
        "output_path": str(output_path),
        "output_sha256": sha256_file(output_path),
        "canvas": {"width": final_image.width, "height": final_image.height},
        "trusted_panels": panel_records,
    }
    temporary_manifest = manifest_path.with_name(f".{manifest_path.name}.tmp")
    temporary_manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary_manifest.replace(manifest_path)
    emit_event(
        "composite_saved",
        output=str(output_path),
        manifest=str(manifest_path),
        trusted_panels=len(panel_records),
    )


def verify_manifest(manifest_path: Path, strict: bool = False) -> list[str]:
    if not manifest_path.is_file():
        raise UserError(f"Provenance manifest does not exist: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise UserError(f"Provenance manifest is invalid JSON: {manifest_path}") from error
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise UserError("Unsupported provenance manifest schema")

    output_path = resolved_path(str(manifest.get("output_path", "")))
    if not output_path.is_file():
        raise UserError(f"Composite output does not exist: {output_path}")
    findings: list[str] = []
    if sha256_file(output_path) != manifest.get("output_sha256"):
        findings.append("Composite output hash does not match the provenance manifest")
    try:
        with Image.open(output_path) as source:
            composite = source.convert("RGBA")
    except Exception as error:
        raise UserError(f"Composite output is not a valid image: {error}") from error

    panels = manifest.get("trusted_panels")
    if not isinstance(panels, list) or not panels:
        raise UserError("Provenance manifest contains no trusted panels")
    for panel in panels:
        if not isinstance(panel, dict) or not isinstance(panel.get("box"), dict):
            raise UserError("Provenance manifest contains an invalid panel record")
        source_path = resolved_path(str(panel.get("source_path", "")))
        if not source_path.is_file():
            findings.append(f"Trusted source is missing: {source_path}")
        elif sha256_file(source_path) != panel.get("source_sha256"):
            findings.append(f"Trusted source changed: {source_path}")
        box = panel["box"]
        try:
            x = int(box["x"])
            y = int(box["y"])
            width = int(box["width"])
            height = int(box["height"])
        except (KeyError, TypeError, ValueError) as error:
            raise UserError("Provenance manifest contains invalid panel coordinates") from error
        region = composite.crop((x, y, x + width, y + height))
        if pixel_hash(region) != panel.get("rendered_pixel_sha256"):
            findings.append(f"Trusted panel pixels changed in composite: {source_path}")

    if findings:
        emit_event(
            "verification_completed",
            manifest=str(manifest_path),
            status="warnings",
            strict=strict,
            findings=findings,
        )
        if strict:
            raise UserError("Strict verification failed: " + "; ".join(findings))
        return findings

    emit_event(
        "verification_completed",
        manifest=str(manifest_path),
        status="passed",
        strict=strict,
        trusted_panels=len(panels),
    )
    return []


def add_network_arguments(parser: argparse.ArgumentParser, include_references: bool) -> None:
    parser.add_argument("--config", required=True, help="Path to the single .env configuration file")
    parser.add_argument("--prompt-file", required=True, help="UTF-8 prompt file")
    if include_references:
        parser.add_argument("--reference", action="append", default=[], help="Reference image; repeatable")
        parser.add_argument("--mask", help="Optional PNG alpha mask")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    preflight_parser = subparsers.add_parser("preflight", help="Validate configuration and inputs")
    preflight_parser.add_argument("--mode", choices=("generate", "edit"), required=True)
    add_network_arguments(preflight_parser, include_references=True)

    generate_parser = subparsers.add_parser("generate", help="Generate a schematic without references")
    add_network_arguments(generate_parser, include_references=False)
    generate_parser.add_argument("--output", required=True)

    edit_parser = subparsers.add_parser("edit", help="Generate a schematic from reference images")
    add_network_arguments(edit_parser, include_references=True)
    edit_parser.add_argument("--output", required=True)

    compose_parser = subparsers.add_parser("compose", help="Overlay immutable charts onto a schematic")
    compose_parser.add_argument("--schematic", required=True)
    compose_parser.add_argument("--chart", action="append", required=True, help="PATH@X,Y,W,H; repeatable")
    compose_parser.add_argument("--output", required=True)
    compose_parser.add_argument("--manifest", required=True)

    verify_parser = subparsers.add_parser("verify", help="Report chart and composite integrity findings")
    verify_parser.add_argument("--manifest", required=True)
    verify_parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with an error when integrity findings are detected",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command in {"preflight", "generate", "edit"}:
        mode = args.mode if args.command == "preflight" else args.command
        config_path = resolved_path(args.config)
        prompt_path = resolved_path(args.prompt_file)
        reference_paths = [resolved_path(path) for path in getattr(args, "reference", [])]
        mask_path = resolved_path(args.mask) if getattr(args, "mask", None) else None
        output_path = resolved_path(args.output) if hasattr(args, "output") else None
        config, prompt, timeout_seconds = preflight_network(
            mode,
            config_path,
            prompt_path,
            reference_paths,
            mask_path,
            output_path,
        )
        if args.command == "preflight":
            return 0
        if mode == "generate":
            image_bytes = generate_image(config, prompt, timeout_seconds)
        else:
            image_bytes = edit_image(
                config,
                prompt,
                timeout_seconds,
                reference_paths,
                mask_path,
            )
        if output_path is None:
            raise UserError("Output path is required")
        save_api_image(image_bytes, output_path, config["GPT_IMAGE_OUTPUT_FORMAT"])
        print(output_path)
        return 0

    if args.command == "compose":
        compose_figure(
            resolved_path(args.schematic),
            args.chart,
            resolved_path(args.output),
            resolved_path(args.manifest),
        )
        print(resolved_path(args.output))
        return 0

    if args.command == "verify":
        verify_manifest(resolved_path(args.manifest), strict=args.strict)
        return 0
    raise UserError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except UserError as error:
        emit_event("command_failed", error=str(error), error_type=type(error).__name__)
        raise SystemExit(2) from error
