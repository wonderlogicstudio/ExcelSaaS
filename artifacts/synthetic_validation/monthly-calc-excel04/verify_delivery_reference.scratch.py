from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

REPO = Path(r"C:\Users\JinwonLee\project\ExcelSaaS")
SCRATCH = Path(r"C:\Users\JinwonLee\project\DigitalTwin\.tmp\monthly-calc-excel04")
sys.path.insert(0, str(REPO / "apps/api"))

from app.delivery_calculation import calculate, engine_fingerprint  # noqa: E402

oracle_path = REPO / "samples/delivery-v3_2/reference-cases.json"
reference_path = SCRATCH / "excel-reference.json"
if not reference_path.exists():
    raise SystemExit(f"missing scratch excel reference: {reference_path}")

oracle = json.loads(oracle_path.read_text(encoding="utf-8"))
reference = json.loads(reference_path.read_text(encoding="utf-8-sig"))
source_sha256 = hashlib.sha256(oracle_path.read_bytes()).hexdigest()
assert reference["source_sha256"] == source_sha256


def same(actual: dict, expected: dict) -> None:
    assert actual["type"] == expected["type"], (actual["type"], expected["type"])
    if actual["type"] == "number":
        assert math.isclose(actual["value"], expected["value"], rel_tol=1e-12, abs_tol=1e-12), (
            actual["value"],
            expected["value"],
        )
    else:
        assert actual["value"] == expected["value"], (actual["value"], expected["value"])

rows = []
for case in oracle["cases"]:
    cells = {
        address: {
            "type": "text" if isinstance(value, str) else "boolean" if isinstance(value, bool) else "number",
            "value": value,
            "style": "0",
        }
        for address, value in case["values"].items()
    }
    cells.update(
        {
            address: {"type": "formula", "value": formula, "style": "0"}
            for address, formula in case["formulas"].items()
        }
    )
    expected = case["expected"]
    excel = next(row for row in reference["results"] if row["id"] == case["id"])["values"]
    result = calculate({"검증": cells})["values"]["검증"]
    for address, expected_value in expected.items():
        same(excel[address], expected_value)
        same(result[address], expected_value)
    rows.append({"id": case["id"], "typed_result_count": len(expected), "excel_and_poi_match_policy": True})
    print("Verified:", case["id"], flush=True)

evidence = {
    "status": "PASS",
    "kind": "SCRATCH_REFERENCE_VALIDATION_ONLY",
    "engine_fingerprint": engine_fingerprint(),
    "case_count": len(rows),
    "typed_result_count": sum(row["typed_result_count"] for row in rows),
    "excel_version": reference["version"],
    "excel_build": reference["build"],
    "oracle_sha256": source_sha256,
    "reference_sha256": hashlib.sha256(reference_path.read_bytes()).hexdigest(),
    "rows": rows,
}
(SCRATCH / "delivery_reference.candidate.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
(SCRATCH / "reference-validation.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
print("Scratch independent policy + installed Excel reference + actual isolated POI verified")
