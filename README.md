# MindelScope

Shared visual language for **cognitive neuroscience models**: what each module does, which equation it implements, how signals evolve in time, and which real situation it is supposed to explain.

This is not a replacement for [ModelDB](https://modeldb.science/) or [Open Source Brain](https://www.opensourcebrain.org/). Those store simulators. MindelScope stores a figure that can be read the same way across labs.

## Two tracks

| Track | Path | Status |
|---|---|---|
| Product (language, authoring, catalog, workshop pack) | `schema/`, `authoring/`, `platform/`, `docs/` | In progress |
| MOSAIC visualisation | [`sandbox/mosaic/`](sandbox/mosaic/) | **WIP — not the workshop demo** |

Do not present `/sandbox/mosaic/viewer/` at the open science workshop until [sandbox/mosaic/STATUS.md](sandbox/mosaic/STATUS.md) is complete.

## Quick start (product)

```text
python -m pip install -r requirements.txt
python schema/validate.py sandbox/mosaic/mosaic.mindel.json
python authoring/agent.py sandbox/mosaic/mosaic.mindel.json
python -m http.server 8000
```

Then open http://127.0.0.1:8000/platform/ and http://127.0.0.1:8000/authoring/

## MOSAIC sandbox (separate)

雙擊 `open-mosaic.bat`，或雙擊 `sandbox\mosaic\viewer\index.html`。

```text
python sandbox/mosaic/open_viewer.py
```

## Layout

| Path | Role |
|---|---|
| `schema/` | MindelSpec v0 and v0.1 |
| `sandbox/mosaic/` | Isolated MOSAIC sim + WIP viewer |
| `authoring/` | Draft editor + consistency agent |
| `platform/` | Catalog, guidelines, submit path |
| `docs/workshop/` | Talk pack **without** live MOSAIC |

Classic models stay `unofficial interpretation` until the original team confirms meaning.
