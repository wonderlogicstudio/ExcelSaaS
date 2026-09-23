from __future__ import annotations

import base64
import math
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from app.delivery_calculation import (
    CALCULATION_MODE_MONTHLY_SHEETS,
    ENGINE_DIR,
    calculate,
    formula_shape,
)
from app.errors import WorkbookCareError


def monthly_cells(formula: str = "='M10'!B16-'M10'!B15") -> dict:
    return {
        "Budget": {"N18": {"type": "formula", "value": formula}},
        "M10": {
            "B16": {"type": "number", "value": 1001},
            "B15": {"type": "number", "value": 1006},
        },
    }


def monthly_chain(length: int, *, reverse: bool = False) -> dict:
    items = [(f"A{length + 1}", {"type": "number", "value": 1})]
    items.extend(
        (f"A{index}", {"type": "formula", "value": f"=M01!A{index + 1}"})
        for index in range(length, 0, -1)
    )
    if reverse:
        items = list(reversed(items))
    return {"M01": dict(items)}


def _encoded(value: object) -> str:
    text = "" if value is None else str(value).lower() if isinstance(value, bool) else str(value)
    return base64.b64encode(text.encode()).decode()


def _decoded_java_rows(output: bytes) -> dict[tuple[str, str], dict]:
    rows = {}
    lines = output.decode().splitlines()
    start = lines.index("CALC_RESULT_V1") + 1
    for line in lines[start:]:
        sheet, address, kind, value = line.split("\t")
        decoded_sheet = base64.b64decode(sheet).decode()
        decoded_value = base64.b64decode(value).decode()
        rows[(decoded_sheet, address)] = {
            "type": kind,
            "value": float(decoded_value) if kind == "number" else decoded_value,
        }
    return rows


def _run_raw_java(
    rows: list[tuple[str, str, str, object]],
    mode: str = "",
    timeout: float = 10.0,
    header: str | None = None,
) -> subprocess.CompletedProcess:
    java = shutil.which("java")
    assert java is not None
    header = header if header is not None else "CALC_V1" + (("\t" + mode) if mode else "")
    payload = "\n".join(
        [header]
        + [
            "\t".join([_encoded(sheet), address, kind, _encoded(value)])
            for sheet, address, kind, value in rows
        ]
        + [""]
    ).encode()
    return subprocess.run(
        [
            java,
            "-cp",
            os.pathsep.join([str(ENGINE_DIR / "classes"), str(ENGINE_DIR / "lib/*")]),
            "DeliveryCalc",
        ],
        input=payload,
        cwd=Path(ENGINE_DIR),
        capture_output=True,
        check=False,
        timeout=timeout,
    )


def test_monthly_internal_mode_calculates_actual_poi_sheet_subtraction():
    result = calculate(monthly_cells(), calculation_mode=CALCULATION_MODE_MONTHLY_SHEETS)

    actual = result["values"]["Budget"]["N18"]
    assert actual["type"] == "number"
    assert math.isclose(actual["value"], -5.0)
    assert result["cached_values_used"] is False
    assert result["coverage"]["combinations"] == ["MONTHLY_SAME_MONTH_SUBTRACT"]


@pytest.mark.parametrize("formula", ["='M10'!B16", "=M10!B16"])
def test_monthly_internal_mode_calculates_direct_sheet_reference(formula):
    result = calculate(monthly_cells(formula), calculation_mode=CALCULATION_MODE_MONTHLY_SHEETS)

    assert result["values"]["Budget"]["N18"] == {
        "type": "number",
        "value": 1001.0,
        "provenance": "ENGINE_CALCULATED",
    }
    assert result["coverage"]["combinations"] == ["MONTHLY_DIRECT_REFERENCE"]


def test_default_calculation_still_rejects_cross_sheet_references():
    with pytest.raises(WorkbookCareError):
        calculate(monthly_cells())


def test_python_unknown_monthly_mode_is_rejected():
    with pytest.raises(WorkbookCareError):
        calculate(monthly_cells(), calculation_mode="monthly_sheet")


