"""Frozen independent multi-sheet, partial-approval and boundary regressions."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location(
    "complex_validation", ROOT / "scripts/verify_complex_validation.py"
)
cases = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cases)


def test_complex_sources_and_independent_oracle_are_frozen():
    hashes = json.loads((cases.PACK / "expected/source-hashes.json").read_text(encoding="utf-8"))
    for path, digest in hashes.items():
        assert hashlib.sha256((cases.PACK / path).read_bytes()).hexdigest() == digest
    cases.oracle()


@pytest.mark.parametrize("filename", list(cases.oracle()["diagnosis"]))
def test_complex_diagnosis_exact_locations_and_normal_exceptions(filename):
    cases.check_diagnosis(filename, cases.oracle()["diagnosis"][filename])


@pytest.mark.parametrize("profile", list(cases.oracle()["repair"]))
def test_complex_independent_chained_calculation_and_partial_scope(profile):
    cases.check_plan(profile, cases.oracle()["repair"][profile])


def test_complex_comparison_all_888_rows_and_exact_large_integer():
    cases.check_comparison(cases.oracle()["comparison"])


@pytest.mark.parametrize("index", range(4))
def test_complex_unsupported_inputs_cannot_be_purchased(index):
    cases.check_negative(cases.oracle()["negative"][index])


def test_complex_comparison_1000_supported_and_1001_rejected():
    cases.check_capacity(cases.oracle()["capacity"])
