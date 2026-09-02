"""Conservative, value-free formula-pattern candidate detection for M4-A.

This module does not evaluate formulas, infer business intent, produce a
replacement formula, or alter a workbook. It recognizes only a narrow subset
of A1-style formulas that can be normalized without retaining formula text.
Any unsupported syntax or likely structural exception is excluded.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from hashlib import sha256

from openpyxl.cell.cell import Cell
from openpyxl.formula import Tokenizer
from openpyxl.utils import column_index_from_string, get_column_letter
from openpyxl.utils.cell import range_boundaries
from openpyxl.worksheet.worksheet import Worksheet

from .models import FormulaPatternEvidence

_CELL_REFERENCE = re.compile(
    r"^(?P<column_absolute>\$?)(?P<column>[A-Za-z]{1,3})"
    r"(?P<row_absolute>\$?)(?P<row>[1-9]\d*)$"
)
_SUMMARY_MARKERS = (
    "subtotal",
    "total",
    "grand total",
    "소계",
    "합계",
    "총계",
    "조정",
    "보정",
    "adjustment",
    "manual",
)
_STRUCTURAL_TOKEN_TYPES = {
    "FUNC",
    "PAREN",
    "SEP",
    # openpyxl Tokenizer uses the long names below. The abbreviated names are
    # retained for compatibility with older tokenizer variants.
    "OPERATOR-INFIX",
    "OPERATOR-PREFIX",
    "OPERATOR-POSTFIX",
    "OP_IN",
    "OP_PRE",
    "OP_POST",
}
_FUNCTION_SIGNATURE = re.compile(r"(?P<name>[A-Z][A-Z0-9_.]*)\(")
_REFERENCE_SIGNATURE = re.compile(
    r"REF\((?:(?:SHEET\((?P<sheet>[^)]*)\)!)?)(?P<coordinates>[^)]*)\)"
)


@dataclass(frozen=True, slots=True)
class FormulaPatternCandidate:
    rule_code: str
    title: str
    description: str
    sheet: str
    cell: str
    evidence: FormulaPatternEvidence


@dataclass(frozen=True, slots=True)
class FormulaPatternWorksheetAudit:
    """Private execution metadata plus candidates for one worksheet.

    The support count is used only to choose a conservative execution outcome;
    neither formula text nor cell values are retained in a result payload.
    """

    candidates: list[FormulaPatternCandidate]
    supported_formula_count: int


@dataclass(frozen=True, slots=True)
class _NormalizedFormula:
    cell: Cell
    signature: str
    pattern_id: str


@dataclass(frozen=True, slots=True)
class _PatternProfile:
    """Private comparison metadata. It is never returned in an API payload."""

    functions: tuple[str, ...]
    sheets: tuple[str, ...]
    absolute_styles: tuple[str, ...]
    absolute_coordinates: tuple[str, ...]
    range_shapes: tuple[int, ...]
    relative_shapes: tuple[str, ...]


def _formula_text(cell: Cell) -> str | None:
    value = cell.value
    if cell.data_type == "f" and isinstance(value, str):
        return value
    if isinstance(value, str) and value.startswith("="):
        return value
    return None


def _pattern_id(signature: str) -> str:
    return sha256(signature.encode("utf-8")).hexdigest()[:16]


def _normalise_reference(reference: str, *, origin_row: int, origin_column: int) -> str | None:
    """Represent a supported A1 reference relative to its formula cell."""
    if "[" in reference or "]" in reference:
        return None

    sheet_prefix = ""
    coordinate_text = reference
    if "!" in reference:
        sheet_name, coordinate_text = reference.rsplit("!", 1)
        if not sheet_name:
            return None
        sheet_prefix = f"SHEET({sheet_name.casefold()})!"

    parts = coordinate_text.split(":")
    if len(parts) not in {1, 2} or not all(parts):
        return None

    normalised_parts: list[str] = []
    for part in parts:
        match = _CELL_REFERENCE.fullmatch(part)
        if match is None:
            return None
        try:
            column_index = column_index_from_string(match.group("column").upper())
        except ValueError:
            return None
        row_index = int(match.group("row"))

        if match.group("column_absolute"):
            column_signature = f"C${column_index}"
        else:
            column_signature = f"C[{column_index - origin_column}]"
        if match.group("row_absolute"):
            row_signature = f"R${row_index}"
        else:
            row_signature = f"R[{row_index - origin_row}]"
        normalised_parts.append(f"{column_signature}{row_signature}")

    return sheet_prefix + ":".join(normalised_parts)


def normalize_formula(formula: str, origin: Cell) -> str | None:
    """Return a safe normalized signature, or None when parsing is uncertain.

    Literal operands are represented by their value-free token category so
    repeated business formulas such as ``IF`` and ``IFERROR`` remain
    comparable without retaining a literal value. Array, table,
    external-workbook, and named-range operands remain unsupported. The
    returned signature is used only to create a one-way pattern ID and is
    never emitted.
    """
    if not formula.startswith("=") or "[" in formula or "]" in formula:
        return None
    try:
        tokens = Tokenizer(formula).items
    except Exception:
        return None

    canonical: list[str] = []
    has_reference = False
    function_stack: list[str] = []
    for token in tokens:
        if token.type == "WSPACE":
            continue
        if token.type == "FUNC":
            if token.subtype == "OPEN":
                function_stack.append(token.value[:-1].upper())
            elif token.subtype == "CLOSE" and function_stack:
                function_stack.pop()
            canonical.append(token.value.upper())
            continue
        if token.type == "OPERAND":
            if token.subtype == "RANGE":
                normalized_reference = _normalise_reference(
                    token.value,
                    origin_row=origin.row,
                    origin_column=origin.column,
                )
                if normalized_reference is None:
                    return None
                canonical.append(f"REF({normalized_reference})")
                has_reference = True
                continue
            literal_category = {
                "NUMBER": "NUMBER",
                "TEXT": "TEXT",
                "LOGICAL": "LOGICAL",
                "ERROR": "ERROR",
            }.get(token.subtype)
            if literal_category is None:
                return None
            if function_stack and function_stack[-1] in {"SUM", "AVERAGE"}:
                # A static aggregate operand can be an intentional adjustment.
                # Keep this narrow legacy syntax outside the M4-C comparison
                # surface until it has its own target/normal quality gate.
                return None
            canonical.append(f"LITERAL({literal_category})")
            continue
        if token.type in _STRUCTURAL_TOKEN_TYPES:
            canonical.append(token.value.upper())
            continue
        return None

    if not has_reference or not canonical:
        return None
    return "".join(canonical)


def _table_bounds(worksheet: Worksheet) -> list[tuple[int, int, int, int]]:
    bounds: list[tuple[int, int, int, int]] = []
    for table in worksheet.tables.values():
        try:
            bounds.append(range_boundaries(table.ref))
        except (TypeError, ValueError):
            continue
    return bounds


def _is_inside_table(
    *, row: int, column: int, table_bounds: list[tuple[int, int, int, int]]
) -> bool:
    return any(
        min_column <= column <= max_column and min_row <= row <= max_row
        for min_column, min_row, max_column, max_row in table_bounds
    )


def _is_merged(worksheet: Worksheet, cell: Cell) -> bool:
    return any(cell.coordinate in merged_range for merged_range in worksheet.merged_cells.ranges)


def _is_summary_or_manual_row(worksheet: Worksheet, row: int, cells: tuple[Cell, ...]) -> bool:
    if row <= 1 or worksheet.row_dimensions[row].hidden:
        return True
    for cell in cells:
        # A formula may legitimately refer to a worksheet named "총계..." or
        # "Adjustment...". Summary markers describe row labels, not formula
        # source text; inspecting formulas here would exclude every data row
        # in that pattern region.
        if _formula_text(cell) is not None:
            continue
        if isinstance(cell.value, str):
            text = cell.value.strip().casefold()
            if text and any(marker in text for marker in _SUMMARY_MARKERS):
                return True
    return False


def _summary_rows(worksheet: Worksheet) -> set[int]:
    """Find known summary/manual rows in one worksheet traversal.

    ``worksheet[row]`` performs repeated slice construction on large sheets.
    Using the already materialized row from ``iter_rows`` preserves the exact
    exclusion rules while keeping the audit linear in worksheet size.
    """
    return {
        row
        for row, cells in enumerate(worksheet.iter_rows(), start=1)
        if _is_summary_or_manual_row(worksheet, row, cells)
    }


def _is_excluded_location(
    worksheet: Worksheet,
    cell: Cell,
    table_bounds: list[tuple[int, int, int, int]],
    summary_rows: set[int],
) -> bool:
    return (
        cell.row in summary_rows
        or _is_merged(worksheet, cell)
        or _is_inside_table(row=cell.row, column=cell.column, table_bounds=table_bounds)
    )


def _blank_row_has_context(worksheet: Worksheet, *, row: int, target_column: int) -> bool:
    """Avoid treating a fully empty separator row as a missing formula."""
    return any(
        cell.column != target_column and cell.value is not None
        for cell in worksheet[row]
    )


def _contiguous_formula_runs(items: list[_NormalizedFormula]) -> list[list[_NormalizedFormula]]:
    if not items:
        return []
    runs: list[list[_NormalizedFormula]] = [[items[0]]]
    for item in items[1:]:
        if item.cell.row == runs[-1][-1].cell.row + 1:
            runs[-1].append(item)
        else:
            runs.append([item])
    return runs


def _supporting_items(
    items: list[_NormalizedFormula],
    dominant_signature: str,
    candidate_row: int,
    worksheet: Worksheet,
    table_bounds: list[tuple[int, int, int, int]],
    summary_rows: set[int],
) -> list[_NormalizedFormula]:
    return [
        item
        for item in items
        if item.cell.row != candidate_row
        and item.signature == dominant_signature
        and not _is_excluded_location(worksheet, item.cell, table_bounds, summary_rows)
    ]


def _region(column: int, rows: list[int]) -> str:
    return f"{get_column_letter(column)}{min(rows)}:{get_column_letter(column)}{max(rows)}"


def _pattern_profile(signature: str) -> _PatternProfile:
    """Extract only structural comparison facts from a private signature.

    The profile intentionally drops formula text, actual cell values, and the
    specific sheet identifiers before a Finding is created.
    """
    references = list(_REFERENCE_SIGNATURE.finditer(signature))
    functions = tuple(
        match.group("name")
        for match in _FUNCTION_SIGNATURE.finditer(signature)
        # ``REF`` is the normalizer's internal marker, not an Excel function.
        if match.group("name") != "REF"
    )
    coordinates = tuple(match.group("coordinates") for match in references)
    return _PatternProfile(
        functions=functions,
        sheets=tuple(
            _pattern_id(match.group("sheet")) if match.group("sheet") else "LOCAL"
            for match in references
        ),
        absolute_styles=tuple(
            "ABSOLUTE" if "$" in coordinate else "RELATIVE" for coordinate in coordinates
        ),
        absolute_coordinates=tuple(
            "|".join(re.findall(r"[CR]\$\d+", coordinate)) for coordinate in coordinates
        ),
        range_shapes=tuple(coordinate.count(":") + 1 for coordinate in coordinates),
        relative_shapes=coordinates,
    )


def _outlier_explanation(
    dominant_signature: str, current_signature: str
) -> tuple[str, str, str, str, str]:
    """Return a conservative, source-free subtype and display summaries."""
    dominant = _pattern_profile(dominant_signature)
    current = _pattern_profile(current_signature)
    normal_case = "소계·예외 계산 또는 업무상 의도된 다른 수식일 수 있습니다."
    dominant_summary = "주변 수식은 같은 함수와 참조 구조가 반복되는 패턴입니다."

    if dominant.functions != current.functions:
        return (
            "FUNCTION_PATTERN_DRIFT",
            "대상 수식의 함수 구성이 주변 반복 패턴과 다릅니다.",
            dominant_summary,
            "대상 수식은 주변과 다른 함수 구성을 사용합니다.",
            normal_case,
        )
    same_reference_arity = len(dominant.relative_shapes) == len(current.relative_shapes)
    changed_reference_pairs = (
        [
            (dominant_reference, current_reference)
            for dominant_reference, current_reference in zip(
                dominant.relative_shapes, current.relative_shapes, strict=True
            )
            if dominant_reference != current_reference
        ]
        if same_reference_arity
        else []
    )

    if same_reference_arity and dominant.sheets != current.sheets:
        return (
            "REFERENCE_SHEET_DRIFT",
            "대상 수식의 참조 시트 사용 방식이 주변 반복 패턴과 다릅니다.",
            dominant_summary,
            "대상 수식은 주변과 다른 참조 시트 사용 방식을 보입니다.",
            normal_case,
        )
    if same_reference_arity and dominant.absolute_styles != current.absolute_styles:
        return (
            "ABSOLUTE_REFERENCE_DRIFT",
            "대상 수식의 절대·상대 참조 방식이 주변 반복 패턴과 다릅니다.",
            dominant_summary,
            "대상 수식은 주변과 다른 절대·상대 참조 방식을 사용합니다.",
            normal_case,
        )
    if same_reference_arity and (
        dominant.absolute_coordinates != current.absolute_coordinates
        and any(dominant.absolute_coordinates)
    ):
        return (
            "REFERENCE_CELL_DRIFT",
            "대상 수식의 고정 참조 위치가 주변 반복 패턴과 다릅니다.",
            dominant_summary,
            "대상 수식은 주변과 다른 고정 참조 위치를 사용합니다.",
            normal_case,
        )
    if changed_reference_pairs and any(
        ":" in dominant_reference or ":" in current_reference
        for dominant_reference, current_reference in changed_reference_pairs
    ):
        return (
            "RANGE_BOUNDARY_DRIFT",
            "대상 수식의 범위 끝 위치가 주변 반복 패턴과 다릅니다.",
            dominant_summary,
            "대상 수식은 주변과 다른 범위 끝 위치를 사용합니다.",
            normal_case,
        )
    if dominant.relative_shapes != current.relative_shapes:
        return (
            "RELATIVE_REFERENCE_DRIFT",
            "대상 수식의 상대 참조 위치가 주변 반복 패턴과 다릅니다.",
            dominant_summary,
            "대상 수식은 주변과 다른 상대 참조 위치를 사용합니다.",
            normal_case,
        )
    return (
        "GENERIC_PATTERN_DRIFT",
        "대상 수식의 구조가 주변 반복 패턴과 다릅니다.",
        dominant_summary,
        "대상 수식은 주변과 다른 수식 구조를 사용합니다.",
        normal_case,
    )


def _candidate_evidence(
    *,
    pattern_type: str,
    region: str,
    dominant_signature: str,
    current_signature: str | None,
    supporting_cells: list[Cell],
    detection_basis: str,
    candidate_cell: Cell | None = None,
) -> FormulaPatternEvidence:
    comparison_locations = [cell.coordinate for cell in supporting_cells[:4]]
    if pattern_type == "FORMULA_GAP_OR_CONSTANT":
        is_blank = candidate_cell is not None and candidate_cell.value is None
        subtype = "BLANK_GAP_CANDIDATE" if is_blank else "CONSTANT_OVERRIDE_CANDIDATE"
        evidence_summary = (
            "반복 수식 사이의 대상 셀이 비어 있습니다."
            if is_blank
            else "반복 수식 사이의 대상 셀에 수식이 아닌 값이 있습니다."
        )
        current_summary = (
            "대상 셀은 빈 셀입니다."
            if is_blank
            else "대상 셀에는 수식이 아닌 값이 있습니다."
        )
        normal_case = "의도된 수동 입력·구분 행 또는 예외 값일 수 있습니다."
    elif current_signature is not None:
        (
            subtype,
            evidence_summary,
            dominant_summary,
            current_summary,
            normal_case,
        ) = _outlier_explanation(dominant_signature, current_signature)
    else:
        subtype = "GENERIC_PATTERN_DRIFT"
        evidence_summary = "주변 반복 수식과 다른 구조 후보를 확인했습니다."
        dominant_summary = "주변 수식은 같은 구조가 반복되는 패턴입니다."
        current_summary = None
        normal_case = "업무상 의도된 예외 구조일 수 있습니다."

    if pattern_type == "FORMULA_GAP_OR_CONSTANT":
        dominant_summary = "주변 수식은 같은 구조가 반복되는 패턴입니다."

    return FormulaPatternEvidence(
        pattern_type=pattern_type,  # type: ignore[arg-type]
        formula_region=region,
        dominant_pattern_id=_pattern_id(dominant_signature),
        current_pattern_id=_pattern_id(current_signature) if current_signature else None,
        neighbor_count=len(supporting_cells),
        evidence_locations=comparison_locations,
        detection_basis=detection_basis,
        current_limitations=[
            "수식 계산 결과, 업무 규칙, 의도된 예외 계산은 확인하지 않았습니다.",
            "지원하는 A1 참조 수식의 제한된 주변 패턴만 비교했습니다.",
            "수정 수식 생성·적용이나 자동 수정 가능 여부는 제공하지 않습니다.",
        ],
        pattern_subtype=subtype,  # type: ignore[arg-type]
        evidence_summary=evidence_summary,
        dominant_pattern_summary=dominant_summary,
        current_pattern_summary=current_summary,
        comparison_locations=comparison_locations,
        normal_case_possibility=normal_case,
    )


def inspect_worksheet_formula_patterns(worksheet: Worksheet) -> FormulaPatternWorksheetAudit:
    """Return conservative formula candidates for a single worksheet.

    The comparison is column-local and requires three or more surrounding
    formulas with one dominant normalized pattern. This deliberately misses
    many possible inconsistencies in exchange for lower false-positive risk.
    """
    table_bounds = _table_bounds(worksheet)
    summary_rows = _summary_rows(worksheet)
    normalized_by_column: dict[int, list[_NormalizedFormula]] = defaultdict(list)
    supported_formula_count = 0

    for row in worksheet.iter_rows():
        for cell in row:
            formula = _formula_text(cell)
            if formula is None or _is_excluded_location(
                worksheet, cell, table_bounds, summary_rows
            ):
                continue
            signature = normalize_formula(formula, cell)
            if signature is not None:
                supported_formula_count += 1
                normalized_by_column[cell.column].append(
                    _NormalizedFormula(
                        cell=cell,
                        signature=signature,
                        pattern_id=_pattern_id(signature),
                    )
                )

    candidates: list[FormulaPatternCandidate] = []
    emitted: set[tuple[str, str]] = set()
    for column, normalized_items in normalized_by_column.items():
        normalized_items.sort(key=lambda item: item.cell.row)
        for run in _contiguous_formula_runs(normalized_items):
            if len(run) < 4:
                continue
            counts = Counter(item.signature for item in run)
            dominant_signature, dominant_count = counts.most_common(1)[0]
            if dominant_count < 3 or sum(count == dominant_count for count in counts.values()) != 1:
                continue

            by_row = {item.cell.row: item for item in run}
            for item in run[1:-1]:
                if item.signature == dominant_signature:
                    continue
                above = by_row.get(item.cell.row - 1)
                below = by_row.get(item.cell.row + 1)
                if above is None or below is None:
                    continue
                if above.signature != dominant_signature or below.signature != dominant_signature:
                    continue
                supporting = _supporting_items(
                    run,
                    dominant_signature,
                    item.cell.row,
                    worksheet,
                    table_bounds,
                    summary_rows,
                )
                if len(supporting) < 3:
                    continue
                key = ("FORMULA_PATTERN_OUTLIER", item.cell.coordinate)
                if key in emitted:
                    continue
                emitted.add(key)
                candidates.append(
                    FormulaPatternCandidate(
                        rule_code="FORMULA_PATTERN_OUTLIER",
                        title="주변 수식과 다른 패턴 후보가 있습니다.",
                        description=(
                            "같은 열의 연속 수식 영역에서 주변 수식과 다른 정규화 패턴을 "
                            "확인했습니다. 업무적으로 정상일 수 있으므로 사용자 확인과 "
                            "정밀검증이 필요합니다."
                        ),
                        sheet=worksheet.title,
                        cell=item.cell.coordinate,
                        evidence=_candidate_evidence(
                            pattern_type="DOMINANT_NORMALIZED_PATTERN_OUTLIER",
                            region=_region(column, [entry.cell.row for entry in run]),
                            dominant_signature=dominant_signature,
                            current_signature=item.signature,
                            supporting_cells=[entry.cell for entry in supporting],
                            detection_basis=(
                                "같은 열의 연속 수식 영역에서 최소 3개의 주변 수식이 같은 "
                                "정규화 패턴을 보이고, 대상 셀만 다른 패턴입니다."
                            ),
                            candidate_cell=item.cell,
                        ),
                    )
                )

        by_row = {item.cell.row: item for item in normalized_items}
        for row in range(2, worksheet.max_row):
            candidate_cell = worksheet.cell(row=row, column=column)
            if _formula_text(candidate_cell) is not None or _is_excluded_location(
                worksheet, candidate_cell, table_bounds, summary_rows
            ):
                continue
            if candidate_cell.value is None and not _blank_row_has_context(
                worksheet, row=row, target_column=column
            ):
                continue
            above = by_row.get(row - 1)
            below = by_row.get(row + 1)
            if above is None or below is None or above.signature != below.signature:
                continue
            supporting = [above, below]
            for nearby_row in (row - 2, row + 2):
                nearby = by_row.get(nearby_row)
                if nearby is not None and nearby.signature == above.signature:
                    supporting.append(nearby)
            supporting = [
                item
                for item in supporting
                if not _is_excluded_location(
                    worksheet, item.cell, table_bounds, summary_rows
                )
            ]
            if len(supporting) < 3:
                continue
            key = ("FORMULA_PATTERN_GAP", candidate_cell.coordinate)
            if key in emitted:
                continue
            emitted.add(key)
            candidates.append(
                FormulaPatternCandidate(
                    rule_code="FORMULA_PATTERN_GAP",
                    title="반복 수식 영역의 수식 누락 또는 상수 덮어쓰기 후보가 있습니다.",
                    description=(
                        "같은 열의 주변 수식 패턴 사이에서 대상 셀에 수식이 없습니다. "
                        "의도된 상수나 구분 행일 수 있으므로 사용자 확인과 정밀검증이 필요합니다."
                    ),
                    sheet=worksheet.title,
                    cell=candidate_cell.coordinate,
                    evidence=_candidate_evidence(
                        pattern_type="FORMULA_GAP_OR_CONSTANT",
                        region=_region(column, [item.cell.row for item in supporting] + [row]),
                        dominant_signature=above.signature,
                        current_signature=None,
                        supporting_cells=[
                            item.cell
                            for item in sorted(
                                supporting, key=lambda entry: entry.cell.row
                            )
                        ],
                        detection_basis=(
                            "대상 셀의 바로 위·아래 수식과 최소 3개의 주변 수식이 같은 "
                            "정규화 패턴을 보이지만 대상 셀에는 수식이 없습니다."
                        ),
                        candidate_cell=candidate_cell,
                    ),
                )
            )

    return FormulaPatternWorksheetAudit(
        candidates=candidates,
        supported_formula_count=supported_formula_count,
    )


def audit_worksheet_formula_patterns(worksheet: Worksheet) -> list[FormulaPatternCandidate]:
    """Return candidates while preserving the original M4-A helper contract."""

    return inspect_worksheet_formula_patterns(worksheet).candidates
