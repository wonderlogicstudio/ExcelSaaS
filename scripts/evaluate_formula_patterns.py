"""Evaluate the narrow M4-A formula-pattern engine against a labelled corpus.

Only synthetic corpus outputs are written under ``artifacts/m4-a5``. Optional
local evaluation writes de-identified aggregate counts only: no local filename,
sheet, cell, finding key, value, or formula text is persisted.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
sys.path.insert(0, str(API_ROOT))

from app.config import Settings
from app.recommendation_engine import add_finding_guidance
from app.scanner import (
    FORMULA_AUDIT_RULE_SET_VERSION,
    SCANNER_VERSION,
    run_formula_audit,
    scan_workbook,
)

M4_RULE_CODES = {"FORMULA_PATTERN_OUTLIER", "FORMULA_PATTERN_GAP"}
PERFORMANCE_RATIO_REVIEW_LIMIT = 2.0


@dataclass(frozen=True, slots=True)
class Candidate:
    sheet: str | None
    cell: str | None
    rule_code: str
    pattern_type: str | None
    pattern_subtype: str | None
    finding_key: str | None
    has_explanation: bool


def _baseline_scan(payload: bytes, *, filename: str, scan_cell_limit: int = 250_000):
    return scan_workbook(
        filename,
        payload,
        Settings(scan_cell_limit=scan_cell_limit, finding_limit=5_000),
    )


def _audit(payload: bytes, *, filename: str, scan_cell_limit: int = 250_000):
    result = run_formula_audit(
        filename,
        payload,
        Settings(
            app_env="internal_beta",
            formula_pattern_audit_enabled=True,
            scan_cell_limit=scan_cell_limit,
            finding_limit=5_000,
        ),
    )
    return result.model_copy(update={"candidates": add_finding_guidance(result.candidates)})


def _candidates(result) -> list[Candidate]:
    candidates: list[Candidate] = []
    for finding in result.candidates:
        evidence = finding.formula_pattern
        if finding.rule_code not in M4_RULE_CODES or evidence is None:
            continue
        candidates.append(
            Candidate(
                sheet=finding.sheet,
                cell=finding.cell,
                rule_code=finding.rule_code,
                pattern_type=evidence.pattern_type,
                pattern_subtype=evidence.pattern_subtype,
                finding_key=finding.finding_key,
                has_explanation=bool(
                    evidence.pattern_subtype
                    and evidence.evidence_summary
                    and evidence.dominant_pattern_summary
                    and evidence.comparison_locations
                    and evidence.normal_case_possibility
                    and evidence.current_limitations
                ),
            )
        )
    return candidates


def _matches(case: dict[str, Any], candidate: Candidate) -> bool:
    return (
        case["sheet"] == candidate.sheet
        and case["cell"] == candidate.cell
        and (
            case.get("expected_rule_code") is None
            or case["expected_rule_code"] == candidate.rule_code
        )
        and (
            case.get("expected_pattern_type") is None
            or case["expected_pattern_type"] == candidate.pattern_type
        )
        and (
            case.get("expected_pattern_subtype") is None
            or case["expected_pattern_subtype"] == candidate.pattern_subtype
        )
    )


def _timed_scan(
    payload: bytes, *, filename: str, enabled: bool
) -> tuple[float, bool, str | None, int]:
    """Measure normal scanner timing without allocation instrumentation.

    ``tracemalloc`` materially changes this tokenizer-heavy workload, so the
    report records memory as not measured rather than presenting distorted
    numbers. No extra dependency is added for a platform-specific metric.
    """
    started = time.perf_counter()
    try:
        if enabled:
            result = _audit(payload, filename=filename)
            scan_truncated = result.status == "SKIPPED_TRUNCATED"
            formula_count = result.formula_cell_count
        else:
            result = _baseline_scan(payload, filename=filename)
            scan_truncated = result.workbook.scan_truncated
            formula_count = result.workbook.formula_count
        elapsed = time.perf_counter() - started
        return elapsed, scan_truncated, None, formula_count
    except Exception as exc:  # pragma: no cover - defensive report path
        elapsed = time.perf_counter() - started
        return elapsed, False, f"{type(exc).__name__}: {exc}", 0


def _quality_decision(summary: dict[str, Any]) -> tuple[str, list[str]]:
    failed = [name for name, passed in summary["quality_gates"].items() if not passed]
    if not failed:
        return "GO", []
    public_types = [
        pattern_type
        for pattern_type, counts in summary["by_pattern_type"].items()
        if counts["false_negatives"] == 0 and counts["false_positives"] == 0
    ]
    return ("CONDITIONAL_GO" if public_types else "NO_GO"), failed


def _matching_candidates(
    case: dict[str, Any], candidates: list[Candidate]
) -> list[tuple[int, Candidate]]:
    return [
        (index, candidate)
        for index, candidate in enumerate(candidates)
        if _matches(case, candidate)
    ]


def evaluate_corpus(
    *,
    corpus_root: Path,
    output_root: Path,
    include_performance: bool = True,
    performance_runs: int = 3,
) -> dict[str, Any]:
    manifest = json.loads((corpus_root / "manifest.json").read_text(encoding="utf-8"))
    by_workbook: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case in manifest["cases"]:
        by_workbook[case["workbook_id"]].append(case)

    rows: list[dict[str, Any]] = []
    true_positives = false_positives = false_negatives = 0
    unsupported_exposures = hard_exclusion_failures = 0
    normal_workbooks = normal_workbook_passes = 0
    by_pattern_type: dict[str, Counter[str]] = defaultdict(Counter)
    by_exception: dict[str, Counter[str]] = defaultdict(Counter)
    workbook_false_positives: dict[str, int] = {}
    errors: list[str] = []
    finding_key_stable = True
    all_explanations_present = True

    for workbook in manifest["workbooks"]:
        workbook_id = workbook["workbook_id"]
        payload = (corpus_root / workbook["filename"]).read_bytes()
        scan_limit = workbook.get("scan_cell_limit", 250_000)
        started = time.perf_counter()
        first = _audit(payload, filename=workbook["filename"], scan_cell_limit=scan_limit)
        elapsed = time.perf_counter() - started
        second = _audit(payload, filename=workbook["filename"], scan_cell_limit=scan_limit)
        actual = _candidates(first)
        repeated = _candidates(second)
        actual_keys = [(candidate.rule_code, candidate.finding_key) for candidate in actual]
        repeated_keys = [(candidate.rule_code, candidate.finding_key) for candidate in repeated]
        finding_key_stable = finding_key_stable and actual_keys == repeated_keys
        all_explanations_present = all_explanations_present and all(
            candidate.has_explanation for candidate in actual
        )
        expected_cases = by_workbook[workbook_id]
        matched_actual: set[int] = set()

        for case in expected_cases:
            matches = _matching_candidates(case, actual)
            matching_indexes = {index for index, _ in matches}
            detected = bool(matches)
            action = case["expected_action"]
            expected_detection = case["expected_detection"]
            outcome = "PASS"
            if expected_detection == "SHOULD_DETECT":
                pattern_type = case["expected_pattern_type"] or "UNSPECIFIED"
                if detected:
                    true_positives += 1
                    by_pattern_type[pattern_type]["true_positives"] += 1
                    matched_actual.update(matching_indexes)
                else:
                    false_negatives += 1
                    by_pattern_type[pattern_type]["false_negatives"] += 1
                    outcome = "FALSE_NEGATIVE"
            else:
                by_exception[action]["cases"] += 1
                if detected:
                    false_positives += 1
                    outcome = (
                        "UNSUPPORTED_EXPOSURE"
                        if expected_detection == "UNSUPPORTED"
                        else "FALSE_POSITIVE"
                    )
                    for _, candidate in matches:
                        by_pattern_type[candidate.pattern_type or "UNSPECIFIED"][
                            "false_positives"
                        ] += 1
                    if expected_detection == "UNSUPPORTED":
                        unsupported_exposures += 1
                    if action == "SUPPRESS_EXCLUDED":
                        hard_exclusion_failures += 1
                    matched_actual.update(matching_indexes)
                    by_exception[action]["failures"] += 1
            rows.append(
                {
                    "case_id": case["case_id"],
                    "workbook_id": workbook_id,
                    "expected_detection": expected_detection,
                    "expected_pattern_type": case["expected_pattern_type"] or "",
                    "expected_pattern_subtype": case.get("expected_pattern_subtype") or "",
                    "expected_action": action,
                    "actual_outcome": outcome,
                    "scan_truncated": first.status == "SKIPPED_TRUNCATED",
                    "processing_ms": round(elapsed * 1000, 2),
                }
            )

        unexpected = [
            candidate for index, candidate in enumerate(actual) if index not in matched_actual
        ]
        false_positives += len(unexpected)
        workbook_false_positives[workbook_id] = len(unexpected)
        for candidate in unexpected:
            by_pattern_type[candidate.pattern_type or "UNSPECIFIED"]["false_positives"] += 1
        if workbook["kind"] == "NORMAL":
            normal_workbooks += 1
            normal_workbook_passes += int(not actual)
        if first.status == "SKIPPED_TRUNCATED" and workbook["kind"] != "TRUNCATED":
            errors.append(f"{workbook_id}: unexpected scan truncation")
        if workbook["kind"] == "TRUNCATED" and first.status != "SKIPPED_TRUNCATED":
            errors.append(f"{workbook_id}: expected scan truncation was not observed")

    precision = (
        true_positives / (true_positives + false_positives)
        if true_positives + false_positives
        else 0.0
    )
    recall = (
        true_positives / (true_positives + false_negatives)
        if true_positives + false_negatives
        else 0.0
    )
    f1 = (
        2 * precision * recall / (precision + recall) if precision + recall else 0.0
    )
    normal_clean_rate = normal_workbook_passes / normal_workbooks if normal_workbooks else 0.0
    normal_fp_average = (
        sum(
            workbook_false_positives[workbook_id]
            for workbook_id in workbook_false_positives
            if workbook_id == "normal-exceptions"
        )
        / normal_workbooks
        if normal_workbooks
        else 0.0
    )

    performance: list[dict[str, Any]] = []
    performance_pass = False
    if include_performance:
        performance_pass = True
        for workload in manifest["performance_workbooks"]:
            payload = (corpus_root / workload["filename"]).read_bytes()
            baseline_runs = [
                _timed_scan(payload, filename=workload["filename"], enabled=False)
                for _ in range(performance_runs)
            ]
            m4_runs = [
                _timed_scan(payload, filename=workload["filename"], enabled=True)
                for _ in range(performance_runs)
            ]
            baseline_seconds = mean(run[0] for run in baseline_runs)
            m4_seconds = mean(run[0] for run in m4_runs)
            ratio = m4_seconds / baseline_seconds if baseline_seconds else None
            run_errors = [run[2] for run in [*baseline_runs, *m4_runs] if run[2]]
            record = {
                "workload": workload["workbook_id"],
                "formula_cells": workload["formula_cells"],
                "runs": performance_runs,
                "baseline_scan_seconds_avg": round(baseline_seconds, 4),
                "m4_enabled_scan_seconds_avg": round(m4_seconds, 4),
                "m4_extra_seconds_avg": round(m4_seconds - baseline_seconds, 4),
                "m4_to_baseline_ratio": round(ratio, 3) if ratio is not None else None,
                "memory_measurement": "not measured; tracemalloc was excluded to avoid altering timing.",
                "scan_truncated": any(run[1] for run in [*baseline_runs, *m4_runs]),
                "errors": run_errors,
            }
            performance.append(record)
            if (
                run_errors
                or record["scan_truncated"]
                or (ratio is not None and ratio > PERFORMANCE_RATIO_REVIEW_LIMIT)
            ):
                performance_pass = False

    for counts in by_pattern_type.values():
        counts.setdefault("true_positives", 0)
        counts.setdefault("false_positives", 0)
        counts.setdefault("false_negatives", 0)

    summary: dict[str, Any] = {
        "evaluation_kind": "synthetic_formula_audit_quality_gate",
        "metric_scope": "Synthetic labelled corpus only; not a claim about general workbook accuracy.",
        "scanner_version": SCANNER_VERSION,
        "rule_set_version": FORMULA_AUDIT_RULE_SET_VERSION,
        "feature_flag": {"formula_pattern_audit_enabled_default": False},
        "corpus": {
            "workbook_count": len(manifest["workbooks"]),
            "case_count": len(manifest["cases"]),
            "target_case_count": true_positives + false_negatives,
            "normal_workbook_count": normal_workbooks,
        },
        "metrics": {
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "true_negatives_or_clean_case_passes": normal_workbook_passes,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "normal_workbook_clean_rate": round(normal_clean_rate, 4),
            "normal_workbook_false_positive_average": round(normal_fp_average, 4),
            "unsupported_exposures": unsupported_exposures,
            "hard_exclusion_failures": hard_exclusion_failures,
        },
        "by_pattern_type": {key: dict(value) for key, value in sorted(by_pattern_type.items())},
        "by_normal_exception": {key: dict(value) for key, value in sorted(by_exception.items())},
        "workbook_false_positives": workbook_false_positives,
        "finding_key_stable": finding_key_stable,
        "all_findings_have_explanation_and_limitations": all_explanations_present,
        "errors": errors,
        "performance": performance,
        "performance_was_run": include_performance,
        "quality_gates": {
            "supported_recall_at_least_0_85": recall >= 0.85,
            "overall_precision_at_least_0_90": precision >= 0.90,
            "normal_workbook_clean_rate_at_least_0_80": normal_clean_rate >= 0.80,
            "normal_workbook_false_positive_average_at_most_1": normal_fp_average <= 1,
            "hard_exclusions_have_zero_findings": hard_exclusion_failures == 0,
            "unsupported_structures_have_zero_candidates": unsupported_exposures == 0,
            "no_scan_or_file_errors": not errors,
            "finding_keys_are_stable": finding_key_stable,
            "all_findings_have_explanation_and_limitations": all_explanations_present,
            "performance_measurement_completed": include_performance,
            "performance_ratio_within_review_limit": performance_pass,
        },
        "case_results": rows,
    }
    summary["decision"], summary["failed_quality_gates"] = _quality_decision(summary)
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "evaluation.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with (output_root / "evaluation.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return summary


def evaluate_local_directory(local_dir: Path) -> dict[str, Any]:
    """Write only de-identified aggregate local results for manual review."""
    input_paths = sorted(
        path for path in local_dir.iterdir() if path.suffix.casefold() in {".xlsx", ".xlsm"}
    )
    records: list[dict[str, Any]] = []
    labels: list[dict[str, str]] = []
    for case_index, path in enumerate(input_paths, start=1):
        result = _audit(path.read_bytes(), filename=path.name)
        candidates = _candidates(result)
        case_ref = f"LOCAL-{case_index:03d}"
        records.append(
            {
                "case_ref": case_ref,
                "candidate_count": len(candidates),
                "rule_counts": dict(Counter(candidate.rule_code for candidate in candidates)),
                "subtype_counts": dict(Counter(candidate.pattern_subtype for candidate in candidates)),
                "scan_truncated": result.status == "SKIPPED_TRUNCATED",
            }
        )
        labels.extend(
            {
                "candidate_ref": f"{case_ref}-F{finding_index:03d}",
                "manual_judgment": "",
                "reviewer_note": "",
            }
            for finding_index, _ in enumerate(candidates, start=1)
        )
    output = {
        "evaluation_kind": "local_deidentified_manual_review",
        "warning": "No ground truth is generated for local files. Use the manual label template.",
        "scanner_version": SCANNER_VERSION,
        "rule_set_version": FORMULA_AUDIT_RULE_SET_VERSION,
        "records": records,
    }
    (local_dir / "evaluation-summary.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with (local_dir / "manual-labels.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=["candidate_ref", "manual_judgment", "reviewer_note"]
        )
        writer.writeheader()
        writer.writerows(labels)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", type=Path, default=ROOT / "samples" / "m4-evaluation")
    parser.add_argument("--output-root", type=Path, default=ROOT / "artifacts" / "m4-a5")
    parser.add_argument("--skip-performance", action="store_true")
    parser.add_argument("--performance-runs", type=int, default=3)
    parser.add_argument("--local-dir", type=Path)
    args = parser.parse_args()

    if args.local_dir is not None:
        if not args.local_dir.exists():
            raise SystemExit(f"Local evaluation directory does not exist: {args.local_dir}")
        result = evaluate_local_directory(args.local_dir)
        print(json.dumps({"local_case_count": len(result["records"])}, ensure_ascii=False))
        return

    result = evaluate_corpus(
        corpus_root=args.corpus_root,
        output_root=args.output_root,
        include_performance=not args.skip_performance,
        performance_runs=max(1, args.performance_runs),
    )
    print(
        json.dumps(
            {
                "decision": result["decision"],
                "precision": result["metrics"]["precision"],
                "recall": result["metrics"]["recall"],
                "output": str(args.output_root),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
