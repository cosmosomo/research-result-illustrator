---
name: research-result-illustrator
description: Turn research charts and result plots into clear scientific illustrations with GPT Image 2. Use when a research agent has produced data plots, heatmaps, microscopy panels, model metrics, or statistical charts and needs a graphical abstract, mechanism figure, result overview, slide visual, poster, or manuscript schematic. Supports direct generation and reference editing first, with optional masks, multiple references, deterministic chart compositing, provenance manifests, and strict integrity verification when exact quantitative pixels matter.
---

# Research Result Illustrator

Use this as the only skill entry point. The research agent supplies charts; this skill designs the scientific visual argument and generates or edits the illustration. Add deterministic chart compositing and strict verification only when the output must preserve exact quantitative pixels.

## Core rule

Treat GPT Image output as an illustration, not a new measurement. Inspect generated axes, values, error bars, significance marks, labels, scale bars, legends, microscopy, and measured effects before presenting them as evidence. Use exact-evidence mode when those pixels must remain unchanged.

## Workflow

1. Read `manifest.yaml` and every file in `always_load`.
2. Capture a one-sentence conclusion, input charts, target use, final canvas, and scientific exclusions. Do not block an exploratory draft on missing publication metadata.
3. Read `references/figure-contract.md` and define the minimum evidence hierarchy needed for the requested output.
4. Read `references/prompt-contract.md` and only the relevant `references/gpt-image/` category.
5. Choose one image mode:
   - `generate`: create a new conceptual schematic canvas;
   - `edit`: preserve layout, subject, apparatus, or visual identity from references;
   - `edit + mask`: constrain the editable reference region.
6. Run `preflight`, then `generate` or `edit` with `scripts/research_illustrator.py`. Network commands read one explicit config file and have no fallback provider.
7. Visually inspect the result and iterate on the prompt or references until the scientific story is clear.
8. For ordinary research communication, deliver the generated image with a note that quantitative details were visually checked.
9. For manuscripts, archives, or any exact-evidence request, run `compose` to place original chart pixels, then run `verify`. Verification reports findings without blocking by default; add `--strict` only when a failed integrity check must stop delivery.

## Commands

```text
uv run python gpt-image-2/skills/research-result-illustrator/scripts/research_illustrator.py preflight --mode edit --config gpt-image-2/.env --prompt-file prompt.md --reference chart.png

uv run python gpt-image-2/skills/research-result-illustrator/scripts/research_illustrator.py edit --config gpt-image-2/.env --prompt-file prompt.md --reference chart.png --output outputs/schematic.png

uv run python gpt-image-2/skills/research-result-illustrator/scripts/research_illustrator.py compose --schematic outputs/schematic.png --chart "chart.png@120,180,960,640" --output outputs/final.png --manifest outputs/final.provenance.json

uv run python gpt-image-2/skills/research-result-illustrator/scripts/research_illustrator.py verify --manifest outputs/final.provenance.json

uv run python gpt-image-2/skills/research-result-illustrator/scripts/research_illustrator.py verify --manifest outputs/final.provenance.json --strict
```

Resolve and report absolute paths. Never continue after a failed preflight or API call. Treat normal verification findings as visible warnings; only strict verification blocks delivery.

## Configuration

Live generation/editing requires `GPT_IMAGE_GENERATE_URL`, `GPT_IMAGE_EDIT_URL`, and `GPT_IMAGE_API_KEY` in the explicit `--config` file. `compose` and `verify` require no API configuration. The full required schema is in `gpt-image-2/.env.example`.

## Deliverables

Always deliver the final image and final prompt. Include source panels, provenance JSON, non-secret configuration summary, and QA notes when exact-evidence mode is requested. For manuscript submission, use a deterministic layout tool for SVG/PDF/TIFF exports; never describe AI-generated pixels as experimental evidence.
