# Existing diagram protocols — comparison matrix

Workshop-week version: a one-page contrast. This is not a systematic review.

| Source | Scale | Time | Probability | Equations | Situation / behaviour | Shared glyphs | Notes |
|---|---|---|---|---|---|---|---|
| Typical cognitive box-and-arrow (textbooks, papers) | Algorithmic / computational | Rarely | Rarely | Sometimes in caption | Often implied, not bound | No | The problem MindelScope starts from |
| [Senk et al. 2022, *PLOS Comp Biol*](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1010086) connectivity notation | Neuronal populations | No | Connection probability as line style | In tables more than glyphs | Devices as I/O, not tasks | Yes (nodes, edges, annotations) | Best existing *network* notation; NEST Desktop implements it |
| [Senna, Marshall, et al. 2025, *PLOS One*](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0318800) NN system diagrams | ML architectures | No | No | Mixed | Occasional input examples | Evidence-based guidance, not a glyph standard | Documents ambiguity; recommends double encoding |
| [Neural Schematics](https://www.frontiersin.org/journals/neuroinformatics/articles/10.3389/fninf.2013.00022/full) (2013) | Large-scale neural nets | No | No | No | No | Yes, circuit-like | Avoids colour because it is ambiguous |
| COGENT (Cooper & Fox) | Cognitive modules | Executable, not a player | Limited | Inside box classes | Task is configured, not narrated | Yes (box classes) | Closest ancestor; dated UI, architecture-bound |
| NAV (Kriete et al.) | Cognitive graphs | Animation from activation matrices | No | No | Sprites possible | Ad hoc | Proves time can be a movie; no shared language |
| Nengo GUI | Neural implementation | Yes, live | Decoded values | In code | Optional sliders | Nengo-specific | Excellent runtime; not a paper protocol |
| [ModelDB](https://modeldb.science/) | Any simulator | No | No | In code | No | No | Archive, not a figure language |
| [Open Source Brain](https://www.opensourcebrain.org/) / NeuroML | Multi-scale biophysics | Simulation viz | Synaptic stats | In NeuroML | Data comparison, not cognitive scenarios | NeuroML | Complementary warehouse |
| openMINDS computation / Neuroshapes | Metadata | Provenance | No | No | No | Schemas | FAIR layer, not glyphs |

## Gap that MindelSpec occupies

Cognitive-level models (Marr’s computational / algorithmic layers) need:

1. a small shared glyph vocabulary,
2. first-class hypothesis distributions,
3. a playback clock,
4. a scenario script that is the same world as the plant,
5. an honest split between paper architecture and this implementation.

No row above has all five. That is the design target, not a claim that those tools failed at their own jobs.

## What we reuse

- From Senk et al.: annotate edges; keep a table for parameters the glyph cannot hold.
- From Senna et al.: double-encode type; do not rely on colour.
- From Neural Schematics: defined entry/exit sides are optional; colour is never the sole cue.
- From COGENT: typed boxes, compound groups.
- From NAV / Nengo: time as a first-class view.
