from __future__ import annotations

from io import BytesIO

from openpyxl import Workbook
from openpyxl.worksheet.table import Table, TableStyleInfo

from app.config import Settings
from app.formula_patterns import normalize_formula
from app.recommendation_engine import add_finding_guidance
from app.scanner import run_formula_audit, scan_workbook


def _scan_pattern_workbook(workbook: Workbook):
    stream = BytesIO()
    workbook.save(stream)
    workbook.close()
    return run_formula_audit(
        "formula-patterns.xlsx",
        stream.getvalue(),
        Settings(app_env="internal_beta", formula_pattern_audit_enabled=True),
    )


def _add_formula_region(sheet, *, column: str = "C", outlier_formula: str | None = None) -> None:
    sheet["A1"] = "Label"
    sheet["B1"] = "Input"
    sheet[f"{column}1"] = "Calculated"
    for row in range(2, 7):
        sheet[f"A{row}"] = f"Item {row}"
        sheet[f"B{row}"] = row
        sheet[f"{column}{row}"] = f"=SUM(B{row})"
    if outlier_formula is not None:
        sheet[f"{column}4"] = outlier_formula


def test_detects_supported_normalized_formula_pattern_outliers() -> None:
    workbook = Workbook()
    function_change = workbook.active
    function_change.title = "Function"
    _add_formula_region(function_change, outlier_formula="=AVERAGE(B4)")

    sheet_change = workbook.create_sheet("SheetReference")
    _add_formula_region(sheet_change)
    for row in range(2, 7):
        sheet_change[f"C{row}"] = f"=SUM(SourceA!B{row})"
    sheet_change["C4"] = "=SUM(SourceB!B4)"

    relative_change = workbook.create_sheet("RelativeReference")
    _add_formula_region(relative_change, outlier_formula="=SUM(B3)")

    range_change = workbook.create_sheet("RangeEnd")
    _add_formula_region(range_change)
    for row in range(2, 7):
        range_change[f"C{row}"] = f"=SUM(B{row}:D{row})"
    range_change["C4"] = "=SUM(B4:C4)"

    result = _scan_pattern_workbook(workbook)
    candidates = [
        finding
        for finding in result.candidates
        if finding.rule_code == "FORMULA_PATTERN_OUTLIER"
    ]

    assert {(finding.sheet, finding.cell) for finding in candidates} == {
        ("Function", "C4"),
        ("SheetReference", "C4"),
        ("RelativeReference", "C4"),
        ("RangeEnd", "C4"),
    }
    expected_subtypes = {
        "Function": "FUNCTION_PATTERN_DRIFT",
        "SheetReference": "REFERENCE_SHEET_DRIFT",
        "RelativeReference": "RELATIVE_REFERENCE_DRIFT",
        "RangeEnd": "RANGE_BOUNDARY_DRIFT",
    }
    for finding in candidates:
        assert finding.formula_pattern is not None
        assert finding.formula_pattern.pattern_type == "DOMINANT_NORMALIZED_PATTERN_OUTLIER"
        assert finding.formula_pattern.pattern_subtype == expected_subtypes[finding.sheet]
        assert finding.formula_pattern.neighbor_count >= 3
        assert finding.formula_pattern.evidence_locations
        assert finding.formula_pattern.comparison_locations
        assert finding.formula_pattern.evidence_summary
        assert finding.formula_pattern.dominant_pattern_summary
        assert finding.formula_pattern.current_pattern_summary
        assert finding.formula_pattern.normal_case_possibility
        assert finding.formula_pattern.current_pattern_id is not None
        assert finding.repair_class == "EXPERT_REVIEW"


def test_detects_constant_and_blank_inside_supported_formula_patterns() -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Gaps"
    _add_formula_region(sheet, column="C")
    sheet["C4"] = 999
    _add_formula_region(sheet, column="D")
    sheet["D4"] = None
    sheet["A4"] = "Item 4"

    result = _scan_pattern_workbook(workbook)
    candidates = [
        finding
        for finding in result.candidates
        if finding.rule_code == "FORMULA_PATTERN_GAP"
    ]

    assert {(finding.sheet, finding.cell) for finding in candidates} == {
        ("Gaps", "C4"),
        ("Gaps", "D4"),
    }
    assert all(finding.formula_pattern is not None for finding in candidates)
    assert {
        finding.cell: finding.formula_pattern.pattern_subtype
        for finding in candidates
        if finding.formula_pattern is not None
    } == {
        "C4": "CONSTANT_OVERRIDE_CANDIDATE",
        "D4": "BLANK_GAP_CANDIDATE",
    }


