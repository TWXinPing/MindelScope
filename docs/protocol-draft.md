# MindelSpec v0 — protocol draft

This is the one-page language for workshop feedback. MOSAIC is the first *test case* in `sandbox/mosaic/`; it is not yet the public demo.

## Why another diagram language?

Box-and-arrow figures in cognitive neuroscience are locally meaningful and globally inconsistent. The same arrow can mean “sends a spike”, “gates a command”, “is a prediction error”, or “happens later”. MindelSpec names those differences.

It does **not** replace NeuroML, ModelDB, or openMINDS. Those store simulators and metadata. This stores *how to read the figure*.

## Module types

| Type | Shape | Means |
|---|---|---|
| `process` | rounded rectangle | A transformation (forward / inverse / predictor) |
| `representation` | parallelogram | State, goal, or cue |
| `comparator` | circle (summing junction) | Error |
| `gate` | stadium | Weighted mix or selection |
| `distribution` | rectangle + bars | Hypothesis distribution |
| `delay` | dashed rounded rectangle | Sensory / feedback lag |
| `plant` | thick rectangle | Body or world |
| `scenario_event` | caption, not a box | A beat in a behavioural story |

## Edge types

| Type | Look | Means |
|---|---|---|
| `information` | solid arrow | A signal is copied or transformed |
| `gating` | width ∝ λ | Contribution is scaled by a belief |
| `error` | rust arrow | Teaching or mismatch signal |
| `context` | dashed | Sensory cue into a prior / predictor |

## Three annotations on every node

1. **Goal** — what computational problem this box solves.
2. **Equation** — the mapping, or the word `none`.
3. **Scenario** — what it corresponds to in a real situation.

## Paper vs implementation

If a box exists in the source paper but not in the attached simulator, set `implemented: false`. The viewer draws it grey and labels it `not in this implementation`. Do not colour it as if it were running.

## Time

Bind traces to module ids. Prefer two clocks when both exist:

- across trials / blocks (learning, context switches)
- within a trial (one movement, one decision)

## MOSAIC as the first test

The 1D demo can express: two process pairs, comparators, a λ distribution, a gate, a plant, a delay, gated learning edges, and a grey responsibility predictor. It cannot yet express hierarchical nesting or neural implementation maps — that is v0.1+ work.
