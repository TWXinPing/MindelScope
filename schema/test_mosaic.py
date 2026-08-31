"""Sanity-check MOSAIC MindelSpec and the authoring heuristics."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = json.loads((ROOT / "sandbox" / "mosaic" / "mosaic.mindel.json").read_text(encoding="utf-8"))


def test_mosaic_honesty() -> None:
    ids = {m["id"] for m in SPEC["modules"]}
    assert "resp_predictor" in ids
    pred = next(m for m in SPEC["modules"] if m["id"] == "resp_predictor")
    assert pred["implemented"] is False
    assert "resp_predictor" in SPEC["unimplemented"]
    for mod in SPEC["modules"]:
        ann = mod.get("annotation") or {}
        assert ann.get("goal"), mod["id"]
        assert ann.get("scenario"), mod["id"]


def test_scenarios_match_plant() -> None:
    viscous = json.loads((ROOT / "sandbox/mosaic/scenarios/viscous_field.json").read_text(encoding="utf-8"))
    delay = json.loads((ROOT / "sandbox/mosaic/scenarios/sensory_delay.json").read_text(encoding="utf-8"))
    blob = viscous["realWorldAnalogy"] + delay["realWorldAnalogy"]
    assert "cup" not in blob.lower()
    assert "viscous" in viscous["realWorldAnalogy"].lower() or "黏滯" in viscous["title"]


if __name__ == "__main__":
    test_mosaic_honesty()
    test_scenarios_match_plant()
    print("OK sandbox/mosaic")
