from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.synthetic_validation.report import write_html_report
from tools.synthetic_validation.schema import ExpectedFinding, sha256_file, write_json
from tools.synthetic_validation.scorer import score_results
from tools.synthetic_validation.tests.test_completion_accounting import _complete_base
from tools.synthetic_validation.tests.test_scorer import _manifest, _truth


def _candidate(sheet: str, cell: str, rule: str, subtype: str | None = None) -> dict:
    payload = {"sheet": sheet, "cell": cell, "rule_code": rule}
    if subtype is not None:
        payload["formula_pattern"] = {"pattern_subtype": subtype}
    return payload


def _raw(base_findings: list[dict] | None = None, candidates: list[dict] | None = None) -> dict:
    return {
        "status": "COMPLETED",
        "base": _complete_base(base_findings or []),
        "audit": {"status": "COMPLETED", "candidates": candidates or []},
    }


def _write_status(root: Path, raws: dict[str, dict]) -> None:
    records = []
    for workbook_id, raw in raws.items():
        raw_path = root / "raw_engine" / f"{workbook_id}.json"
        write_json(raw_path, raw)
        records.append({"workbook_id": workbook_id, "status": "COMPLETED", "elapsed_ms": 1, "raw_output": str(raw_path), "raw_sha256": sha256_file(raw_path)})
    write_json(root / "engine_status.json", {"records": records})


class MismatchAccountingTests(unittest.TestCase):
    def test_wrong_diagnostics_are_mismatch_fp_not_normal_region_fp(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            m4_expected = ExpectedFinding("m4", "m4_candidate", "Sheet1", "A1", "FORMULA_PATTERN_GAP", "BLANK_GAP_CANDIDATE")
            base_expected = ExpectedFinding("base", "confirmed_error", "Sheet1", "B3", "FORMULA_REF_ERROR")
            workbooks = [
                _truth("wrong_subtype", [m4_expected]),
                _truth("normal_fp", []),
                _truth("exact_wrong", [m4_expected]),
                _truth("duplicate_wrong", [m4_expected]),
                _truth("other_sheet", [m4_expected]),
                _truth("range_overlap", [base_expected]),
                _truth("wrong_source", [base_expected]),
            ]
            wrong_subtype = _candidate("Sheet1", "A1", "FORMULA_PATTERN_GAP", "RELATIVE_REFERENCE_DRIFT")
            exact = _candidate("Sheet1", "A1", "FORMULA_PATTERN_GAP", "BLANK_GAP_CANDIDATE")
            normal_fp = _candidate("Sheet1", "C2", "FORMULA_PATTERN_GAP", "BLANK_GAP_CANDIDATE")
            range_wrong_rule = {"sheet": "Sheet1", "cell": "B2:B4", "rule_code": "FORMULA_VISIBLE_ERROR_TOKEN"}
            wrong_source = _candidate("Sheet1", "B3", "FORMULA_REF_ERROR")
            raws = {
                "wrong_subtype": _raw(candidates=[wrong_subtype]),
                "normal_fp": _raw(candidates=[normal_fp]),
                "exact_wrong": _raw(candidates=[exact, wrong_subtype]),
                "duplicate_wrong": _raw(candidates=[wrong_subtype, wrong_subtype]),
                "other_sheet": _raw(candidates=[_candidate("Sheet2", "A1", "FORMULA_PATTERN_GAP", "RELATIVE_REFERENCE_DRIFT")]),
                "range_overlap": _raw(base_findings=[range_wrong_rule]),
                "wrong_source": _raw(candidates=[wrong_source]),
            }
            _write_status(root, raws)

            summary = score_results(manifest=_manifest(workbooks), dataset_root=root / "dataset", run_root=root)
            metrics = summary["metrics_full_contract"]
            successful = summary["metrics_successful_only"]

            self.assertEqual(metrics["tp"], 1)
            self.assertEqual(metrics["fn"], 5)
            self.assertEqual(metrics["fp"], 6)
            self.assertEqual(metrics["diagnostic_mismatch"], 5)
            self.assertEqual(metrics["normal_region_fp"], 1)
            self.assertEqual(metrics["candidate_fp"], 1)
            self.assertEqual(metrics["definitive_fp"], 0)
            self.assertEqual(metrics["duplicates_not_fp"], 1)
            self.assertEqual(metrics["unjudged_findings_not_passes"], 1)
            self.assertEqual(successful["diagnostic_mismatch"], 5)
            self.assertEqual(successful["normal_region_fp"], 1)
            self.assertEqual(successful["fp"], 6)

            by_workbook = {row["workbook_id"]: row for row in summary["workbooks"]}
            self.assertEqual(by_workbook["wrong_subtype"]["diagnostic_mismatches"], 1)
            self.assertEqual(by_workbook["normal_fp"]["normal_region_false_positives"], 1)
            self.assertEqual(by_workbook["exact_wrong"]["diagnostic_mismatches"], 1)
            self.assertEqual(by_workbook["exact_wrong"]["false_positives"], 1)
            self.assertEqual(by_workbook["duplicate_wrong"]["diagnostic_mismatches"], 1)
            self.assertEqual(by_workbook["duplicate_wrong"]["duplicates_not_fp"], 1)
            self.assertEqual(by_workbook["other_sheet"]["diagnostic_mismatches"], 0)
            self.assertEqual(by_workbook["range_overlap"]["diagnostic_mismatches"], 1)
            self.assertEqual(by_workbook["wrong_source"]["diagnostic_mismatches"], 1)
            self.assertEqual(summary["by_scope"][0]["diagnostic_mismatch"], 5)
            self.assertEqual(summary["by_scope"][0]["normal_region_fp"], 1)

            html_path = write_html_report(manifest=_manifest(workbooks), summary=summary, run_root=root)
            html = html_path.read_text(encoding="utf-8")
            self.assertIn("Diagnostic mismatch:</b> 5", html)
            self.assertIn("Normal-region FP:</b> 1", html)
            with (root / "reports" / "workbook_results.csv").open(newline="", encoding="utf-8") as stream:
                workbook_fields = csv.DictReader(stream).fieldnames or []
            with (root / "reports" / "scope_results.csv").open(newline="", encoding="utf-8") as stream:
                scope_fields = csv.DictReader(stream).fieldnames or []
            self.assertIn("diagnostic_mismatches", workbook_fields)
            self.assertIn("normal_region_false_positives", workbook_fields)
            self.assertIn("diagnostic_mismatch", scope_fields)
            self.assertIn("normal_region_fp", scope_fields)


if __name__ == "__main__":
    unittest.main()
