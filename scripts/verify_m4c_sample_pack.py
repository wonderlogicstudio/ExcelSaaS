"""Verify the supplied synthetic M4-C pack through the isolated audit engine.

This developer-only command intentionally prints counts and expected locations
from the supplied synthetic labels. It never prints formulas, cell values, or
uploads files. The free-diagnosis count is displayed separately to prevent it
from being mistaken for the optional formula-audit candidate count.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
SUPPLIED_PACK_ROOT = (
    ROOT
    / "samples"
    / "WorkbookCare_M4C_Sample_Pack_2026-09-01"
    / "WorkbookCare_M4C_Sample_Pack"
)

sys.path.insert(0, str(API_ROOT))

from app.config import Settings  # noqa: E402
from app.scanner import run_formula_audit, scan_workbook  # noqa: E402


AUDIT_SETTINGS = Settings(
    app_env="internal_beta",
    formula_pattern_audit_enabled=True,
    scan_cell_limit=250_000,
    finding_limit=5_000,
)


def _candidate_key(filename: str, candidate: object) -> tuple[str, str | None, str | None, str, str | None]:
    finding = candidate
    evidence = finding.formula_pattern
    return (
        filename,
        finding.sheet,
        finding.cell,
        finding.rule_code,
        evidence.pattern_subtype if evidence else None,
    )


def main() -> int:
    manifest_path = SUPPLIED_PACK_ROOT / "expected" / "m4c_manifest.json"
    if not manifest_path.is_file():
        print(f"M4-C supplied pack is missing: {manifest_path}")
        return 1

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = {
        (
            item["file"],
            item["sheet"],
            item["cell"],
            item["expected_rule"],
            item["expected_subtype"],
        )
        for item in manifest["expected_findings"]
    }
    actual: set[tuple[str, str | None, str | None, str, str | None]] = set()
    failures: list[str] = []

    for scenario in manifest["scenarios"]:
        filename = scenario["file"]
        payload = (SUPPLIED_PACK_ROOT / "samples" / filename).read_bytes()
        base_result = scan_workbook(filename, payload, Settings())
        audit_result = run_formula_audit(filename, payload, AUDIT_SETTINGS)
        if audit_result.status != "COMPLETED":
            failures.append(f"{filename}: audit status={audit_result.status}")
            continue
        actual.update(_candidate_key(filename, candidate) for candidate in audit_result.candidates)
        print(
            f"{filename}: free scan {len(base_result.findings)} findings / "
            f"M4-C audit {len(audit_result.candidates)} candidates"
        )

    missing = expected - actual
    unexpected = actual - expected
    if missing:
        failures.append(f"missing expected candidates: {len(missing)}")
    if unexpected:
        failures.append(f"unexpected candidates: {len(unexpected)}")
    if failures:
        print("M4-C supplied-pack verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("M4-C supplied-pack verification passed: 36 exact audit candidates, no extras.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
