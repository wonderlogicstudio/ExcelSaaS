from __future__ import annotations

from app.config import Settings
from app.scanner import scan_workbook


def test_scan_finds_high_value_workbook_risks(risky_workbook_bytes: bytes) -> None:
    result = scan_workbook("monthly-report.xlsx", risky_workbook_bytes, Settings())

    codes = {finding.rule_code for finding in result.findings}
    assert "FORMULA_REF_ERROR" in codes
    assert "FORMULA_VOLATILE" in codes
    assert "FORMULA_WHOLE_COLUMN_REFERENCE" in codes
    assert "FORMULA_DEEP_NESTING" in codes
    assert "FORMULA_EXTERNAL_REFERENCE" in codes
    assert "NUMBER_STORED_AS_TEXT" in codes
    assert "SHEET_HIDDEN" in codes
    assert "SHEET_VERY_HIDDEN" in codes

    assert result.workbook.sheet_count == 3
    assert result.workbook.hidden_sheet_count == 1
    assert result.workbook.very_hidden_sheet_count == 1
    assert result.workbook.formula_count == 5
    assert result.workbook.external_link_count >= 1
    assert result.summary.critical_count >= 1
    assert result.summary.warning_count >= 3
    assert result.summary.safe_candidate_count >= 1
    assert result.quote.currency == "KRW"
    assert result.filename == "monthly-report.xlsx"


def test_scan_marks_xlsm_as_expert_review(risky_workbook_bytes: bytes) -> None:
    result = scan_workbook("macro-report.xlsm", risky_workbook_bytes, Settings())

    assert result.workbook.has_macros is True
    assert result.quote.status == "EXPERT_REVIEW"
    assert result.quote.amount is None
    assert any(finding.rule_code == "FILE_MACRO_ENABLED" for finding in result.findings)


def test_scan_respects_cell_limit(risky_workbook_bytes: bytes) -> None:
    result = scan_workbook(
        "limited.xlsx",
        risky_workbook_bytes,
        Settings(scan_cell_limit=2),
    )

    assert result.workbook.scan_truncated is True
    assert result.workbook.scanned_cell_count == 2
    assert any(
        finding.rule_code == "SCAN_CELL_LIMIT_REACHED" for finding in result.findings
    )


def test_structured_table_reference_is_not_misclassified_as_external() -> None:
    from io import BytesIO

    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet["A1"] = "=SUM(Table1[Amount])"
    stream = BytesIO()
    workbook.save(stream)
    workbook.close()

    result = scan_workbook("table-formula.xlsx", stream.getvalue(), Settings())

    assert result.workbook.external_link_count == 0
    assert not any(
        finding.rule_code == "FORMULA_EXTERNAL_REFERENCE" for finding in result.findings
    )


def test_leading_zero_identifier_is_not_a_numeric_repair_candidate() -> None:
    from io import BytesIO

    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet["A1"] = "Account"
    sheet["A2"] = 1001
    sheet["A3"] = 1002
    sheet["A4"] = 1003
    sheet["A5"] = "001004"
    stream = BytesIO()
    workbook.save(stream)
    workbook.close()

    result = scan_workbook("identifiers.xlsx", stream.getvalue(), Settings())

    assert not any(finding.rule_code == "NUMBER_STORED_AS_TEXT" for finding in result.findings)
