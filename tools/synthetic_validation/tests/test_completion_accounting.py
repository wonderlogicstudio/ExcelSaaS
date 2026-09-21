from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.synthetic_validation.engine_worker import _status_from_parts
from tools.synthetic_validation.report import write_html_report
from tools.synthetic_validation.schema import ExpectedFinding, sha256_file, write_json
from tools.synthetic_validation.scorer import score_results
from tools.synthetic_validation.tests.test_scorer import _manifest, _truth


def _complete_base(findings: list[dict] | None = None) -> dict:
    findings = findings or []
    return {
        "workbook": {"scan_truncated": False},
        "summary": {"issue_count": len(findings)},
        "findings": findings,
        "finding_counts": {
            "total_detected": len(findings),
            "returned_details": len(findings),
            "omitted_details": 0,
            "scan_complete": True,
        },
    }


def _completed_audit(candidates: list[dict] | None = None) -> dict:
    return {"status": "COMPLETED", "candidates": candidates or []}


def _write_raw(root: Path, workbook_id: str, raw: dict, *, record_status: str | None = None) -> dict:
    raw_path = root / "raw_engine" / f"{workbook_id}.json"
    write_json(raw_path, raw)
    return {
        "workbook_id": workbook_id,
        "status": record_status or raw.get("status", "COMPLETED"),
        "elapsed_ms": 1,
        "raw_output": str(raw_path),
        "raw_sha256": sha256_file(raw_path),
    }


class CompletionAccountingTests(unittest.TestCase):
    def test_worker_classifies_skipped_abstained_unknown_failed_and_incomplete_base_as_partial(self) -> None:
        base = _complete_base()
        for audit_status in [
            "SKIPPED_WORKBOOK_LIMIT",
            "SKIPPED_TRUNCATED",
            "SKIPPED_FORMULA_LIMIT",
            "SKIPPED_UNSUPPORTED_STRUCTURE",
            "SKIPPED_CANDIDATE_LIMIT",
            "ABSTAINED_INSUFFICIENT_EVIDENCE",
            "UNKNOWN_STATUS",
            "FAILED",
        ]:
            with self.subTest(audit_status=audit_status):
                self.assertEqual(_status_from_parts(base, {"status": audit_status, "candidates": []}), "PARTIAL")

        self.assertEqual(_status_from_parts(base, _completed_audit()), "COMPLETED")
        self.assertEqual(_status_from_parts({"workbook": {"scan_truncated": True}, "findings": []}, _completed_audit()), "PARTIAL")
        self.assertEqual(_status_from_parts({**base, "finding_counts": {**base["finding_counts"], "scan_complete": False}}, _completed_audit()), "PARTIAL")
        self.assertEqual(_status_from_parts({**base, "finding_counts": {**base["finding_counts"], "omitted_details": 1}}, _completed_audit()), "PARTIAL")
        self.assertEqual(_status_from_parts({**base, "summary": {"issue_count": 1}, "finding_counts": None}, _completed_audit()), "PARTIAL")
        self.assertEqual(_status_from_parts(None, {"status": "FAILED", "candidates": []}), "FAILED")
        self.assertEqual(_status_from_parts(None, None), "FAILED")

    def test_score_separates_process_outputs_from_analysis_completion_and_preserves_full_contract_fns(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            m4_expected = ExpectedFinding("m4", "m4_candidate", "Sheet1", "A1", "FORMULA_PATTERN_GAP", "BLANK_GAP_CANDIDATE")
            base_expected = ExpectedFinding("base", "confirmed_error", "Sheet1", "B3", "FORMULA_REF_ERROR")
            completed = _truth("completed", [m4_expected])
            partial = _truth("partial", [base_expected, m4_expected])
            failed = _truth("failed", [m4_expected])
            missing = _truth("missing", [])
            candidate = {"sheet": "Sheet1", "cell": "A1", "rule_code": "FORMULA_PATTERN_GAP", "formula_pattern": {"pattern_subtype": "BLANK_GAP_CANDIDATE"}}
            base_finding = {"sheet": "Sheet1", "cell": "B3", "rule_code": "FORMULA_REF_ERROR"}
            records = [
                _write_raw(root, "completed", {"status": "COMPLETED", "base": _complete_base(), "audit": _completed_audit([candidate])}),
                _write_raw(root, "partial", {"status": "COMPLETED", "base": _complete_base([base_finding]), "audit": {"status": "SKIPPED_UNSUPPORTED_STRUCTURE", "candidates": []}}, record_status="COMPLETED"),
                {"workbook_id": "failed", "status": "FAILED", "elapsed_ms": 1, "raw_output": None, "raw_sha256": None},
            ]
            write_json(root / "engine_status.json", {"records": records, "completion": {"workbooks_total": 4, "completed": 4}})

            manifest = _manifest([completed, partial, failed, missing])
            summary = score_results(manifest=manifest, dataset_root=root / "dataset", run_root=root)

            self.assertEqual(
                summary["completion"],
                {
                    "workbooks_total": 4,
                    "process_outputs": 2,
                    "completed": 1,
                    "partial": 1,
                    "failed": 1,
                    "timeouts": 0,
                    "not_run": 1,
                    "skipped": 1,
                    "abstained": 0,
                    "audit_failed": 0,
                    "truncated": 0,
                    "raw_errors": 0,
                },
            )
            self.assertEqual(summary["metrics_full_contract"]["tp"], 2)
            self.assertEqual(summary["metrics_full_contract"]["fn"], 2)
            self.assertEqual(summary["metrics_successful_only"]["tp"], 1)
            self.assertEqual(summary["metrics_successful_only"]["fn"], 0)
            self.assertEqual(summary["metrics_successful_only"]["completion_rate"], 0.25)
            self.assertEqual(summary["by_scope"][0]["successful_workbooks"], 1)

            html_path = write_html_report(manifest=manifest, summary=summary, run_root=root)
            html = html_path.read_text(encoding="utf-8")
            self.assertIn("Process outputs:</b> 2/4", html)
            self.assertIn("Fully analyzed:</b> 1/4", html)
            self.assertIn("Skipped audits:</b> 1", html)

    def test_score_handles_base_only_partial_with_null_audit_and_preserves_not_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            expected = ExpectedFinding("base", "confirmed_error", "Sheet1", "B3", "FORMULA_REF_ERROR")
            base_only = _truth("base_only", [expected])
            explicit_not_run = _truth("explicit_not_run", [])
            base_finding = {"sheet": "Sheet1", "cell": "B3", "rule_code": "FORMULA_REF_ERROR"}
            records = [
                _write_raw(root, "base_only", {"status": "PARTIAL", "base": _complete_base([base_finding]), "audit": None}, record_status="PARTIAL"),
                {"workbook_id": "explicit_not_run", "status": "NOT_RUN", "elapsed_ms": None, "raw_output": None, "raw_sha256": None},
            ]
            write_json(root / "engine_status.json", {"records": records})

            summary = score_results(manifest=_manifest([base_only, explicit_not_run]), dataset_root=root / "dataset", run_root=root)

            self.assertEqual(summary["completion"]["partial"], 1)
            self.assertEqual(summary["completion"]["not_run"], 1)
            self.assertEqual(summary["completion"]["failed"], 0)
            self.assertEqual(summary["metrics_full_contract"]["tp"], 1)
            self.assertEqual(summary["workbooks"][0]["audit_status"], "UNKNOWN")
            self.assertEqual(summary["workbooks"][1]["engine_status"], "NOT_RUN")


if __name__ == "__main__":
    unittest.main()
