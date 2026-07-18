# Lightweight figure contract before image generation

A useful research figure is a visual argument, not a decorated chart. Start with the result the user wants to communicate, then choose how much evidence protection the destination actually requires.

## Default contract

1. **Core conclusion**: state the one-sentence claim the figure must defend.
2. **Evidence chain**: map every chart to a unique question and drop redundant panels.
3. **Archetype**: choose `schematic-led composite`, `evidence-led composite`, `image plate + quant`, `before/after mechanism`, or `pipeline plus outcomes`.
4. **AI role**: define conceptual entities, relationships, context, and the visual role of each chart. Explicitly forbid invented observations and unsupported numbers.
5. **Delivery contract**: set the canvas and intended output before the API call.

For manuscript, archive, or exact-evidence work, extend the contract with source provenance, immutable labels, SHA-256 hashes, reserved chart boxes, deterministic composition, and strict verification.

## Fail-fast gates

- Stop when API URL, key, model, timeout, or response mode is missing.
- Stop when the relay protocol differs from the configured generation/edit transport.
- Stop on integrity findings only when the user requested strict verification.

The chart serves the scientific logic. GPT Image styling is subordinate to clarity, defensibility, and provenance.
