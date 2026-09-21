from __future__ import annotations

import csv
from collections import Counter, defaultdict
from math import ceil
from pathlib import Path
from statistics import mean, median
from typing import Any

from openpyxl.utils.cell import coordinate_to_tuple, range_boundaries

from .engine_worker import _status_from_parts
from .runner import _classified_record, _completion
from .schema import (
    IN_SCOPE_BASE_RULES,
    DatasetManifest,
    ExpectedFinding,
    WorkbookTruth,
    read_json,
    write_json,
)


def _actual_findings(raw: dict[str, Any]) -> list[dict[str, Any]]:
    if _status_from_parts(raw.get("base"), raw.get("audit")) not in {"COMPLETED", "PARTIAL"}:
        return []
    rows: list[dict[str, Any]] = []
    for finding in (raw.get("base") or {}).get("findings", []):
        rows.append({"source": "base", "sheet": finding.get("sheet"), "cell": finding.get("cell"), "rule_code": finding.get("rule_code"), "pattern_subtype": None, "severity": finding.get("severity"), "repair_class": finding.get("repair_class"), "raw": finding})
    for finding in (raw.get("audit") or {}).get("candidates", []):
        evidence = finding.get("formula_pattern") or {}
        rows.append({"source": "m4_candidate", "sheet": finding.get("sheet"), "cell": finding.get("cell"), "rule_code": finding.get("rule_code"), "pattern_subtype": evidence.get("pattern_subtype"), "severity": finding.get("severity"), "repair_class": finding.get("repair_class"), "raw": finding})
    return rows


def _bounds(cell_or_range: str | None) -> tuple[int, int, int, int] | None:
    if not cell_or_range:
        return None
    try:
        if ":" in cell_or_range:
            return range_boundaries(cell_or_range)
        row, col = coordinate_to_tuple(cell_or_range)
        return (col, row, col, row)
    except Exception:
        return None


def _location_overlaps(expected_cell: str, actual_cell: str | None) -> bool:
    expected = _bounds(expected_cell)
    actual = _bounds(actual_cell)
    if expected is None or actual is None:
        return False
    e_min_col, e_min_row, e_max_col, e_max_row = expected
    a_min_col, a_min_row, a_max_col, a_max_row = actual
    return not (e_max_col < a_min_col or a_max_col < e_min_col or e_max_row < a_min_row or a_max_row < e_min_row)


def _normalize_location(cell_or_range: str | None) -> str:
    bounds = _bounds(cell_or_range)
    if bounds is None:
        return f"malformed:{cell_or_range or ''}"
    min_col, min_row, max_col, max_row = bounds
    return f"{min_col}:{min_row}:{max_col}:{max_row}"


def _canonical_key(actual: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        str(actual.get("source") or ""),
        str(actual.get("sheet") or ""),
        _normalize_location(actual.get("cell")),
        str(actual.get("rule_code") or ""),
        str(actual.get("pattern_subtype") or ""),
    )


