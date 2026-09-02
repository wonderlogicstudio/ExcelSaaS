from __future__ import annotations

import json
from pathlib import Path

from app.config import Settings
from app.recommendation_engine import enrich_scan_result
from app.scanner import scan_workbook


def _read_fixture(repository_root: Path, workbook_name: str) -> dict[str, object]:
    fixture_path = (
        repository_root
        / "samples"
        / "m3"
        / "fixtures"
        / f"{Path(workbook_name).stem}.scan-result.json"
    )
    return json.loads(fixture_path.read_text(encoding="utf-8"))


def _assert_fixture_matches_scanner(repository_root: Path, workbook_name: str) -> None:
    sample_path = repository_root / "samples" / "m3" / workbook_name
    fixture = _read_fixture(repository_root, workbook_name)
    result = enrich_scan_result(
        scan_workbook(sample_path.name, sample_path.read_bytes(), Settings())
    )
    fixture_result = fixture["scan_result"]

    assert fixture["fixture_metadata"]["generated_from"] == (
        f"samples/m3/{workbook_name}"
    )
    assert fixture["fixture_metadata"]["scanner_version"] == result.scanner_version
    assert fixture["fixture_metadata"]["rule_set_version"] == result.rule_set_version
    assert fixture_result["workbook"] == result.workbook.model_dump()
    assert fixture_result["summary"] == result.summary.model_dump()
    assert fixture_result["quote"] == result.quote.model_dump()

    fixture_findings = [
        {key: value for key, value in finding.items() if key != "id"}
        for finding in fixture_result["findings"]
    ]
    actual_findings = [
        {key: value for key, value in finding.items() if key != "id"}
        for finding in (item.model_dump(mode="json") for item in result.findings)
    ]
    assert fixture_findings == actual_findings


def test_m3_low_or_zero_findings_scenario_matches_real_scanner_result() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    _assert_fixture_matches_scanner(repository_root, "low-or-zero-findings.xlsx")

    fixture = _read_fixture(repository_root, "low-or-zero-findings.xlsx")
    assert fixture["scan_result"]["summary"]["issue_count"] == 0
    assert fixture["scan_result"]["findings"] == []


def test_m3_revalidation_scenario_has_removed_continued_and_new_real_signals() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    before_name = "revalidation-before.xlsx"
    after_name = "revalidation-after.xlsx"
    _assert_fixture_matches_scanner(repository_root, before_name)
    _assert_fixture_matches_scanner(repository_root, after_name)

    before = _read_fixture(repository_root, before_name)["scan_result"]["findings"]
    after = _read_fixture(repository_root, after_name)["scan_result"]["findings"]
    before_codes = {finding["rule_code"] for finding in before}
    after_codes = {finding["rule_code"] for finding in after}

    assert "FORMULA_EXTERNAL_REFERENCE" in before_codes - after_codes
    assert "NUMBER_STORED_AS_TEXT" in before_codes - after_codes
    assert "FORMULA_REF_ERROR" in before_codes & after_codes
    assert "FORMULA_VOLATILE" in after_codes - before_codes
