from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

from openpyxl import Workbook

from app.config import Settings
from app.recommendation_engine import build_finding_guidance, enrich_scan_result
from app.scanner import scan_workbook
from app.service_catalog import APPROVED_REPAIR, BETA_PRICE_RANGES, PRECISION_VERIFICATION


def test_recommendation_enrichment_preserves_scanner_rule_codes(
    risky_workbook_bytes: bytes,
) -> None:
    raw_result = scan_workbook("monthly-report.xlsx", risky_workbook_bytes, Settings())
    assert all(finding.guidance is None for finding in raw_result.findings)

    result = enrich_scan_result(raw_result)

    assert result.summary.information_only_count >= 1
    assert result.summary.repair_review_candidate_count == (
        result.summary.safe_candidate_count
        + result.summary.confirmation_required_count
        + result.summary.expert_review_count
    )
    assert all(finding.guidance is not None for finding in result.findings)
    assert [finding.rule_code for finding in result.findings] == [
        finding.rule_code for finding in raw_result.findings
    ]
    assert PRECISION_VERIFICATION.code in {
        finding.guidance.recommended_service_code for finding in result.findings
    }
    assert any(
        finding.guidance.recommended_service_code is None for finding in result.findings
    )

    numeric_text = next(
        finding for finding in result.findings if finding.rule_code == "NUMBER_STORED_AS_TEXT"
    )
    assert numeric_text.guidance is not None
    assert numeric_text.guidance.evidence_grade == "PATTERN_INFERENCE"
    assert numeric_text.guidance.action_category == "FIX_RECOMMENDED"
    assert numeric_text.guidance.repair_eligibility == "MANUAL_GUIDANCE_AVAILABLE"
    assert numeric_text.guidance.user_confirmation_required is False
    assert numeric_text.guidance.how_to_check_in_excel
    assert numeric_text.guidance.when_it_may_be_normal
    assert numeric_text.guidance.when_action_is_recommended
    assert "다시 검사" in numeric_text.guidance.recommended_next_action
    assert numeric_text.guidance.repair_readiness is not None
    assert numeric_text.guidance.repair_readiness.status == "REPAIR_CANDIDATE_AFTER_APPROVAL"
    assert numeric_text.guidance.repair_readiness.planned_service_codes == [
        PRECISION_VERIFICATION.code,
        APPROVED_REPAIR.code,
    ]
    assert "변환 미리보기" not in numeric_text.description
    assert "실제 집계 결과" in numeric_text.description

    formula_error = next(
        finding for finding in result.findings if finding.rule_code == "FORMULA_REF_ERROR"
    )
    assert formula_error.guidance is not None
    assert formula_error.guidance.action_category == "DEEP_VALIDATION_REQUIRED"
    assert formula_error.guidance.recommended_service_code == PRECISION_VERIFICATION.code

    information = next(
        finding for finding in result.findings if finding.rule_code == "FORMULA_VOLATILE"
    )
    assert information.guidance is not None
    assert information.guidance.action_category == "INFO_ONLY"
    assert information.guidance.recommended_service_code is None


def test_finding_key_is_stable_and_value_free(risky_workbook_bytes: bytes) -> None:
    first = scan_workbook("monthly-report.xlsx", risky_workbook_bytes, Settings())
    second = scan_workbook("monthly-report.xlsx", risky_workbook_bytes, Settings())

    first_keys = [finding.finding_key for finding in first.findings]
    second_keys = [finding.finding_key for finding in second.findings]

    assert first_keys == second_keys
    assert all(key for key in first_keys)
    assert all("1,800" not in key for key in first_keys if key)
    assert first.scanner_version == "0.1.3"
    assert first.rule_set_version == "2026.09.4"


def test_zero_finding_result_stays_empty_without_creating_guidance() -> None:
    workbook = Workbook()
    stream = BytesIO()
    workbook.save(stream)
    workbook.close()

    result = enrich_scan_result(scan_workbook("empty.xlsx", stream.getvalue(), Settings()))

    assert result.summary.issue_count == 0
    assert result.findings == []


def test_guidance_uses_only_known_rule_templates(risky_workbook_bytes: bytes) -> None:
    result = enrich_scan_result(
        scan_workbook("monthly-report.xlsx", risky_workbook_bytes, Settings())
    )
    unknown = result.findings[0].model_copy(update={"rule_code": "UNSUPPORTED_RULE"})
    guidance = build_finding_guidance(unknown)

    assert guidance.recommended_service_code == PRECISION_VERIFICATION.code
    assert "정적 검사 규칙" in guidance.detected_fact


def test_quote_uses_catalog_managed_beta_price_range(risky_workbook_bytes: bytes) -> None:
    result = enrich_scan_result(
        scan_workbook("monthly-report.xlsx", risky_workbook_bytes, Settings())
    )
    expected_range = BETA_PRICE_RANGES[result.quote.tier]

    assert expected_range is not None
    assert (result.quote.amount_min, result.quote.amount_max) == expected_range
    assert result.quote.service_status == "PLANNED"
    assert result.quote.planned_deliverables == list(PRECISION_VERIFICATION.planned_deliverables)
    assert result.quote.pricing_note is not None
    assert "결제는 진행되지 않습니다" in result.quote.pricing_note
    assert APPROVED_REPAIR.status == "PLANNED"
    assert "수정 후 재검증 보고서" in APPROVED_REPAIR.planned_deliverables


def test_demo_fixture_matches_real_sample_scan() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    fixture_path = repository_root / "apps" / "web" / "src" / "data" / "demo-result.fixture.json"
    sample_path = repository_root / "samples" / "demo-risky-workbook.xlsx"

    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    result = enrich_scan_result(
        scan_workbook(sample_path.name, sample_path.read_bytes(), Settings())
    )
    fixture_result = fixture["scan_result"]

    assert fixture["fixture_metadata"]["generated_from"] == "samples/demo-risky-workbook.xlsx"
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
