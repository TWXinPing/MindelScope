# MindelSpec v0.1

v0.1 keeps the v0 glyph set and adds reporting rules learned from existing diagram protocols. Schema file: [schema/mindelspec.v0.1.json](../schema/mindelspec.v0.1.json).

## What changed after v0

- `caption` is required at the model level (a sentence a non-author can read).
- `staticOnly` flags figures that have no traces.
- `doubleEncoding` records whether type is encoded by shape *and* another channel.
- `reports` lists which clocks, distributions, and scenarios are present.
- `relatedStandards` points at NeuroML / openMINDS / ModelDB records without importing them.
- Nested `group` remains a string in v0; v0.1 allows `groups[]` with parent ids for compound boxes.

## Ten rules

1. **Shape carries type.** Colour may mark identity (module 1 vs 2) but must not be the only cue. (Senna et al. 2025; Senk et al. 2022 both warn against colour-only legends.)
2. **Annotate three ways.** Goal, equation, situation. Missing equation must say `none`.
3. **Name the arrow.** information / gating / error / context. Do not reuse one arrowhead for all four.
4. **Distributions are nodes.** Softmax, Gaussian likelihoods, and priors are not a footnote.
5. **Time is explicit.** Either bind traces or set `staticOnly: true`.
6. **Separate paper and code.** Unimplemented paper parts are dashed and listed in `unimplemented`.
7. **Draw the world** if the model controls or predicts a plant.
8. **Scenario matches the simulator.** Do not narrate lifting cups if the plant is a viscous field.
9. **Classic models start unofficial.** `interpretation` stays `unofficial` until the original team or a named reviewer confirms meaning.
10. **Export two artefacts.** Static SVG/PNG for the PDF; interactive page for supplementary / teaching.

## Relationship to other standards

| Standard | Role relative to MindelSpec |
|---|---|
| ModelDB | Store and cite the simulator. Link from `relatedStandards.modeldb`. |
| NeuroML / OSB | Biophysical / network implementation. Optional mapping later; not a requirement for cognitive-level figures. |
| openMINDS computation | Provenance metadata for simulation runs. Complementary. |
| Senk et al. 2022 connectivity notation | Population-level neural networks. Reuse their edge annotations if you zoom to that scale. |
| COGENT | Executable cognitive boxes. MindelSpec is language-first, execution-optional. |

## Success test

A researcher who has never implemented MOSAIC, given only the glyph sheet, can point to the dashed box and say “that is gating, not prediction error”, and can say whether λ is a distribution or a single switch.
