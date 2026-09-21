from __future__ import annotations

import csv
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from tools.synthetic_validation.schema import ExpectedFinding
from tools.synthetic_validation.scorer import score_results
from tools.synthetic_validation.tests.test_scorer import (
    _manifest,
    _truth,
    _write_status,
)


class CsvExportTests(unittest.TestCase):
    def test_scope_csv_uses_all_row_keys_when_later_scope_adds_tp(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            expected = ExpectedFinding("e1", "m4_candidate", "Sheet1", "A1", "FORMULA_PATTERN_GAP", "BLANK_GAP_CANDIDATE")
            first_scope = _truth("first", [])
            second_scope = replace(_truth("second", [expected]), family_id="F-second", business_domain="unit business b")
            raws = {
                "first": {"status": "COMPLETED", "base": {"findings": []}, "audit": {"status": "COMPLETED", "candidates": []}},
                "second": {"status": "COMPLETED", "base": {"findings": []}, "audit": {"status": "COMPLETED", "candidates": [
                    {"sheet": "Sheet1", "cell": "A1", "rule_code": "FORMULA_PATTERN_GAP", "formula_pattern": {"pattern_subtype": "BLANK_GAP_CANDIDATE"}},
                ]}},
            }
            _write_status(root, raws)

            summary = score_results(manifest=_manifest([first_scope, second_scope]), dataset_root=root / "dataset", run_root=root)

            with (root / "reports" / "scope_results.csv").open(newline="", encoding="utf-8") as stream:
                reader = csv.DictReader(stream)
                scope_rows = list(reader)

            self.assertEqual(summary["metrics_full_contract"]["tp"], 1)
            self.assertEqual(reader.fieldnames, sorted(set().union(*(row.keys() for row in summary["by_scope"]))))
            self.assertIn("tp", reader.fieldnames or [])
            self.assertEqual(scope_rows[1]["tp"], "1")


if __name__ == "__main__":
    unittest.main()
