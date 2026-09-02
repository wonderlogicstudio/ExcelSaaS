from __future__ import annotations

import json
from pathlib import Path

from openpyxl.utils.cell import range_boundaries

from app.config import Settings
from app.scanner import FORMULA_AUDIT_RULE_SET_VERSION, run_formula_audit, scan_workbook

ROOT = Path(__file__).resolve().parents[3]
SUPPLIED_PACK_ROOT = (
    ROOT
    / "samples"
    / "WorkbookCare_M4C_Sample_Pack_2026-09-01"
    / "WorkbookCare_M4C_Sample_Pack"
)
CORPUS_ROOT = SUPPLIED_PACK_ROOT / "samples"
MANIFEST_PATH = SUPPLIED_PACK_ROOT / "expected" / "m4c_manifest.json"
AUDIT_SETTINGS = Settings(
    app_env="internal_beta",
    formula_pattern_audit_enabled=True,
    scan_cell_limit=250_000,
    finding_limit=5_000,
)


def _base_contract(result) -> dict[str, object]:
    return {
        "workbook": result.workbook.model_dump(),
        "summary": result.summary.model_dump(),
        "quote": result.quote.model_dump(),
        "limitations": result.limitations,
        "findings": [
            finding.model_dump(exclude={"id"})
            for finding in result.findings
        ],
    }


def _candidate_key(finding) -> tuple[str | None, str | None, str, str | None]:
    evidence = finding.formula_pattern
    return (
        finding.sheet,
        finding.cell,
        finding.rule_code,
        evidence.pattern_subtype if evidence else None,
    )


def _is_in_range(cell: str | None, cell_or_range: str) -> bool:
    if cell is None:
        return False
    min_column, min_row, max_column, max_row = range_boundaries(cell_or_range)
    from openpyxl.utils.cell import coordinate_to_tuple

    row, column = coordinate_to_tuple(cell)
    return min_row <= row <= max_row and min_column <= column <= max_column


def test_m4c_practical_corpus_matches_targets_without_normal_exception_candidates() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
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
    normal_exceptions = manifest["normal_exceptions"]
    actual: set[tuple[str, str | None, str | None, str, str | None]] = set()

    for scenario in manifest["scenarios"]:
        filename = scenario["file"]
        payload = (CORPUS_ROOT / filename).read_bytes()
        base_without_audit = scan_workbook(filename, payload, Settings())
        base_with_audit_enabled = scan_workbook(filename, payload, AUDIT_SETTINGS)
        assert _base_contract(base_without_audit) == _base_contract(base_with_audit_enabled)
        assert not any(
            finding.rule_code.startswith("FORMULA_PATTERN_")
            for finding in base_with_audit_enabled.findings
        )

        result = run_formula_audit(filename, payload, AUDIT_SETTINGS)
        assert result.status == "COMPLETED"
        assert result.rule_set_version == FORMULA_AUDIT_RULE_SET_VERSION
        for finding in result.candidates:
            actual.add((filename, *_candidate_key(finding)))
            for normal in normal_exceptions:
                if normal["file"] != filename or normal["sheet"] != finding.sheet:
                    continue
                assert not _is_in_range(finding.cell, normal["cell"])

    assert actual == expected
    assert len(actual) == 36
