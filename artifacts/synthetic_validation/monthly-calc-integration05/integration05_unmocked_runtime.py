from __future__ import annotations

import json
from pathlib import Path

from app.delivery_execution import compatibility_status
from app.delivery_plan import reference_status
from app.delivery_runtime_check import verify

repo = Path(__file__).resolve().parents[3]
sample_dir = repo / "samples" / "delivery-v3_2"
out_path = Path(__file__).with_name("unmocked-runtime-result.json")

before = {
    "reference_status": reference_status(),
    "compatibility_status": compatibility_status(),
}
if before["reference_status"].get("status") != "PASS":
    raise SystemExit(f"reference_status not PASS: {before['reference_status']}")
if before["compatibility_status"].get("status") != "PASS":
    raise SystemExit(f"compatibility_status not PASS: {before['compatibility_status']}")

result = verify(sample_dir)
evidence = {
    "status": "PASS",
    "kind": "UNMOCKED_REFERENCE_COMPATIBILITY_RP01_RP02_RUNTIME",
    "before": before,
    "runtime_result": result,
    "boundaries": {
        "compatibility_mocked": False,
        "reference_mocked": False,
        "excel_browser_deploy_git": False,
        "profiles": ["RP01_NUMERIC_TEXT_FIELD_V1", "RP02_FORMULA_RESTORE_V1"],
    },
}
out_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(evidence, ensure_ascii=False, sort_keys=True))
