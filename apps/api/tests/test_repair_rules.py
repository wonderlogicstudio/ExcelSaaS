from __future__ import annotations

from test_delivery_inputs import fixture, policy
from test_delivery_plan import make_job

from app.config import Settings
from app.delivery_inputs import PROFILE_2, inspect_input, numeric_text, preflight
from app.delivery_plan import build_plan
from app.repair_rules.formula_restore import blank_formula_eligible, formula_restore_replacement
from app.repair_rules.numeric_text import numeric_text_eligible, numeric_text_replacement


def test_numeric_text_rule_matches_preflight_and_plan(tmp_path):
    snapshot = inspect_input("synthetic.xlsx", fixture.workbook_bytes(), Settings())
    sheet = next(iter(snapshot["cells"]))
    amount = snapshot["cells"][sheet]["B2"]
    identifier = snapshot["cells"][sheet]["A2"]

    assert numeric_text("12,000") == 12000
    assert numeric_text_eligible(amount)
    assert not numeric_text_eligible(identifier)
    assert numeric_text_replacement(amount) == {**amount, "type": "number", "value": 12000}
    for rejected in [identifier, {**amount, "special_format": True}]:
        try:
            numeric_text_replacement(rejected)
        except ValueError:
            pass
        else:
            raise AssertionError("ineligible numeric text record was replaced")

    gate = preflight(snapshot, policy(targets=["B2", "A2"]))
    decisions = {row["cell"]: row for row in gate["targets"]}
    assert gate["status"] == "UNSUPPORTED"
    assert decisions["B2"]["eligible"] is True
    assert decisions["A2"]["reason_codes"] == ["NOT_UNAMBIGUOUS_INTEGER_TEXT"]

    _, job = make_job(tmp_path)
    plan = build_plan(job, policy(targets=["B2"]))
    assert plan["patches"][0]["after"] == {"type": "number", "value": 12000, "style": "0"}


def test_formula_restore_rule_matches_preflight_and_plan(tmp_path):
    snapshot = inspect_input("synthetic.xlsx", fixture.workbook_bytes(), Settings())
    sheet = next(iter(snapshot["cells"]))
    blank = snapshot["cells"][sheet].get("F3", {"type": "blank", "value": None, "style": "0"})
    nonblank_formula = snapshot["cells"][sheet]["G3"]

    restored = formula_restore_replacement(blank, "=ROUND(C3*D3*(1-E3),0)")
    assert blank_formula_eligible(blank)
    assert not blank_formula_eligible(nonblank_formula)
    assert restored == {**blank, "type": "formula", "value": "=ROUND(C3*D3*(1-E3),0)"}

    gate = preflight(snapshot, policy(PROFILE_2, ["F3", "G3"]))
    decisions = {row["cell"]: row for row in gate["targets"]}
    assert gate["status"] == "UNSUPPORTED"
    assert decisions["F3"]["eligible"] is True
    assert decisions["G3"]["reason_codes"] == ["TARGET_NOT_TRUE_BLANK"]

    _, job = make_job(tmp_path)
    plan = build_plan(job, policy(PROFILE_2, ["F3"]))
    assert plan["patches"][0]["after"] == {
        "type": "formula",
        "value": "=ROUND(C3*D3*(1-E3),0)",
        "style": "0",
    }
