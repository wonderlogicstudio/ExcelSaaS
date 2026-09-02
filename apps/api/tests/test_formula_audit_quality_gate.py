from __future__ import annotations

import importlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CORPUS_ROOT = ROOT / "samples" / "m4-evaluation"


def _evaluator_module():
    sys.path.insert(0, str(ROOT / "scripts"))
    return importlib.import_module("evaluate_formula_patterns")


def _outcomes(summary: dict[str, object]) -> list[tuple[str, str]]:
    rows = summary["case_results"]
    assert isinstance(rows, list)
    return [(row["case_id"], row["actual_outcome"]) for row in rows]


def test_synthetic_quality_gate_is_labelled_reproducible_and_value_free(tmp_path: Path) -> None:
    evaluator = _evaluator_module()
    manifest = json.loads((CORPUS_ROOT / "manifest.json").read_text(encoding="utf-8"))
    assert len(manifest["cases"]) >= 40
    assert {case["expected_detection"] for case in manifest["cases"]} == {
        "SHOULD_DETECT",
        "SHOULD_NOT_DETECT",
        "UNSUPPORTED",
    }
    assert all((CORPUS_ROOT / workbook["filename"]).exists() for workbook in manifest["workbooks"])

    first = evaluator.evaluate_corpus(
        corpus_root=CORPUS_ROOT,
        output_root=tmp_path / "first",
        include_performance=False,
    )
    second = evaluator.evaluate_corpus(
        corpus_root=CORPUS_ROOT,
        output_root=tmp_path / "second",
        include_performance=False,
    )

    assert first["decision"] == "CONDITIONAL_GO"
    assert first["metrics"] == second["metrics"]
    assert first["quality_gates"] == second["quality_gates"]
    assert _outcomes(first) == _outcomes(second)
    assert first["finding_key_stable"] is True
    assert first["all_findings_have_explanation_and_limitations"] is True
    assert first["performance_was_run"] is False
    assert all(
        row["expected_pattern_subtype"]
        for row in first["case_results"]
        if row["expected_detection"] == "SHOULD_DETECT"
    )

    rendered = (tmp_path / "first" / "evaluation.json").read_text(encoding="utf-8")
    assert "=SUM(" not in rendered
    assert "=AVERAGE(" not in rendered
    assert "901" not in rendered
    assert "FunctionDrift" not in rendered


def test_local_evaluation_persists_only_deidentified_review_references(tmp_path: Path) -> None:
    evaluator = _evaluator_module()
    local_dir = tmp_path / "local-evaluation"
    local_dir.mkdir()
    shutil.copyfile(CORPUS_ROOT / "detected-patterns.xlsx", local_dir / "private-workbook.xlsx")

    result = evaluator.evaluate_local_directory(local_dir)

    assert result["records"]
    summary = (local_dir / "evaluation-summary.json").read_text(encoding="utf-8")
    labels = (local_dir / "manual-labels.csv").read_text(encoding="utf-8")
    assert "private-workbook.xlsx" not in summary
    assert "FunctionDrift" not in summary
    assert "C4" not in summary
    assert "=SUM(" not in summary
    assert "LOCAL-001-F001" in labels
