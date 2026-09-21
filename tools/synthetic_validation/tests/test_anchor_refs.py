from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

from tools.synthetic_validation.anchors import (
    PAYROLL_ALT_PREMIUM,
    PAYROLL_ALT_PREMIUM_CELL,
    PAYROLL_ANCHOR_HOURS,
    PAYROLL_ANCHOR_TARGET_ROW,
    create_payroll_anchor_mutant,
    prepare_payroll_anchor_normal,
)
from tools.synthetic_validation.schema import FormulaCellSpec, WorkbookTruth
from tools.synthetic_validation.verify_generated import (
    GenerationValidationError,
    validate_generated_workbook,
)


def _replace_spec(truth: WorkbookTruth, sheet: str, cell: str, **updates: Any) -> WorkbookTruth:
    specs: list[FormulaCellSpec] = []
    for spec in truth.formula_cells:
        specs.append(replace(spec, **updates) if spec.sheet == sheet and spec.cell == cell else spec)
    return replace(truth, formula_cells=specs)


def _write_cell(dataset_root: Path, truth: WorkbookTruth, sheet: str, cell: str, value: Any) -> None:
    wb = load_workbook(dataset_root / truth.relative_path)
    try:
        wb[sheet][cell] = value
        wb.save(dataset_root / truth.relative_path)
    finally:
        wb.close()


class AnchorReferenceTests(unittest.TestCase):
    def test_payroll_normal_uses_absolute_and_mixed_anchor_refs_with_independent_expected_value(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            dataset_root = Path(temp) / "dataset"
            workbook_dir = dataset_root / "workbooks"
            normal, expected = prepare_payroll_anchor_normal(seed=23, workbook_id="unit-normal-anchor", split="train", output_dir=workbook_dir)
            target = next(spec for spec in normal.formula_cells if spec.sheet == "Payroll" and spec.cell == f"J{PAYROLL_ANCHOR_TARGET_ROW}")

            self.assertEqual(PAYROLL_ANCHOR_HOURS, expected["hours"])
            self.assertIn("'Rate Card'!$B12", target.formula)
            self.assertIn("C$5", target.formula)
            self.assertIn("$B$5", target.formula)
            self.assertNotEqual(expected["before_expected"], expected["after_expected"])
            self.assertEqual(target.semantic_value, expected["before_expected"])

            checks = validate_generated_workbook(dataset_root, normal)
            self.assertEqual(checks["excel_recalculation"], "NOT_RUN")
            self.assertGreater(checks["reference_checks"], 0)

    def test_payroll_anchor_shift_mutates_one_formula_cell_and_records_reference_cell_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            dataset_root = Path(temp) / "dataset"
            workbook_dir = dataset_root / "workbooks"
            normal, _expected = prepare_payroll_anchor_normal(seed=23, workbook_id="unit-normal-anchor", split="train", output_dir=workbook_dir)

            mutated, mutation = create_payroll_anchor_mutant(normal_truth=normal, output_dir=workbook_dir)

            self.assertEqual(mutated.mutation_target, f"Payroll!J{PAYROLL_ANCHOR_TARGET_ROW}")
            self.assertIn(f"${PAYROLL_ALT_PREMIUM_CELL[0]}${PAYROLL_ALT_PREMIUM_CELL[1:]}", mutation["after_formula"])
            self.assertEqual(PAYROLL_ALT_PREMIUM, 0.25)
            self.assertNotEqual(mutation["before_expected"], mutation["after_expected"])
            self.assertTrue(mutated.generation_checks["mutation_target_only_changed"])
            expected = [finding for finding in mutated.expected_findings if finding.mutation_type == "m4_anchor_reference_shift"]
            self.assertEqual(len(expected), 1)
            self.assertEqual(expected[0].rule_code, "FORMULA_PATTERN_OUTLIER")
            self.assertEqual(expected[0].pattern_subtype, "REFERENCE_CELL_DRIFT")

            checks = validate_generated_workbook(dataset_root, mutated)
            self.assertEqual(checks["excel_recalculation"], "NOT_RUN")

    def test_wrong_anchor_formula_tamper_fails_even_when_truth_spec_matches(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            dataset_root = Path(temp) / "dataset"
            workbook_dir = dataset_root / "workbooks"
            normal, expected = prepare_payroll_anchor_normal(seed=23, workbook_id="unit-normal-anchor", split="train", output_dir=workbook_dir)
            target = next(spec for spec in normal.formula_cells if spec.sheet == "Payroll" and spec.cell == f"J{PAYROLL_ANCHOR_TARGET_ROW}")
            bad_formula = target.formula.replace("$B$5", "$B$6")
            _write_cell(dataset_root, normal, target.sheet, target.cell, bad_formula)
            tampered = _replace_spec(normal, target.sheet, target.cell, formula=bad_formula, semantic_value=expected["after_expected"])

            with self.assertRaisesRegex(GenerationValidationError, "unsupported payroll anchor formula"):
                validate_generated_workbook(dataset_root, tampered)


if __name__ == "__main__":
    unittest.main()
