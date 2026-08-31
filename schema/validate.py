"""Validate a MindelSpec document against schema/mindelspec.v0.json."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schema" / "mindelspec.v0.json"


def validate(doc_path: Path, schema_path: Path = SCHEMA_PATH) -> list[str]:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    doc = json.loads(doc_path.read_text(encoding="utf-8"))
    validator = Draft7Validator(schema)
    return [f"{'/'.join(str(p) for p in err.path) or '<root>'}: {err.message}" for err in validator.iter_errors(doc)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("docs", nargs="+", type=Path)
    parser.add_argument("--schema", type=Path, default=SCHEMA_PATH)
    args = parser.parse_args()
    failed = False
    for path in args.docs:
        errors = validate(path, args.schema)
        if errors:
            failed = True
            print(f"FAIL {path}")
            for err in errors:
                print(f"  - {err}")
        else:
            print(f"OK   {path}")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
