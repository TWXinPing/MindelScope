# Contributing

1. Validate `*.mindel.json` with `python schema/validate.py path/to/file.json`.
2. Keep paper-only modules `implemented: false`.
3. Scenario scripts must describe the same plant the simulator runs.
4. New catalog entries go in `examples/<id>/` and `platform/catalog.js` **only after** they leave `sandbox/`.
5. Do not mark `author-confirmed` without a written note from the original team or a named reviewer (see `platform/submit.html`).
6. Do not link `sandbox/mosaic/viewer` from the workshop pack or the catalog.
