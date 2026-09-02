from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "research-result-illustrator"
    / "scripts"
    / "research_illustrator.py"
)
SPEC = importlib.util.spec_from_file_location("research_illustrator", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load test target: {SCRIPT_PATH}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ResearchIllustratorTests(unittest.TestCase):
    def create_image(self, path: Path, size: tuple[int, int], color: str) -> None:
        image = Image.new("RGB", size, color)
        draw = ImageDraw.Draw(image)
        draw.line((10, size[1] - 10, size[0] - 10, 10), fill="black", width=4)
        image.save(path, format="PNG")

    def test_compose_and_verify_preserve_trusted_panel(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            schematic = directory / "schematic.png"
            chart = directory / "chart.png"
            output = directory / "final.png"
            manifest = directory / "final.provenance.json"
            self.create_image(schematic, (800, 500), "#dceaf3")
            self.create_image(chart, (320, 200), "white")

            MODULE.compose_figure(
                schematic,
                [f"{chart}@400,250,320,200"],
                output,
                manifest,
            )
            self.assertEqual(MODULE.verify_manifest(manifest), [])

            payload = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(payload["trusted_panels"][0]["source_path"], str(chart.resolve()))

    def test_verify_reports_tampered_composite_without_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            schematic = directory / "schematic.png"
            chart = directory / "chart.png"
            output = directory / "final.png"
            manifest = directory / "final.provenance.json"
            self.create_image(schematic, (640, 480), "#e8eef0")
            self.create_image(chart, (240, 160), "white")
            MODULE.compose_figure(
                schematic,
                [f"{chart}@300,200,240,160"],
                output,
                manifest,
            )

            with Image.open(output) as source:
                modified = source.convert("RGB")
            modified.putpixel((320, 220), (255, 0, 0))
            modified.save(output, format="PNG")

            findings = MODULE.verify_manifest(manifest)

            self.assertTrue(any("output hash" in finding for finding in findings))

    def test_strict_verify_rejects_tampered_composite(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            schematic = directory / "schematic.png"
            chart = directory / "chart.png"
            output = directory / "final.png"
            manifest = directory / "final.provenance.json"
            self.create_image(schematic, (640, 480), "#e8eef0")
            self.create_image(chart, (240, 160), "white")
            MODULE.compose_figure(
                schematic,
                [f"{chart}@300,200,240,160"],
                output,
                manifest,
            )

            with Image.open(output) as source:
                modified = source.convert("RGB")
            modified.putpixel((320, 220), (255, 0, 0))
            modified.save(output, format="PNG")

            with self.assertRaisesRegex(MODULE.UserError, "Strict verification failed"):
                MODULE.verify_manifest(manifest, strict=True)

    def test_preflight_rejects_missing_network_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            config = directory / ".env"
            prompt = directory / "prompt.md"
            config.write_text(
                "GPT_IMAGE_GENERATE_URL=\nGPT_IMAGE_API_KEY=\nGPT_IMAGE_MODEL=gpt-image-2\n",
                encoding="utf-8",
            )
            prompt.write_text("Conceptual research schematic", encoding="utf-8")

            with self.assertRaisesRegex(MODULE.UserError, "Missing required configuration"):
                MODULE.preflight_network("generate", config, prompt, [], None, None)

    def test_reference_sheet_profiles_and_composes_source_panels(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            first = directory / "first.png"
            second = directory / "second.png"
            output = directory / "reference-sheet.png"
            self.create_image(first, (80, 40), "white")
            self.create_image(second, (40, 80), "#dceaf3")

            profile = MODULE.profile_references([first, second])
            self.assertEqual(profile["count"], 2)
            self.assertEqual(profile["total_pixels"], 6400)

            MODULE.build_reference_sheet(
                [f"{first}@0,0,80,40", f"{second}@100,20,40,80"],
                (160, 120),
                "#ffffff",
                output,
            )

            with Image.open(output) as image:
                self.assertEqual(image.size, (160, 120))

            with self.assertRaisesRegex(MODULE.UserError, "exceeds canvas"):
                MODULE.build_reference_sheet(
                    [f"{first}@100,100,80,40"],
                    (160, 120),
                    "#ffffff",
                    output,
                )


if __name__ == "__main__":
    unittest.main()
