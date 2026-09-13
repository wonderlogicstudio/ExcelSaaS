"""Compare actual product code with a separately frozen complex synthetic oracle."""

from pathlib import Path
import argparse, hashlib, json, sys, tempfile, time

ROOT = Path(__file__).resolve().parents[1]
if not (ROOT / "apps/api").exists():
    ROOT = Path(r"C:\Users\JinwonLee\project\ExcelSaaS")
PACK = ROOT / "samples/WorkbookCare_Complex_Validation_2026-09-13"
sys.path.insert(0, str(ROOT / "apps/api"))
from app.config import Settings
from app.scanner import scan_workbook, run_formula_audit
from app.delivery_inputs import inspect_input, preflight
from app.delivery_plan import build_plan
from app.delivery_store import DeliveryStore
from app.errors import WorkbookCareError
from app.comparison_engine import compare_sources, read_source


def oracle():
    data = (PACK / "expected/expected.json").read_bytes()
    assert (
        hashlib.sha256(data).hexdigest()
        == (PACK / "expected/ORACLE_LOCK.sha256").read_text().split()[0]
    )
    return json.loads(data)


def settings():
    return Settings(
        app_env="internal_beta",
        formula_pattern_audit_enabled=True,
        scan_cell_limit=250000,
        finding_limit=5000,
    )


def policy(case):
    return {
        "profile": case["profile"],
        "sheet": case["sheet"],
        "targets": case["targets"],
        "role": "AMOUNT",
        "confirmed": True,
        "anchor": case["anchor"],
        "anchor_formula": case["anchor_formula"],
    }


def comparison_spec(controls, capacity=False):
    common = {
        "period": "2026-09 synthetic",
        "amount_meaning": "총액",
        "currency": "KRW",
        "unit": "KRW_WON",
    }
    result = {
        s: {
            "sheet": "CSV" if capacity else "거래",
            "range": f"A1:{'B' if capacity else 'E'}{controls[s]['rows'] + 1}",
            "header_row": 1,
            "key_columns": ["A"] if capacity else ["A", "B"],
            "amount_column": "B" if capacity else "D",
            "exclusions": [],
            "criteria": common,
        }
        for s in ["A", "B"]
    }
    result["policy"] = {
        **common,
        "confirmed": True,
        "normalization": "NONE",
        "tolerance_krw": "0",
    }
    return result


def check_diagnosis(file, expected):
    payload = (PACK / file).read_bytes()
    scan = scan_workbook(file, payload, settings())
    audit = run_formula_audit(file, payload, settings())
    actual = sorted(
        (f.sheet, f.cell, f.rule_code, f.formula_pattern.pattern_subtype)
        for f in audit.candidates
    )
    wanted = sorted(
        (f["sheet"], f["cell"], f["rule_code"], f["subtype"]) for f in expected["m4"]
    )
    assert audit.status == "COMPLETED", audit.status
    assert actual == wanted, {
        "missing": list(set(wanted) - set(actual)),
        "unexpected": list(set(actual) - set(wanted)),
    }
    findings = sorted((f.sheet, f.cell, f.rule_code) for f in scan.findings)
    assert findings == sorted(
        (f["sheet"], f["cell"], f["rule_code"]) for f in expected["structure_locations"]
    ), {"actual_structure": findings}
    return {
        "m4_candidates": len(actual),
        "structure_findings": len(findings),
        "expected_exact": True,
        "manual_exceptions_not_flagged": True,
    }


def check_plan(label, case):
    payload = (PACK / case["file"]).read_bytes()
    snap = inspect_input(case["file"], payload, settings())
    p = policy(case)
    gate = preflight(snap, p)
    assert (
        gate["eligible_count"] == case["patch_count"]
        and gate["status"] == "PRELIMINARY_ONLY"
    ), gate
    with tempfile.TemporaryDirectory(prefix="workbookcare-complex-plan-") as folder:
        store = DeliveryStore(Path(folder))
        job = store.create("synthetic-complex", payload, snap, "complex-" + label)
        plan = build_plan(job, p)
        assert len(plan["patches"]) == case["patch_count"]
        for c, v in case["expected"].items():
            got = plan["expected_calculated_values"][case["sheet"]][c]
            assert got["type"] == v["type"] and got["value"] == v["value"], {
                "cell": c,
                "expected": v,
                "actual": got,
            }
        actual = {(r["sheet"], r["cell"]) for r in plan["impact"]}
        assert actual == {(case["sheet"], c) for c in case["impact"]}, {
            "impact_diff": list(actual ^ {(case["sheet"], c) for c in case["impact"]})
        }
        for c, f in case["restored_formulas"].items():
            assert (
                next(x for x in plan["patches"] if x["cell"] == c)["after"]["value"]
                == f
            )
        return {
            "patches": len(plan["patches"]),
            "exact_values": len(case["expected"]),
            "impact_cells": len(actual),
            "formula_count": plan["coverage"]["formula_count"],
            "sum_after": case["sum_after"],
            "expected_exact": True,
        }