@pytest.mark.parametrize(
    "formula",
    [
        "=M10!$B$16",
        "=M10!B16:M10!B17",
        "=M10!B16-M11!B15",
        "=Sheet1!A1",
        "=SUM(M10!B16)",
        "=[Book.xlsx]M10!B16",
    ],
)
def test_monthly_mode_rejects_unsupported_cross_sheet_grammar(formula):
    with pytest.raises(WorkbookCareError):
        formula_shape(
            formula,
            calculation_mode=CALCULATION_MODE_MONTHLY_SHEETS,
            current_sheet="Budget",
            sheet_names={"Budget", "M10", "M11"},
        )


def test_monthly_mode_rejects_missing_sheet_before_engine(monkeypatch):
    def fail_if_engine_started(*_args, **_kwargs):
        raise AssertionError("engine should not start")

    monkeypatch.setattr(subprocess, "Popen", fail_if_engine_started)
    cells = {"Budget": {"N18": {"type": "formula", "value": "='M10'!B16-'M10'!B15"}}}

    with pytest.raises(WorkbookCareError):
        calculate(cells, calculation_mode=CALCULATION_MODE_MONTHLY_SHEETS)


def test_monthly_mode_rejects_missing_reference_cell_before_engine(monkeypatch):
    def fail_if_engine_started(*_args, **_kwargs):
        raise AssertionError("engine should not start")

    monkeypatch.setattr(subprocess, "Popen", fail_if_engine_started)
    cells = monthly_cells()
    del cells["M10"]["B15"]

    with pytest.raises(WorkbookCareError) as exc_info:
        calculate(cells, calculation_mode=CALCULATION_MODE_MONTHLY_SHEETS)

    assert exc_info.value.code == "ENGINE_UNSUPPORTED"


def test_monthly_mode_rejects_cross_sheet_formula_cycles_before_engine(monkeypatch):
    def fail_if_engine_started(*_args, **_kwargs):
        raise AssertionError("engine should not start")

    monkeypatch.setattr(subprocess, "Popen", fail_if_engine_started)
    cells = {
        "M01": {"A1": {"type": "formula", "value": "=M02!A1"}},
        "M02": {"A1": {"type": "formula", "value": "=M01!A1"}},
    }

    with pytest.raises(WorkbookCareError):
        calculate(cells, calculation_mode=CALCULATION_MODE_MONTHLY_SHEETS)


def test_monthly_mode_rejects_non_numeric_operands_before_engine(monkeypatch):
    def fail_if_engine_started(*_args, **_kwargs):
        raise AssertionError("engine should not start")

    monkeypatch.setattr(subprocess, "Popen", fail_if_engine_started)
    cells = monthly_cells()
    cells["M10"]["B15"] = {"type": "text", "value": "1006"}

    with pytest.raises(WorkbookCareError):
        calculate(cells, calculation_mode=CALCULATION_MODE_MONTHLY_SHEETS)


