from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.synthetic_validation.generator import (
    create_mutated_workbook,
    create_normal_workbook,
)
from tools.synthetic_validation.scenarios import SCENARIOS
from tools.synthetic_validation.verify_generated import validate_generated_workbook


def _scenario(scenario_id: str):
    return next(scenario for scenario in SCENARIOS if scenario.scenario_id == scenario_id)


class MutationRoleTests(unittest.TestCase):
    def test_unsupported_table_mutation_preserves_original_role_and_validates(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            dataset_root = Path(temp) / "dataset"
            workbook_dir = dataset_root / "workbooks"
            scenario = _scenario("purchase_orders_table")
            normal = create_normal_workbook(scenario=scenario, seed=3, workbook_id="unit-normal-table", split="train", output_dir=workbook_dir)

            mutated = create_mutated_workbook(normal_truth=normal, mutation_index=0, seed=1, output_dir=workbook_dir)

            target_sheet, target_cell = mutated.mutation_target.split("!", 1)
            original = next(spec for spec in normal.formula_cells if spec.sheet == target_sheet and spec.cell == target_cell)
            replacement = next(spec for spec in mutated.formula_cells if spec.sheet == target_sheet and spec.cell == target_cell)
            self.assertEqual(replacement.role, original.role)
            self.assertFalse(replacement.supported_by_current_m4)
            self.assertTrue(any(finding.kind == "out_of_scope" for finding in mutated.expected_findings))
            checks = validate_generated_workbook(dataset_root, mutated)
            self.assertGreaterEqual(checks["boundary_checks"], 1)

    def test_unsupported_horizontal_mutation_keeps_exploratory_role_and_out_of_scope(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            dataset_root = Path(temp) / "dataset"
            workbook_dir = dataset_root / "workbooks"
            scenario = _scenario("budget_horizontal_months")
            normal = create_normal_workbook(scenario=scenario, seed=5, workbook_id="unit-normal-horizontal", split="train", output_dir=workbook_dir)

            mutated = create_mutated_workbook(normal_truth=normal, mutation_index=0, seed=8, output_dir=workbook_dir)

            target_sheet, target_cell = mutated.mutation_target.split("!", 1)
            replacement = next(spec for spec in mutated.formula_cells if spec.sheet == target_sheet and spec.cell == target_cell)
            self.assertEqual(replacement.role, "exploratory")
            self.assertFalse(replacement.supported_by_current_m4)
            self.assertTrue(any(finding.kind == "out_of_scope" for finding in mutated.expected_findings))


if __name__ == "__main__":
    unittest.main()