def check_comparison(expected):
    sources = {
        side: read_source(file, (PACK / file).read_bytes(), settings())
        for side, file in expected["files"].items()
    }
    result = compare_sources(sources, comparison_spec(expected["controls"]))
    summary = result["summary"]
    assert summary["counts"] == expected["counts"], summary["counts"]
    assert summary["group_count"] == expected["groups"]
    for side in ["A", "B"]:
        control = expected["controls"][side]
        assert (
            summary["input_rows"][side] == control["rows"]
            and summary["known_amount_totals"][side] == control["known_amount"]
            and summary["unknown_amount_row_counts"][side]
            == control["unknown_amount_rows"]
        ), summary
        actual_rows = [r for record in result["records"] for r in record[side]]
        assert len(actual_rows) == control["rows"]
        for row in expected["physical_rows"][side]:
            actual = next(
                g
                for g in result["records"]
                if any(x["physical_row"] == row["physical_row"] for x in g[side])
            )
            assert actual["status"] == row["status"]
    assert (
        next(r for r in result["records"] if r["key_parts"] == ["정밀", "BIG"])["delta"]
        == "1"
    )
    return {
        "summary": summary,
        "all_source_row_classes_match": True,
        "big_integer_delta": "1",
        "B_is_truth": False,
    }


def check_negative(case):
    payload = (PACK / case["file"]).read_bytes()
    if case["stage"] == "repair_input":
        try:
            inspect_input(case["file"], payload, settings())
        except WorkbookCareError as error:
            assert error.code == case["error_code"]
            return {"error_code": error.code, "expected_block": True}
        raise AssertionError("Expected input rejection")
    snap = inspect_input(case["file"], payload, settings())
    p = policy(oracle()["repair"]["RP01_ALL"])
    p.update({k: case[k] for k in ["profile", "targets", "role"] if k in case})
    if case["file"].startswith("04"):
        p.update(sheet="거래원장", targets=["C2"])
    gate = preflight(snap, p)
    reasons = set(gate["reason_codes"]) | {
        c for t in gate["targets"] for c in t["reason_codes"]
    }
    assert set(case["required_reasons"]) <= reasons, reasons
    assert gate["eligible_count"] == 0 and not gate["purchase_enabled"]
    return {"expected_block": True, "reasons": sorted(reasons)}


def check_capacity(expected):
    name = expected["supported_file"]
    source = read_source(name, (PACK / name).read_bytes(), settings())
    result = compare_sources(
        {"A": source, "B": source},
        comparison_spec({"A": {"rows": 1000}, "B": {"rows": 1000}}, True),
    )
    summary = result["summary"]
    assert summary["counts"]["MATCHED"] == 1000 and summary["known_amount_totals"] == {
        "A": expected["known_amount"],
        "B": expected["known_amount"],
    }
    try:
        read_source(
            expected["rejected_file"],
            (PACK / expected["rejected_file"]).read_bytes(),
            settings(),
        )
    except WorkbookCareError as e:
        assert e.code == expected["error_code"]
        return {
            "supported_rows": 1000,
            "known_amount": expected["known_amount"],
            "rejected_rows": 1001,
            "expected_block": True,
            "report_generated": False,
        }
    raise AssertionError("1001-row input was not blocked")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    o = oracle()
    rows = []
    cases = [
        *(
            ("diagnosis:" + n, lambda n=n, e=e: check_diagnosis(n, e))
            for n, e in o["diagnosis"].items()
        ),
        *((n, lambda n=n, e=e: check_plan(n, e)) for n, e in o["repair"].items()),
        ("comparison", lambda: check_comparison(o["comparison"])),
        *(
            (f"negative:{i}", lambda c=c: check_negative(c))
            for i, c in enumerate(o["negative"])
        ),
        ("capacity", lambda: check_capacity(o["capacity"])),
    ]
    for name, run in cases:
        start = time.monotonic()
        try:
            result = run()
            row = {"case": name, "status": "PASS", "result": result}
        except Exception as error:
            row = {
                "case": name,
                "status": "FAIL",
                "error_type": type(error).__name__,
                "error_code": getattr(error, "code", None),
                "detail": str(error)[:2000],
            }
        row["seconds"] = round(time.monotonic() - start, 3)
        rows.append(row)
        print(
            json.dumps(
                {"case": name, "status": row["status"], "seconds": row["seconds"]}
            ),
            flush=True,
        )
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    assert not args.evidence.exists()
    args.evidence.write_text(
        json.dumps(
            {
                "kind": "ACTUAL_LOCAL_PRODUCT_VS_FROZEN_COMPLEX_ORACLES",
                "rows": rows,
                "official_pg_verified": False,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return 0 if all(r["status"] == "PASS" for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
