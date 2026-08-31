"""CLI consistency agent for MindelSpec (mirrors authoring/agent.js)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def suggest(spec: dict) -> list[dict]:
    notes = []
    modules = spec.get("modules") or []
    edges = spec.get("edges") or []
    by_type = lambda t: [m for m in modules if m.get("type") == t]
    ids = {m["id"] for m in modules}

    if not by_type("plant"):
        notes.append({"kind": "add-module", "type": "plant", "reason": "A cognitive control model needs an explicit body or environment node."})

    for fwd in modules:
        if fwd.get("role") == "predictor" or str(fwd.get("label", "")).lower().startswith("forward"):
            cmp = next((m for m in modules if m.get("type") == "comparator" and m.get("group") == fwd.get("group")), None)
            if not cmp:
                notes.append({"kind": "add-module", "type": "comparator", "reason": f"{fwd['id']} predicts but has no comparator."})

    if any(m.get("role") == "controller" for m in by_type("process")) and not by_type("gate"):
        notes.append({"kind": "add-module", "type": "gate", "reason": "Multiple controllers should mix through a gate."})

    if by_type("comparator") and not by_type("distribution"):
        notes.append({"kind": "add-module", "type": "distribution", "reason": "Prediction errors should land in an explicit distribution node."})

    for edge in edges:
        if edge.get("source") not in ids or edge.get("target") not in ids:
            notes.append({"kind": "remove-edge", "id": edge.get("id"), "reason": f"{edge.get('id')} points at a missing module."})
            continue
        src = next(m for m in modules if m["id"] == edge["source"])
        tgt = next(m for m in modules if m["id"] == edge["target"])
        gating_ok = src["type"] in {"gate", "distribution"} or tgt["type"] in {"gate", "distribution"} or edge.get("gatedBy")
        if edge.get("type") == "gating" and not gating_ok:
            notes.append({"kind": "retype-edge", "id": edge["id"], "reason": "Gating edges should touch a gate or distribution, or set gatedBy."})
        if edge.get("type") == "error" and src.get("type") not in {"comparator", "distribution"} and src.get("role") != "error_corrector":
            notes.append({"kind": "retype-edge", "id": edge["id"], "reason": "Error edges should start from a comparator, distribution, or reflex."})

    for mod in modules:
        ann = mod.get("annotation") or {}
        if not ann.get("goal"):
            notes.append({"kind": "annotate", "id": mod["id"], "reason": f"{mod['id']} has no computational goal."})
        if not ann.get("equation") and mod.get("type") in {"process", "comparator", "distribution", "gate", "plant"}:
            notes.append({"kind": "annotate", "id": mod["id"], "reason": f"{mod['id']} should carry an equation."})
        if not ann.get("scenario"):
            notes.append({"kind": "annotate", "id": mod["id"], "reason": f"{mod['id']} is not mapped onto a real situation."})
    return notes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", type=Path)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    notes = suggest(spec)
    if not notes:
        print("OK — no consistency notes")
        return
    for n in notes:
        print(f"{n['kind']}: {n['reason']}")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
