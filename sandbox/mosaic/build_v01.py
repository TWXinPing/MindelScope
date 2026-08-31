"""Build a v0.1 wrapper around the v0 MOSAIC document."""

from __future__ import annotations

import json
from pathlib import Path

src = Path(__file__).with_name("mosaic.mindel.json")
doc = json.loads(src.read_text(encoding="utf-8"))
doc["mindelspec"] = "0.1"
doc["caption"] = "Two paired forward–inverse modules switch between free space and a viscous field; λ comes from prediction error, not from a context predictor."
doc["staticOnly"] = False
doc["doubleEncoding"] = {"typeByShape": True, "identityByColor": True}
doc["reports"] = {
    "clocks": ["across_trials", "within_trial"],
    "hasDistribution": True,
    "hasScenario": True,
    "hasUnimplementedSplit": True,
}
doc["groups"] = [
    {"id": "module_1", "label": "Free-space pair"},
    {"id": "module_2", "label": "Viscous-field pair"},
]
doc["relatedStandards"] = {"doi": "10.1016/S0893-6080(98)00066-5"}
out = Path(__file__).with_name("mosaic.mindel.v0.1.json")
out.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Wrote {out}")
