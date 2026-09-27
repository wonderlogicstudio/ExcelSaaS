"""Write the synthetic supported-control repair and its bounded proof."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/api"))
spec = importlib.util.spec_from_file_location(
    "false_repair_guard_fixture", ROOT / "apps/api/tests/test_false_repair_guard.py"
)
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)

from app.config import Settings  # noqa: E402
from app.delivery_execution import compatibility_status  # noqa: E402
from app.delivery_inputs import PROFILE_1, PROFILE_2, PROFILE_COMBINED, inspect_input  # noqa: E402
from app.delivery_patch import patch_workbook, verify_output  # noqa: E402
from app.delivery_plan import build_plan  # noqa: E402
from app.delivery_store import DeliveryStore  # noqa: E402


def main() -> None:
    evidence = ROOT / "artifacts/synthetic_validation/false-repair-guard01"
    source = fixture.mixed_workbook(fixture.CONTROL)
    snapshot = inspect_input("guard.xlsx", source, Settings())
    store = DeliveryStore(evidence / "runtime")
    job = store.create("owner", source, snapshot, "false-repair-guard-artifact")
    policy = {
        "profile": PROFILE_COMBINED,
        "items": [
            fixture.policy(PROFILE_1, ["B2", "B3"]),
            fixture.policy(PROFILE_2, ["F3"]),
        ],
    }
    plan = build_plan(job, policy)
    repaired = patch_workbook(source, snapshot, plan)
    verification = verify_output(source, repaired, plan, Settings())
    original_path = evidence / "supported-control-source.xlsx"
    repaired_path = evidence / "supported-control-repaired.xlsx"
    original_path.write_bytes(source)
    repaired_path.write_bytes(repaired)
    report = {
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "source_sha256_after": hashlib.sha256(original_path.read_bytes()).hexdigest(),
        "repaired_sha256": hashlib.sha256(repaired).hexdigest(),
        "oracle_sha256": hashlib.sha256(
            (evidence / "expected-supported-control.json").read_bytes()
        ).hexdigest(),
        "exact_targets": plan["exact_targets"],
        "F3_engine_calculated": plan["expected_calculated_values"][fixture.SHEET]["F3"],
        "G2_engine_calculated": plan["expected_calculated_values"][fixture.SHEET]["G2"],
        "verification": verification,
        "native_compatibility": compatibility_status(),
    }
    (evidence / "supported-control-result.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "source_sha256": report["source_sha256"],
        "repaired_sha256": report["repaired_sha256"],
        "exact_targets": report["exact_targets"],
        "native_compatibility": report["native_compatibility"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