@pytest.mark.parametrize(
    "value",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_monthly_mode_rejects_non_finite_operands_before_engine(monkeypatch, value):
    def fail_if_engine_started(*_args, **_kwargs):
        raise AssertionError("engine should not start")

    monkeypatch.setattr(subprocess, "Popen", fail_if_engine_started)
    cells = monthly_cells()
    cells["M10"]["B15"] = {"type": "number", "value": value}

    with pytest.raises(WorkbookCareError):
        calculate(cells, calculation_mode=CALCULATION_MODE_MONTHLY_SHEETS)


def test_monthly_formula_operand_allows_upstream_blank_when_operand_evaluates_number():
    cells = {
        "Budget": {"N18": {"type": "formula", "value": "=M10!B16-M10!B15"}},
        "M10": {
            "B16": {"type": "number", "value": 1001},
            "A2": {"type": "blank", "value": None},
            "B15": {"type": "formula", "value": "=A2"},
        },
    }
    result = calculate(cells, calculation_mode=CALCULATION_MODE_MONTHLY_SHEETS)
    assert result["values"]["M10"]["B15"] == {
        "type": "number",
        "value": 0.0,
        "provenance": "ENGINE_CALCULATED",
    }
    assert result["values"]["Budget"]["N18"] == {
        "type": "number",
        "value": 1001.0,
        "provenance": "ENGINE_CALCULATED",
    }


@pytest.mark.parametrize(
    ("kind", "value"),
    [
        ("text", "1006"),
        ("boolean", True),
        ("error", "#VALUE!"),
    ],
)
def test_monthly_formula_operand_rejects_nonnumeric_results(kind, value):
    formula_number = {
        "Budget": {"N18": {"type": "formula", "value": "=M10!B16-M10!B15"}},
        "M10": {
            "A1": {"type": "number", "value": 1001},
            "A2": {"type": "number", "value": 1006},
            "B16": {"type": "formula", "value": "=A1"},
            "B15": {"type": "formula", "value": "=A2"},
        },
    }
    result = calculate(formula_number, calculation_mode=CALCULATION_MODE_MONTHLY_SHEETS)
    assert result["values"]["Budget"]["N18"]["value"] == -5.0

    cells = {
        "Budget": {"N18": {"type": "formula", "value": "=M10!B16-M10!B15"}},
        "M10": {
            "B16": {"type": "number", "value": 1001},
            "A2": {"type": kind, "value": value},
            "B15": {"type": "formula", "value": "=A2"},
        },
    }
    with pytest.raises(WorkbookCareError):
        calculate(cells, calculation_mode=CALCULATION_MODE_MONTHLY_SHEETS)


def test_monthly_formula_operand_rejects_empty_text_result():
    cells = {
        "Budget": {"N18": {"type": "formula", "value": "=M10!B16-M10!B15"}},
        "M10": {
            "B16": {"type": "number", "value": 1001},
            "B15": {"type": "formula", "value": '=""'},
        },
    }
    with pytest.raises(WorkbookCareError):
        calculate(cells, calculation_mode=CALCULATION_MODE_MONTHLY_SHEETS)


def test_monthly_direct_blank_operand_rejects_before_engine(monkeypatch):
    def fail_if_engine_started(*_args, **_kwargs):
        raise AssertionError("engine should not start")

    monkeypatch.setattr(subprocess, "Popen", fail_if_engine_started)
    cells = monthly_cells()
    cells["M10"]["B15"] = {"type": "blank", "value": None}

    with pytest.raises(WorkbookCareError):
        calculate(cells, calculation_mode=CALCULATION_MODE_MONTHLY_SHEETS)


@pytest.mark.parametrize("reverse", [False, True])
def test_monthly_mode_near_1000_depth_rejects_without_recursion_error(
    monkeypatch, reverse
):
    def fail_if_engine_started(*_args, **_kwargs):
        raise AssertionError("engine should not start")

    monkeypatch.setattr(subprocess, "Popen", fail_if_engine_started)

    with pytest.raises(WorkbookCareError):
        calculate(
            monthly_chain(950, reverse=reverse),
            calculation_mode=CALCULATION_MODE_MONTHLY_SHEETS,
        )


def test_monthly_mode_allows_boundary_depth_and_valid_sheet_subtraction():
    chain = calculate(monthly_chain(101), calculation_mode=CALCULATION_MODE_MONTHLY_SHEETS)
    assert chain["values"]["M01"]["A1"]["value"] == 1.0

    with pytest.raises(WorkbookCareError):
        calculate(monthly_chain(102), calculation_mode=CALCULATION_MODE_MONTHLY_SHEETS)

    monthly = calculate(monthly_cells(), calculation_mode=CALCULATION_MODE_MONTHLY_SHEETS)
    assert monthly["values"]["Budget"]["N18"]["value"] == -5.0


def test_java_monthly_guard_rejects_raw_protocol_bypasses():
    non_numeric = _run_raw_java(
        [
            ("Budget", "N18", "formula", "=M10!B16-M10!B15"),
            ("M10", "B16", "number", 1001),
            ("M10", "B15", "text", "1006"),
        ],
        CALCULATION_MODE_MONTHLY_SHEETS,
    )
    assert non_numeric.returncode != 0

    cycle = _run_raw_java(
        [
            ("M01", "A1", "formula", "=M02!A1"),
            ("M02", "A1", "formula", "=M01!A1"),
        ],
        CALCULATION_MODE_MONTHLY_SHEETS,
    )
    assert cycle.returncode != 0

    depth_rows = [("M01", "A103", "number", 1)]
    depth_rows.extend(
        ("M01", f"A{index}", "formula", f"=M01!A{index + 1}")
        for index in range(102, 0, -1)
    )
    depth = _run_raw_java(depth_rows, CALCULATION_MODE_MONTHLY_SHEETS)
    assert depth.returncode != 0


def test_raw_java_protocol_rejects_unknown_and_malformed_modes():
    valid_rows = [("M10", "B16", "number", 1001)]

    unknown = _run_raw_java(valid_rows, "monthly_sheet")
    assert unknown.returncode != 0

    malformed = _run_raw_java(valid_rows, header="CALC_V1\tmonthly_sheet_internal\textra")
    assert malformed.returncode != 0


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity"])
def test_raw_java_monthly_guard_rejects_non_finite_numbers(value):
    result = _run_raw_java(
        [
            ("Budget", "N18", "formula", "=M10!B16-M10!B15"),
            ("M10", "B16", "number", 1001),
            ("M10", "B15", "number", value),
        ],
        CALCULATION_MODE_MONTHLY_SHEETS,
    )

    assert result.returncode == 20


def test_raw_java_default_mode_rejects_cross_sheet_reference():
    result = _run_raw_java(
        [
            ("Budget", "N18", "formula", "=M10!B16"),
            ("M10", "B16", "number", 1001),
        ]
    )

    assert result.returncode != 0


@pytest.mark.parametrize(
    "formula",
    [
        "=M10!$B$16",
        "=M10!B16:M10!B17",
        "=M10:M11!B16",
        "=[Book.xlsx]M10!B16",
        "=M10!B16-M11!B15",
        "=Sheet1!A1",
        "=SUM(M10!B16)",
    ],
)
def test_raw_java_monthly_mode_rejects_reference_grammar_negatives(formula):
    result = _run_raw_java(
        [
            ("Budget", "N18", "formula", formula),
            ("M10", "B16", "number", 1001),
            ("M10", "B15", "number", 1006),
            ("M11", "B15", "number", 1006),
            ("Sheet1", "A1", "number", 1001),
        ],
        CALCULATION_MODE_MONTHLY_SHEETS,
    )

    assert result.returncode != 0


def test_raw_java_monthly_mode_numeric_baseline_control():
    result = _run_raw_java(
        [
            ("Budget", "N18", "formula", "=M10!B16-M10!B15"),
            ("M10", "B16", "number", 1001),
            ("M10", "B15", "number", 1006),
        ],
        CALCULATION_MODE_MONTHLY_SHEETS,
    )

    assert result.returncode == 0
    rows = _decoded_java_rows(result.stdout)
    assert rows[("Budget", "N18")] == {"type": "number", "value": -5.0}
    assert rows[("M10", "B16")] == {"type": "number", "value": 1001.0}
    assert rows[("M10", "B15")] == {"type": "number", "value": 1006.0}


def test_java_monthly_guard_rejects_raw_range_chain_depth_bypass():
    rows = [("M01", "A103", "number", 1)]
    rows.extend(
        ("M01", f"A{index}", "formula", f"=SUM(A{index + 1}:A{index + 1})")
        for index in range(102, 0, -1)
    )

    result = _run_raw_java(rows, CALCULATION_MODE_MONTHLY_SHEETS)

    assert result.returncode != 0


def test_java_monthly_guard_rejects_huge_range_before_expansion():
    result = _run_raw_java(
        [
            ("M01", "A1", "formula", "=SUM(A1:XFD1048576)"),
        ],
        CALCULATION_MODE_MONTHLY_SHEETS,
        timeout=2.0,
    )

    assert result.returncode != 0