def test_excludes_headers_boundaries_summary_rows_blank_dividers_merged_and_tables() -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Boundary"

    _add_formula_region(sheet, column="C")
    sheet["C6"] = "=SUM(C2:C5)"  # total at a region boundary

    summary_sheet = workbook.create_sheet("Summary")
    _add_formula_region(summary_sheet, outlier_formula="=AVERAGE(B4)")
    summary_sheet["A4"] = "소계"

    divider_sheet = workbook.create_sheet("BlankDivider")
    _add_formula_region(divider_sheet)
    divider_sheet["C4"] = None
    divider_sheet["A4"] = None
    divider_sheet["B4"] = None  # a fully blank divider for this formula region

    merged_sheet = workbook.create_sheet("Merged")
    _add_formula_region(merged_sheet, outlier_formula="=AVERAGE(B4)")
    merged_sheet.merge_cells("C4:D4")

    table_sheet = workbook.create_sheet("Table")
    _add_formula_region(table_sheet, outlier_formula="=AVERAGE(B4)")
    table = Table(displayName="FormulaTable", ref="A1:C6")
    table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    table_sheet.add_table(table)

    result = _scan_pattern_workbook(workbook)
    pattern_findings = [
        finding for finding in result.candidates if finding.formula_pattern is not None
    ]

    assert pattern_findings == []


def test_does_not_treat_a_summary_marker_inside_a_formula_reference_as_a_summary_row() -> None:
    workbook = Workbook()
    source = workbook.active
    source.title = "총계정원장"
    for row in range(2, 7):
        source[f"A{row}"] = f"AC-{row}"
        source[f"B{row}"] = row * 100

    sheet = workbook.create_sheet("대사표")
    sheet["A1"] = "Account"
    sheet["B1"] = "Balance"
    for row in range(2, 7):
        sheet[f"A{row}"] = f"AC-{row}"
        sheet[f"B{row}"] = (
            "=SUMIFS('총계정원장'!$B$2:$B$6,'총계정원장'!$A$2:$A$6,"
            f"A{row})"
        )
    sheet["B4"] = "=SUMIFS('총계정원장'!$B$2:$B$6,'총계정원장'!$A$2:$A$6,A3)"

    result = _scan_pattern_workbook(workbook)

    assert {(finding.sheet, finding.cell, finding.rule_code) for finding in result.candidates} == {
        ("대사표", "B4", "FORMULA_PATTERN_OUTLIER")
    }


def test_pattern_audit_is_default_off_and_emits_value_free_stable_evidence() -> None:
    workbook = Workbook()
    sheet = workbook.active
    _add_formula_region(sheet, outlier_formula="=AVERAGE(B4)")
    stream = BytesIO()
    workbook.save(stream)
    workbook.close()
    payload = stream.getvalue()

    disabled = scan_workbook("patterns.xlsx", payload, Settings())
    still_isolated = scan_workbook(
        "patterns.xlsx",
        payload,
        Settings(app_env="internal_beta", formula_pattern_audit_enabled=True),
    )
    first = run_formula_audit(
        "patterns.xlsx",
        payload,
        Settings(app_env="internal_beta", formula_pattern_audit_enabled=True),
    )
    second = run_formula_audit(
        "patterns.xlsx",
        payload,
        Settings(app_env="internal_beta", formula_pattern_audit_enabled=True),
    )

    assert not any(finding.formula_pattern is not None for finding in disabled.findings)
    assert not any(finding.formula_pattern is not None for finding in still_isolated.findings)
    first_candidates = [finding for finding in first.candidates if finding.formula_pattern]
    second_candidates = [finding for finding in second.candidates if finding.formula_pattern]
    assert [finding.finding_key for finding in first_candidates] == [
        finding.finding_key for finding in second_candidates
    ]
    payload_json = first.model_dump_json()
    assert "=AVERAGE(B4)" not in payload_json
    evidence_json = "".join(
        finding.formula_pattern.model_dump_json()
        for finding in first_candidates
        if finding.formula_pattern is not None
    )
    # Finding IDs are UUIDs and can coincidentally contain a numeric literal.
    # Check value-free evidence, not the entire envelope, for literal leakage.
    assert "999" not in evidence_json

    enriched = add_finding_guidance(first.candidates)
    candidate = next(finding for finding in enriched if finding.formula_pattern)
    assert candidate.guidance is not None
    assert candidate.guidance.evidence_grade == "PATTERN_INFERENCE"
    assert candidate.guidance.action_category == "DEEP_VALIDATION_REQUIRED"
    assert candidate.guidance.repair_eligibility == "CURRENTLY_NOT_SUPPORTED"


def test_pattern_audit_skips_truncated_scans() -> None:
    workbook = Workbook()
    sheet = workbook.active
    _add_formula_region(sheet, outlier_formula="=AVERAGE(B4)")
    stream = BytesIO()
    workbook.save(stream)
    workbook.close()

    result = run_formula_audit(
        "truncated-patterns.xlsx",
        stream.getvalue(),
        Settings(app_env="internal_beta", formula_pattern_audit_enabled=True, scan_cell_limit=2),
    )

    assert result.status == "SKIPPED_TRUNCATED"
    assert result.candidates == []


def test_normalizes_supported_literals_without_retaining_values() -> None:
    workbook = Workbook()
    sheet = workbook.active
    first = sheet["C2"]
    second = sheet["C3"]
    first.value = '=IF(A2="internal-one",B2*0.1,0)'
    second.value = '=IF(A3="internal-two",B3*0.9,9)'

    first_signature = normalize_formula(first.value, first)
    second_signature = normalize_formula(second.value, second)

    assert first_signature is not None
    assert first_signature == second_signature
    assert "internal-one" not in first_signature
    assert "0.1" not in first_signature
    assert normalize_formula("=SUM(B2,1)", first) is None