def _dedupe_actuals(actual: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    seen: set[tuple[str, str, str, str, str]] = set()
    unique: list[dict[str, Any]] = []
    duplicates = 0
    for item in actual:
        key = _canonical_key(item)
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        unique.append(item)
    return unique, duplicates


def _matches(expected: ExpectedFinding, actual: dict[str, Any]) -> bool:
    if expected.sheet != actual.get("sheet") or not _location_overlaps(expected.cell, actual.get("cell")):
        return False
    if expected.rule_code and expected.rule_code != actual.get("rule_code"):
        return False
    if expected.pattern_subtype and expected.pattern_subtype != actual.get("pattern_subtype"):
        return False
    if expected.kind == "m4_candidate" and actual.get("source") != "m4_candidate":
        return False
    if expected.kind == "confirmed_error" and actual.get("source") != "base":
        return False
    return True


def _normal_region_cells(truth: WorkbookTruth) -> set[tuple[str, str]]:
    return {(spec.sheet, spec.cell) for spec in truth.formula_cells if spec.role in {"detail", "normal_exception"} and spec.supported_by_current_m4}


def _ambiguous_or_unsupported_cells(truth: WorkbookTruth) -> set[tuple[str, str]]:
    cells = {(item.sheet, item.cell) for item in truth.expected_findings if item.kind in {"out_of_scope", "user_confirmation"}}
    for spec in truth.formula_cells:
        if (not spec.supported_by_current_m4) or spec.role in {"subtotal", "exploratory"}:
            cells.add((spec.sheet, spec.cell))
    return cells


def _group_key(truth: WorkbookTruth) -> tuple[str, str, str, str, str]:
    return (truth.business_domain, truth.structural_family, truth.mutation_type or "normal", truth.split, truth.family_id)


def _overlaps_scored_expected(candidate: dict[str, Any], expected: list[ExpectedFinding]) -> bool:
    return any(
        item.sheet == candidate.get("sheet") and _location_overlaps(item.cell, candidate.get("cell"))
        for item in expected
    )


def _percent(numerator: int, denominator: int) -> float | str:
    return "N/A" if denominator == 0 else round(numerator / denominator, 4)


def score_results(*, manifest: DatasetManifest, dataset_root: Path, run_root: Path) -> dict[str, Any]:
    del dataset_root
    status = read_json(run_root / "engine_status.json")
    by_id = {record["workbook_id"]: record for record in status.get("records", [])}
    classified_by_id = {record["workbook_id"]: _classified_record(record) for record in status.get("records", [])}
    completion = _completion(status.get("records", []), [truth.workbook_id for truth in manifest.workbooks])
    rows: list[dict[str, Any]] = []
    workbook_rows: list[dict[str, Any]] = []
    counters = Counter()
    completed_counters = Counter()
    by_family: dict[str, Counter[str]] = defaultdict(Counter)
    by_scope: dict[tuple[str, str, str, str, str], Counter[str]] = defaultdict(Counter)
    durations: list[int | float] = []

    for truth in manifest.workbooks:
        record = by_id.get(truth.workbook_id, {"status": "NOT_RUN"})
        classified = classified_by_id.get(truth.workbook_id, {"status": "NOT_RUN", "audit_status": "NOT_RUN", "truncated": False, "omitted_details": 0})
        engine_status = str(classified["status"])
        if record.get("elapsed_ms") is not None:
            durations.append(record["elapsed_ms"])
        expected = [item for item in truth.expected_findings if item.is_scored_error]
        raw: dict[str, Any] = {}
        audit_status = str(classified.get("audit_status") or "NOT_RUN")
        if engine_status in {"COMPLETED", "PARTIAL"} and record.get("raw_output"):
            raw = read_json(Path(record["raw_output"]))
            audit_status = (raw.get("audit") or {}).get("status", "UNKNOWN")
        actual, duplicate_count = _dedupe_actuals(_actual_findings(raw))
        matched_actual: set[int] = set()
        scope_key = _group_key(truth)
        workbook_counts = Counter()

        for item in expected:
            matches = [index for index, candidate in enumerate(actual) if index not in matched_actual and _matches(item, candidate)]
            if matches:
                matched_actual.add(matches[0])
                outcome = "TP"
                workbook_counts["tp"] += 1
            else:
                outcome = "FN"
                workbook_counts["fn"] += 1
            rows.append({"workbook_id": truth.workbook_id, "split": truth.split, "business_domain": truth.business_domain, "structural_family": truth.structural_family, "mutation_type": truth.mutation_type or "normal", "family_id": truth.family_id, "kind": truth.kind, "expected_id": item.expected_id, "expected_kind": item.kind, "expected_rule": item.rule_code or "", "expected_subtype": item.pattern_subtype or "", "sheet": item.sheet, "region": item.cell, "cell": item.cell, "outcome": outcome, "engine_status": engine_status})

        normal_cells = _normal_region_cells(truth)
        excluded_cells = _ambiguous_or_unsupported_cells(truth)
        excluded = 0
        definitive_false_positives = 0
        candidate_false_positives = 0
        diagnostic_mismatches = 0
        unjudged = 0
        for index, candidate in enumerate(actual):
            if index in matched_actual:
                continue
            location = (candidate.get("sheet"), candidate.get("cell"))
            if _bounds(candidate.get("cell")) is None:
                unjudged += 1
                outcome = "UNJUDGED_MALFORMED_LOCATION"
                expected_kind = "unjudged_outside_scope"
            elif location in excluded_cells:
                excluded += 1
                outcome = "EXCLUDED_AMBIGUOUS_OR_OUT_OF_SCOPE"
                expected_kind = "excluded_or_ambiguous"
            elif _overlaps_scored_expected(candidate, expected):
                diagnostic_mismatches += 1
                outcome = "FP_DIAGNOSTIC_MISMATCH"
                expected_kind = "scored_expected_diagnostic_mismatch"
            elif location in normal_cells:
                if candidate.get("source") == "m4_candidate":
                    candidate_false_positives += 1
                    outcome = "FP_M4_CANDIDATE_NORMAL_REGION"
                    expected_kind = "normal_region"
                elif candidate.get("rule_code") in IN_SCOPE_BASE_RULES:
                    definitive_false_positives += 1
                    outcome = "FP_BASE_NORMAL_REGION"
                    expected_kind = "normal_region"
                else:
                    unjudged += 1
                    outcome = "UNJUDGED_BASE_RULE_OUTSIDE_SCOPE"
                    expected_kind = "unjudged_outside_scope"
            else:
                unjudged += 1
                outcome = "UNJUDGED_OUTSIDE_DECLARED_SCOPE"
                expected_kind = "unjudged_outside_scope"
            rows.append({"workbook_id": truth.workbook_id, "split": truth.split, "business_domain": truth.business_domain, "structural_family": truth.structural_family, "mutation_type": truth.mutation_type or "normal", "family_id": truth.family_id, "kind": truth.kind, "expected_id": "", "expected_kind": expected_kind, "expected_rule": "", "expected_subtype": "", "sheet": candidate.get("sheet") or "", "region": candidate.get("cell") or "", "cell": candidate.get("cell") or "", "outcome": outcome, "engine_status": engine_status})

        normal_region_fp = definitive_false_positives + candidate_false_positives
        total_fp = normal_region_fp + diagnostic_mismatches
        workbook_counts["fp"] += total_fp
        workbook_counts["candidate_fp"] += candidate_false_positives
        workbook_counts["definitive_fp"] += definitive_false_positives
        workbook_counts["normal_region_fp"] += normal_region_fp
        workbook_counts["diagnostic_mismatch"] += diagnostic_mismatches
        workbook_counts["excluded"] += excluded
        workbook_counts["unjudged"] += unjudged
        workbook_counts["duplicates"] += duplicate_count
        if str(audit_status).startswith("SKIPPED_"):
            workbook_counts["audit_skipped"] += 1
        if str(audit_status).startswith("ABSTAINED"):
            workbook_counts["audit_abstained"] += 1
        if audit_status == "FAILED":
            workbook_counts["audit_failed"] += 1
        if classified.get("truncated") or int(classified.get("omitted_details") or 0) > 0:
            workbook_counts["truncated"] += 1
        counters.update(workbook_counts)
        by_family[truth.family_id].update(workbook_counts)
        by_scope[scope_key].update(workbook_counts)
        if engine_status == "COMPLETED":
            completed_counters.update(workbook_counts)
        for target in (by_family[truth.family_id], by_scope[scope_key]):
            target["workbooks"] += 1
            target["successful_workbooks"] += 1 if engine_status == "COMPLETED" else 0

        workbook_rows.append({"workbook_id": truth.workbook_id, "split": truth.split, "business_domain": truth.business_domain, "structural_family": truth.structural_family, "mutation_type": truth.mutation_type or "normal", "family_id": truth.family_id, "kind": truth.kind, "engine_status": engine_status, "raw_status": classified.get("raw_status") or "", "audit_status": audit_status, "base_truncated_or_omitted": bool(classified.get("truncated") or int(classified.get("omitted_details") or 0) > 0), "omitted_details": int(classified.get("omitted_details") or 0), "expected_scored": len(expected), "actual_findings_and_candidates": len(actual), "duplicates_not_fp": duplicate_count, "false_positives": total_fp, "candidate_false_positives": candidate_false_positives, "definitive_false_positives": definitive_false_positives, "normal_region_false_positives": normal_region_fp, "diagnostic_mismatches": diagnostic_mismatches, "excluded_ambiguous_or_out_of_scope": excluded, "unjudged_findings": unjudged})

    completed = sum(1 for row in workbook_rows if row["engine_status"] == "COMPLETED")
    partial = sum(1 for row in workbook_rows if row["engine_status"] == "PARTIAL")
    p95 = sorted(durations)[max(0, ceil(len(durations) * 0.95) - 1)] if durations else None
    by_scope_rows = []
    for key, counts in sorted(by_scope.items()):
        business_domain, structural_family, mutation_type, split, family_id = key
        fp_values = [row["false_positives"] for row in workbook_rows if (row["business_domain"], row["structural_family"], row["mutation_type"], row["split"], row["family_id"]) == key]
        by_scope_rows.append({"business_domain": business_domain, "structural_family": structural_family, "mutation_type": mutation_type, "split": split, "family_id": family_id, **dict(counts), "avg_fp_per_workbook": round(mean(fp_values), 4) if fp_values else 0, "max_fp_per_workbook": max(fp_values) if fp_values else 0})
    summary = {
        "dataset_version": manifest.dataset_version,
        "run_id": manifest.run_id,
        "metric_scope": "Synthetic diagnostic validation only; not a customer-file accuracy claim.",
        "entrypoint_scope": "Local scan_workbook plus run_formula_audit, not HTTP/UI.",
        "excel_recalculation": "NOT_RUN",
        "completion": completion,
        "metrics_full_contract": {"tp": counters["tp"], "fn": counters["fn"], "fp": counters["fp"], "candidate_fp": counters["candidate_fp"], "definitive_fp": counters["definitive_fp"], "normal_region_fp": counters["normal_region_fp"], "diagnostic_mismatch": counters["diagnostic_mismatch"], "duplicates_not_fp": counters["duplicates"], "precision": _percent(counters["tp"], counters["tp"] + counters["fp"]), "recall": _percent(counters["tp"], counters["tp"] + counters["fn"]), "excluded_ambiguous_or_out_of_scope_not_passes": counters["excluded"], "unjudged_findings_not_passes": counters["unjudged"], "workbooks_total": len(workbook_rows), "workbooks_completed": completed, "workbooks_partial": partial},
        "metrics_successful_only": {"workbooks_completed": completed, "workbooks_partial": partial, "workbooks_total": len(workbook_rows), "completion_rate": _percent(completed, len(workbook_rows)), "tp": completed_counters["tp"], "fn": completed_counters["fn"], "fp": completed_counters["fp"], "normal_region_fp": completed_counters["normal_region_fp"], "diagnostic_mismatch": completed_counters["diagnostic_mismatch"], "precision": _percent(completed_counters["tp"], completed_counters["tp"] + completed_counters["fp"]), "recall": _percent(completed_counters["tp"], completed_counters["tp"] + completed_counters["fn"])},
        "timing_ms": {"median": median(durations) if durations else None, "p95_ceil": p95},
        "by_family": {family: dict(counts) for family, counts in sorted(by_family.items())},
        "by_scope": by_scope_rows,
        "workbooks": workbook_rows,
    }
    reports_dir = run_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    write_json(reports_dir / "summary.json", summary)
    for name, data in {"case_results.csv": rows, "workbook_results.csv": workbook_rows, "scope_results.csv": by_scope_rows}.items():
        with (reports_dir / name).open("w", newline="", encoding="utf-8") as stream:
            if data:
                writer = csv.DictWriter(stream, fieldnames=sorted({key for row in data for key in row}))
                writer.writeheader()
                writer.writerows(data)
    return summary
