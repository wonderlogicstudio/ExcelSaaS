from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

from tools.synthetic_validation.generator import (
    create_mutated_workbook,
    create_normal_workbook,
)
from tools.synthetic_validation.scenarios import SCENARIOS
from tools.synthetic_validation.schema import FormulaCellSpec, WorkbookTruth
from tools.synthetic_validation.verify_generated import (
    GenerationValidationError,
    validate_generated_workbook,
)


def _generated_pair(root: Path) -> tuple[Path, WorkbookTruth, WorkbookTruth]:
    dataset_root = root / "dataset"
    workbook_dir = dataset_root / "workbooks"
    normal = create_normal_workbook(scenario=SCENARIOS[0], seed=7, workbook_id="unit-normal-retail", split="train", output_dir=workbook_dir)
    mutated = create_mutated_workbook(normal_truth=normal, mutation_index=3, seed=11, output_dir=workbook_dir)
    return dataset_root, normal, mutated


def _replace_spec(truth: WorkbookTruth, sheet: str, cell: str, **updates: Any) -> WorkbookTruth:
    formula_cells: list[FormulaCellSpec] = []
    for spec in truth.formula_cells:
        formula_cells.append(replace(spec, **updates) if spec.sheet == sheet and spec.cell == cell else spec)
    return replace(truth, formula_cells=formula_cells)


def _write_cell(dataset_root: Path, truth: WorkbookTruth, sheet: str, cell: str, value: Any) -> None:
    path = dataset_root / truth.relative_path
    wb = load_workbook(path)
    try:
        wb[sheet][cell] = value
        wb.save(path)
    finally:
        wb.close()


class IntentionalMutationValidationTests(unittest.TestCase):
    def test_declared_ref_mutant_passes_after_normal_pair_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            dataset_root, normal, mutated = _generated_pair(Path(temp))

            self.assertEqual(validate_generated_workbook(dataset_root, normal)["excel_recalculation"], "NOT_RUN")
            self.assertEqual(mutated.kind, "mutated")
            self.assertEqual(mutated.mutation_type, "base_broken_ref_token")
            self.assertEqual(mutated.mutation_snapshot.after_value, "=SUM(#REF!)")

            checks = validate_generated_workbook(dataset_root, mutated)

            self.assertEqual(checks["answer_marker_cells"], 0)
            self.assertEqual(checks["excel_recalculation"], "NOT_RUN")

    def test_declared_mutant_rejects_actual_target_tamper(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            dataset_root, _normal, mutated = _generated_pair(Path(temp))
            snapshot = mutated.mutation_snapshot
            assert snapshot is not None
            _write_cell(dataset_root, mutated, snapshot.sheet, snapshot.cell, snapshot.before_value)

            with self.assertRaises(GenerationValidationError):
                validate_generated_workbook(dataset_root, mutated)

    def test_declared_mutant_rejects_inconsistent_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            dataset_root, _normal, mutated = _generated_pair(Path(temp))
            snapshot = mutated.mutation_snapshot
            assert snapshot is not None

            invalid_cases = [
                replace(mutated, mutation_target=None),
                replace(mutated, mutation_snapshot=None),
                replace(mutated, mutation_target=f"{snapshot.sheet}!A1"),
                replace(mutated, mutation_snapshot=replace(snapshot, after_data_type="n")),
                replace(mutated, mutation_snapshot=replace(snapshot, after_value="=#DIV/0!")),
                replace(mutated, mutation_snapshot=replace(snapshot, before_value=snapshot.after_value, before_data_type=snapshot.after_data_type)),
            ]
            for invalid_truth in invalid_cases:
                with self.subTest(invalid_truth=invalid_truth), self.assertRaises(GenerationValidationError):
                    validate_generated_workbook(dataset_root, invalid_truth)

    def test_undeclared_normal_ref_sum_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            dataset_root, normal, _mutated = _generated_pair(Path(temp))
            target = normal.formula_cells[0]
            _write_cell(dataset_root, normal, target.sheet, target.cell, "=SUM(#REF!)")
            tampered_truth = _replace_spec(normal, target.sheet, target.cell, formula="=SUM(#REF!)", semantic_value=None)

            with self.assertRaisesRegex(GenerationValidationError, "invalid subtotal range"):
                validate_generated_workbook(dataset_root, tampered_truth)

    def test_non_target_ref_sum_is_rejected_on_declared_mutant(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            dataset_root, _normal, mutated = _generated_pair(Path(temp))
            snapshot = mutated.mutation_snapshot
            assert snapshot is not None
            nontarget = next(spec for spec in mutated.formula_cells if not (spec.sheet == snapshot.sheet and spec.cell == snapshot.cell))
            _write_cell(dataset_root, mutated, nontarget.sheet, nontarget.cell, "=SUM(#REF!)")
            tampered_truth = _replace_spec(mutated, nontarget.sheet, nontarget.cell, formula="=SUM(#REF!)", semantic_value=None)

            with self.assertRaisesRegex(GenerationValidationError, "invalid subtotal range"):
                validate_generated_workbook(dataset_root, tampered_truth)

    def test_subtotal_boundary_validation_still_runs_for_unaffected_cells(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            dataset_root, normal, _mutated = _generated_pair(Path(temp))
            subtotal = next(spec for spec in normal.formula_cells if spec.role == "subtotal")
            bad_formula = "=SUM(A1:A1)"
            _write_cell(dataset_root, normal, subtotal.sheet, subtotal.cell, bad_formula)
            tampered_truth = _replace_spec(normal, subtotal.sheet, subtotal.cell, formula=bad_formula)

            with self.assertRaisesRegex(GenerationValidationError, "subtotal range includes non-detail cells"):
                validate_generated_workbook(dataset_root, tampered_truth)


if __name__ == "__main__":
    unittest.main()
