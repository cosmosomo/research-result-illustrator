---
name: research-result-illustrator
description: Turn research charts and result plots into clear scientific illustrations or layout blueprints with GPT Image 2. Use when a research agent has produced data plots, heatmaps, microscopy panels, model metrics, or statistical charts and needs a graphical abstract, mechanism figure, result overview, slide visual, poster, or manuscript schematic. Supports generation, reference editing, deterministic multi-panel reference sheets, exact chart compositing, provenance manifests, and scientific-state drift QA when quantitative pixels matter.
---

# Research Result Illustrator

Use this as the only skill entry point. The research agent supplies charts; this skill designs the scientific visual argument and generates or edits the illustration. Add deterministic chart compositing and strict verification only when the output must preserve exact quantitative pixels.

## Core rule

Treat GPT Image output as an illustration, not a new measurement. If a source panel contains curves, points, heatmap cells, error bars, peak locations, axes, or numeric labels that support a claim, the AI output is a layout blueprint by default. Rebuild from source data or use exact-evidence composition before publication.

## Workflow

1. Read `manifest.yaml` and every file in `always_load`.
2. Capture a one-sentence conclusion, input charts, target use, final canvas, scientific exclusions, and a state-lock list: preprocessing state, normalization scope, axis direction/range, group/fold unit, uncertainty definition, and immutable labels.
3. Read `references/figure-contract.md` and define the minimum evidence hierarchy needed for the requested output.
4. Read `references/prompt-contract.md` and only the relevant `references/gpt-image/` category.
5. Choose one image mode:
   - `generate`: create a new conceptual schematic canvas;
   - `edit`: preserve layout, subject, apparatus, or visual identity from references;
   - `edit + mask`: constrain the editable reference region.
6. When three or more images describe one composite, build one deterministic `reference-sheet` first. Multiple independent style or identity references may remain separate when each has a named role.
7. Run `preflight`, then `generate` or `edit` with `scripts/research_illustrator.py`. Network commands read one explicit config file and have no fallback provider.
8. Compare source and output side by side. Audit layout, text, quantitative geometry, and scientific state separately; do not accept a visually attractive result that changes the data state.
9. For conceptual communication, deliver the generated image and identify any AI-redrawn chart content. For quantitative figures, replace redrawn content with deterministic source panels or rebuild the accepted geometry from source data.
10. For manuscripts, archives, or any exact-evidence request, run `compose` to place original chart pixels, then run `verify`. Verification reports findings without blocking by default; add `--strict` only when a failed integrity check must stop delivery.

## Failure handling

- On HTTP 524 or a multipart timeout, do not repeat the identical request. If the references form one layout, create one deterministic reference sheet and make one explicit retry.
- On `content_policy_violation` for benign scientific material, preserve the reference, model, exclusions, and scientific meaning; rewrite only the prompt into neutral descriptive language, save it as a new prompt file, and make one explicit retry.
- Never automate these retries or hide the first failure. Record the failed request class, elapsed time, changed variable, and retry outcome.

## Commands

```text
uv run python gpt-image-2/skills/research-result-illustrator/scripts/research_illustrator.py preflight --mode edit --config gpt-image-2/.env --prompt-file prompt.md --reference chart.png

uv run python gpt-image-2/skills/research-result-illustrator/scripts/research_illustrator.py edit --config gpt-image-2/.env --prompt-file prompt.md --reference chart.png --output outputs/schematic.png

uv run python gpt-image-2/skills/research-result-illustrator/scripts/research_illustrator.py reference-sheet --panel "panel-a.png@40,40,700,440" --panel "panel-b.png@780,40,700,440" --canvas 1536x1024 --background "#ffffff" --output outputs/reference-sheet.png

uv run python gpt-image-2/skills/research-result-illustrator/scripts/research_illustrator.py compose --schematic outputs/schematic.png --chart "chart.png@120,180,960,640" --output outputs/final.png --manifest outputs/final.provenance.json

uv run python gpt-image-2/skills/research-result-illustrator/scripts/research_illustrator.py verify --manifest outputs/final.provenance.json

uv run python gpt-image-2/skills/research-result-illustrator/scripts/research_illustrator.py verify --manifest outputs/final.provenance.json --strict
```

Resolve and report absolute paths. Never continue after a failed preflight or API call. Treat normal verification findings as visible warnings; only strict verification blocks delivery.

## Configuration

Live generation/editing uses the single explicit configuration file supplied with `--config`; this repository provides the non-secret schema in `gpt-image-2/.env.example`. It contains the full generate/edit endpoint URLs, API key, model, timeout, image format, response mode, edit field, and input fidelity. Copy it to an untracked local `.env` and fill it locally. Never print or copy the API key into prompts, logs, provenance manifests, or deliverables. `compose`, `reference-sheet`, and `verify` require no API configuration.

## Deliverables

Always deliver the final image and final prompt. For quantitative figures, also deliver the state-lock list and source-versus-output drift notes. Include source panels, provenance JSON, non-secret configuration summary, and QA notes when exact-evidence mode is requested. For manuscript submission, use a deterministic layout tool for SVG/PDF/TIFF exports; never describe AI-generated pixels as experimental evidence.
