# Default operating stance

## Composition

- Prefer one hero schematic plus subordinate evidence panels over equal-sized tiles.
- Keep generated and measured layers visibly distinguishable.
- Reserve chart boxes before generation; do not generate first and force charts into accidental spaces.
- Reuse condition colors, symbols, and terminology across schematic and chart panels.
- Keep plots on opaque white panels; use dark image plates only when the source evidence requires it.

## Scientific integrity

- Treat statistics, `n`, uncertainty, source-data traceability, scale bars, and image-processing notes as part of the figure.
- Use GPT Image output only as conceptual illustration, never as measurement.
- Add long labels, equations, axes, and exact notation with deterministic tools after generation.
- Identify every unsupported mechanism or ambiguous generated object during QA.

## Prompting

- Load only one or two relevant GPT Image references rather than the entire gallery.
- For edits, repeat invariants and name each reference image's role.
- Change one variable per iteration; do not silently relax scientific exclusions.
- Prefer high quality for final scientific illustrations and a cheaper setting only for explicit drafts.

## Privacy

Do not send confidential manuscript content, unpublished patient data, identifying images, or restricted source material to a relay without explicit authorization. Never print API keys or embed them in prompts, manifests, or logs.
