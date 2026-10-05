from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(r"C:\Users\JinwonLee\project\ExcelSaaS")
SCRATCH = Path(r"C:\Users\JinwonLee\project\DigitalTwin\.tmp\monthly-calc-excel04")
sys.path.insert(0, str(REPO / "apps/api"))

from app.delivery_calculation import CALCULATION_MODE_MONTHLY_SHEETS, calculate, engine_fingerprint  # noqa: E402

oracle_path = REPO / "artifacts/synthetic_validation/monthly-repair-spec01/acceptance-oracle.json"
oracle = json.loads(oracle_path.read_text(encoding="utf-8"))
case = oracle["case"]
assert case["sheet"] == "Budget"
assert case["cell"] == "N18"
assert case["after_formula"] == "='M10'!B16-'M10'!B15"
assert case["after_value"] == {"type": "number", "value": -5}
assert case["derivation"] == "M10!B16=1001 minus M10!B15=1006 = -5"

cells = {
    "Budget": {"N18": {"type": "formula", "value": case["after_formula"]}},
    "M10": {
        "B16": {"type": "number", "value": 1001},
        "B15": {"type": "number", "value": 1006},
    },
}
result = calculate(cells, calculation_mode=CALCULATION_MODE_MONTHLY_SHEETS)
actual = result["values"]["Budget"]["N18"]
if actual.get("type") != "number" or actual.get("value") != -5.0:
    raise AssertionError(actual)

evidence = {
    "status": "PASS",
    "kind": "REDUCED_MONTHLY_INTERNAL_ENGINE_CONTROL",
    "source": "monthly-repair-spec01 acceptance oracle case.after_formula/after_value/derivation",
    "engine_fingerprint": engine_fingerprint(),
    "formula": case["after_formula"],
    "operands": {"M10!B16": 1001, "M10!B15": 1006},
    "expected": case["after_value"],
    "actual": actual,
    "note": "Reduced two-sheet internal calculation control; not a supported full 13-sheet fixture run.",
}
path = SCRATCH / "monthly-engine-result.json"
path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
print(json.dumps(evidence, ensure_ascii=False))

