from __future__ import annotations

import base64
import copy
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
import time

import pytest
from test_delivery_inputs import (
    ROOT,
    fixture,
    make_client,
    monthly_policy,
    monthly_workbook_bytes,
    policy,
)

from app.config import Settings
from app.delivery_api import get_store
from app.delivery_calculation import calculate, formula_shape, translate_formula
from app.delivery_inputs import (
    PROFILE_1,
    PROFILE_2,
    PROFILE_3,
    PROFILE_COMBINED,
    inspect_input,
    policy_scope,
    preflight,
)
from app.delivery_plan import build_plan, customer_plan, plan_digest, validate_plan
from app.delivery_process import process_limits
from app.delivery_rehearsal import entitled
from app.delivery_rights import payment_grant
from app.delivery_store import DeliveryStore
from app.errors import WorkbookCareError
from app.payment_plan_actions import reselect, restore_order

ORACLE = json.loads(
    (ROOT / "samples/delivery-v3_2/reference-cases.json").read_text(encoding="utf-8")
)


@pytest.mark.parametrize("case", ORACLE["cases"], ids=lambda c: c["id"])
def test_real_poi_matches_fixed_independent_oracle(case):
    cells = {
        a: {
            "type": "text"
            if isinstance(v, str)
            else "boolean"
            if isinstance(v, bool)
            else "number",
            "value": v,
        }
        for a, v in case["values"].items()
    }
    cells.update({a: {"type": "formula", "value": v} for a, v in case["formulas"].items()})
    result = calculate({"검증": cells})
    assert result["cached_values_used"] is False
    for address, expected in case["expected"].items():
        actual = result["values"]["검증"][address]
        assert actual["type"] == expected["type"]
        if actual["type"] == "number":
            assert math.isclose(actual["value"], expected["value"], rel_tol=1e-12, abs_tol=1e-12)
        else:
            assert actual["value"] == expected["value"]


def make_job(tmp_path):
    store = DeliveryStore(tmp_path)
    source = fixture.workbook_bytes()
    snapshot = inspect_input("synthetic.xlsx", source, Settings())
    return store, store.create("owner", source, snapshot, "synthetic-request-one")


def make_monthly_job(tmp_path, *, source=None):
    store = DeliveryStore(tmp_path)
    data = source or monthly_workbook_bytes()
    snapshot = inspect_input("monthly.xlsx", data, Settings())
    request_key = f"monthly-{hashlib.sha256(data).hexdigest()[:16]}"
    return store, store.create("owner", data, snapshot, request_key)


def test_whole_selected_set_and_subset_have_independent_impacts(tmp_path):
    store, job = make_job(tmp_path)
    both = build_plan(job, policy())
    single = build_plan(job, policy(targets=["B2"]))
    assert both["expected_calculated_values"]["검증"]["H2"]["value"] == 15500
    assert single["expected_calculated_values"]["검증"]["H2"]["value"] == 12000
    assert both["digest"] != single["digest"] and both["digest"] == plan_digest(both)
    assert both["exact_targets"] == [["검증", "B2"], ["검증", "B3"]]
    assert store.load("owner", job["id"])["source"] == fixture.workbook_bytes()
    assert both["source_cache_used"] is False


def test_monthly_profile_builds_exact_single_target_plan_from_actual_workbook(tmp_path):
    _store, job = make_monthly_job(tmp_path)
    plan = build_plan(job, monthly_policy())

    assert plan["profile_version"] == PROFILE_3
    assert plan["calculation_mode"] == "monthly_sheet_internal"
    assert plan["patches"] == [
        {
            **plan["patches"][0],
            "sheet": "Budget",
            "cell": "N18",
            "before": {"type": "formula", "value": "=N15-N14", "style": "0"},
            "after": {
                "type": "formula",
                "value": "='M10'!B16-'M10'!B15",
                "style": "0",
            },
            "change_kind": "MONTHLY_FORMULA_REPLACEMENT",
            "profile_version": PROFILE_3,
        }
    ]
    assert plan["expected_calculated_values"]["Budget"]["N18"] == {
        "type": "number",
        "value": -5.0,
        "provenance": "ENGINE_CALCULATED",
    }
    assert plan["exact_targets"] == [["Budget", "N18"]]
    assert plan["digest"] == plan_digest(plan)


def test_monthly_profile_rejects_normal_equivalent_and_no_eligible(tmp_path):
    for formula in ("='M10'!B16-'M10'!B15", "=N16-N15"):
        _store, job = make_monthly_job(
            tmp_path,
            source=monthly_workbook_bytes(target_formula=formula),
        )
        with pytest.raises(WorkbookCareError):
            build_plan(job, monthly_policy(before_formula=formula))

    _store, job = make_monthly_job(tmp_path)
    with pytest.raises(WorkbookCareError):
        build_plan(job, monthly_policy(targets=["O18"], before_formula="='M11'!B16-'M11'!B15"))


def test_monthly_profile_rejects_other_before_error_and_unsupported_source(tmp_path):
    def other_error(workbook):
        workbook["Budget"]["P20"] = "=P21/P22"
        workbook["Budget"]["P21"] = 1
        workbook["Budget"]["P22"] = 0

    _store, job = make_monthly_job(tmp_path, source=monthly_workbook_bytes(extra=other_error))
    with pytest.raises(WorkbookCareError) as existing_error:
        build_plan(job, monthly_policy())
    assert existing_error.value.code == "EXISTING_CALCULATION_ERROR"

    _store, job = make_monthly_job(
        tmp_path,
        source=monthly_workbook_bytes(target_formula="=OFFSET(N15,0,0)"),
    )
    with pytest.raises(WorkbookCareError):
        build_plan(job, monthly_policy(before_formula="=OFFSET(N15,0,0)"))


def test_combined_policy_calculates_once_against_frozen_complex03(tmp_path):
    source = (
        ROOT
        / "samples/WorkbookCare_Complex_Validation_2026-09-13/03_정산수정_연쇄계산.xlsx"
    ).read_bytes()
    sheet = "정산"
    store = DeliveryStore(tmp_path)
    job = store.create(
        "owner",
        source,
        inspect_input("complex03.xlsx", source, Settings()),
        "complex03-combined-request",
    )
    combined = {
        "profile": PROFILE_COMBINED,
        "items": [
            policy(
                PROFILE_1,
                ["B12", "B24", "B39", "B52", "B65", "B78", "B94", "B111"],
                sheet=sheet,
                role="AMOUNT",
            ),
            policy(
                PROFILE_2,
                ["F31", "F64", "F107"],
                sheet=sheet,
                anchor="F8",
                anchor_formula="=ROUND(C8*D8*(1-E8),0)",
            ),
        ],
    }
    plan = build_plan(job, combined)
    values = plan["expected_calculated_values"][sheet]
    assert len(plan["patches"]) == 11
    direct = {(p["sheet"], p["cell"]) for p in plan["patches"]}
    assert len([i for i in plan["impact"] if (i["sheet"], i["cell"]) not in direct]) == 42
    assert values["J130"]["value"] == 2177677
    assert [values[cell]["value"] for cell in ["F31", "F64", "F107"]] == [5232, 3551, 7800]
    assert plan["profile_version"] == PROFILE_COMBINED
    assert {p["profile_version"] for p in plan["patches"]} == {PROFILE_1, PROFILE_2}


def test_combined_policy_rejects_overlapping_targets(tmp_path):
    _, job = make_job(tmp_path)
    result = preflight(
        job["snapshot"],
        {
            "profile": PROFILE_COMBINED,
            "items": [policy(targets=["B2"]), policy(targets=["B2"])],
        },
    )
    assert result["status"] == "UNSUPPORTED"
    assert "OVERLAPPING_TARGETS" in result["reason_codes"]


def test_combined_paid_grant_allows_subset_but_rejects_expansion(tmp_path):
    store, job = make_job(tmp_path)
    combined = {
        "profile": PROFILE_COMBINED,
        "items": [policy(targets=["B2", "B3"]), policy(PROFILE_2, ["F3"])],
    }
    full = build_plan(job, combined)
    subset_policy = {"profile": PROFILE_COMBINED, "items": [policy(targets=["B2"])]}
    subset = build_plan(job, subset_policy)
    subset_ids = [patch["candidate_id"] for patch in subset["patches"]]

    def paid_candidate(plan, current_policy, scope_ids=None):
        state = {
            **job["state"],
            "payment": "PAID",
            "order_id": "order-1",
            "policy": current_policy,
            "plan": plan,
            "payment_grant": {
                "kind": "SANDBOX_ORDER",
                "mode": "LOCAL_CONTRACT",
                "owner": job["owner"],
                "job_id": job["id"],
                "order_id": "order-1",
                "product_id": job["product"],
                "expires_at": time.time() + 600,
                "input_hash": job["snapshot"]["source_hash"],
                "scope_ids": scope_ids or [patch["candidate_id"] for patch in full["patches"]],
                "profile": PROFILE_COMBINED,
                **policy_scope(combined),
            },
        }
        return {**job, "state": state}

    quantity_policy = {
        "profile": PROFILE_COMBINED,
        "items": [policy(targets=["B2"], role="QUANTITY")],
    }
    equivalent_anchor_policy = {
        "profile": PROFILE_COMBINED,
        "items": [
            policy(
                PROFILE_2,
                ["F3"],
                anchor="F4",
                anchor_formula="=ROUND(C4*D4*(1-E4),0)",
            )
        ],
    }

    assert payment_grant(paid_candidate(subset, subset_policy), "internal_beta")
    assert payment_grant(paid_candidate(full, combined, subset_ids), "internal_beta") is None
    assert payment_grant(
        paid_candidate(build_plan(job, quantity_policy), quantity_policy), "internal_beta"
    ) is None
    assert payment_grant(
        paid_candidate(build_plan(job, equivalent_anchor_policy), equivalent_anchor_policy),
        "internal_beta",
    ) is None


def test_combined_paid_grant_rejects_target_criteria_permutation(tmp_path):
    _, job = make_job(tmp_path)
    original_policy = {
        "profile": PROFILE_COMBINED,
        "items": [
            policy(targets=["B2"], role="AMOUNT"),
            policy(targets=["B3"], role="QUANTITY"),
        ],
    }
    swapped_policy = {
        "profile": PROFILE_COMBINED,
        "items": [
            policy(targets=["B3"], role="AMOUNT"),
            policy(targets=["B2"], role="QUANTITY"),
        ],
    }
    original = build_plan(job, original_policy)
    swapped = build_plan(job, swapped_policy)
    grant = {
        "kind": "SANDBOX_ORDER",
        "mode": "LOCAL_CONTRACT",
        "owner": job["owner"],
        "job_id": job["id"],
        "order_id": "order-1",
        "product_id": job["product"],
        "expires_at": time.time() + 600,
        "input_hash": job["snapshot"]["source_hash"],
        "scope_ids": [patch["candidate_id"] for patch in original["patches"]],
        "profile": PROFILE_COMBINED,
        **policy_scope(original_policy),
    }

    assert {patch["candidate_id"] for patch in swapped["patches"]} == set(grant["scope_ids"])
    assert (
        policy_scope(swapped_policy)["policy_item_base_hashes"]
        == grant["policy_item_base_hashes"]
    )
    assert payment_grant(
        {
            **job,
            "state": {
                **job["state"],
                "payment": "PAID",
                "order_id": "order-1",
                "policy": swapped_policy,
                "plan": swapped,
                "payment_grant": grant,
            },
        },
        "internal_beta",
    ) is None


def test_restore_order_rejects_combined_retained_item_criteria_change(tmp_path, monkeypatch):
    _, job = make_job(tmp_path)
    original_policy = {
        "profile": PROFILE_COMBINED,
        "items": [policy(targets=["B2"], role="AMOUNT")],
    }
    changed_scope = policy_scope(
        {
            "profile": PROFILE_COMBINED,
            "items": [policy(targets=["B2"], role="QUANTITY")],
        }
    )
    order = {
        "id": "wc_" + "1" * 32,
        "payment": "PAID",
        "cancel_requested": False,
        "refund": "NONE",
        "expires_at": time.time() + 600,
        "input_hash": job["snapshot"]["source_hash"],
        "product_id": job["product"],
        "profile": PROFILE_COMBINED,
        "scope_ids": [],
        **policy_scope(original_policy),
    }
    monkeypatch.setattr("app.payment_plan_actions.get_order", lambda *_args, **_kwargs: order)
    monkeypatch.setattr(
        "app.payment_plan_actions.supported_scope",
        lambda _job: {
            "profile": PROFILE_COMBINED,
            "scope_ids": [],
            "spec_hash": "same",
            **changed_scope,
        },
    )

    with pytest.raises(WorkbookCareError) as error:
        restore_order(None, job["owner"], order["id"], job)

    assert error.value.code == "ORDER_RESTORE_SOURCE_MISMATCH"


def test_restore_order_rejects_combined_target_anchor_permutation(tmp_path, monkeypatch):
    _, job = make_job(tmp_path)
    original_policy = {
        "profile": PROFILE_COMBINED,
        "items": [
            policy(PROFILE_2, ["F3"], anchor="F2", anchor_formula="=ROUND(C2*D2*(1-E2),0)"),
            policy(PROFILE_2, ["F5"], anchor="F4", anchor_formula="=ROUND(C4*D4*(1-E4),0)"),
        ],
    }
    swapped_scope = policy_scope(
        {
            "profile": PROFILE_COMBINED,
            "items": [
                policy(PROFILE_2, ["F5"], anchor="F2", anchor_formula="=ROUND(C2*D2*(1-E2),0)"),
                policy(PROFILE_2, ["F3"], anchor="F4", anchor_formula="=ROUND(C4*D4*(1-E4),0)"),
            ],
        }
    )
    order = {
        "id": "wc_" + "2" * 32,
        "payment": "PAID",
        "cancel_requested": False,
        "refund": "NONE",
        "expires_at": time.time() + 600,
        "input_hash": job["snapshot"]["source_hash"],
        "product_id": job["product"],
        "profile": PROFILE_COMBINED,
        "scope_ids": ["same-f3", "same-f5"],
        **policy_scope(original_policy),
    }
    monkeypatch.setattr("app.payment_plan_actions.get_order", lambda *_args, **_kwargs: order)
    monkeypatch.setattr(
        "app.payment_plan_actions.supported_scope",
        lambda _job: {
            "profile": PROFILE_COMBINED,
            "scope_ids": ["same-f3", "same-f5"],
            "spec_hash": "same",
            **swapped_scope,
        },
    )

    with pytest.raises(WorkbookCareError) as error:
        restore_order(None, job["owner"], order["id"], job)

    assert error.value.code == "ORDER_RESTORE_SOURCE_MISMATCH"


def test_restore_order_allows_combined_bound_subset_without_criteria_change(tmp_path, monkeypatch):
    _, job = make_job(tmp_path)
    original_policy = {
        "profile": PROFILE_COMBINED,
        "items": [
            policy(targets=["B2"], role="AMOUNT"),
            policy(targets=["B3"], role="QUANTITY"),
        ],
    }
    subset_scope = policy_scope(
        {"profile": PROFILE_COMBINED, "items": [policy(targets=["B2"], role="AMOUNT")]}
    )
    order = {
        "id": "wc_" + "3" * 32,
        "job_id": "old-job",
        "payment": "PAID",
        "cancel_requested": False,
        "refund": "NONE",
        "expires_at": time.time() + 600,
        "input_hash": job["snapshot"]["source_hash"],
        "product_id": job["product"],
        "profile": PROFILE_COMBINED,
        "scope_ids": ["kept"],
        "entitlement": "ACTIVE",
        "recovery": "SOURCE_REUPLOAD_OR_CANCEL",
        **policy_scope(original_policy),
    }

    class FakeDb:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, query, *_args):
            if query.startswith("SELECT expires FROM jobs"):
                return type("Rows", (), {"fetchone": lambda _self: {"expires": time.time() - 1}})()
            if query.startswith("SELECT state,revision FROM jobs"):
                return type(
                    "Rows",
                    (),
                    {
                        "fetchone": lambda _self: {
                            "state": json.dumps(job["state"]),
                            "revision": job["revision"],
                        }
                    },
                )()
            return self

        def fetchone(self):
            return None

    class FakeStore:
        def connection(self):
            return FakeDb()

    monkeypatch.setattr("app.payment_plan_actions.get_order", lambda *_args, **_kwargs: order)
    monkeypatch.setattr("app.payment_plan_actions.sync_job", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("app.payment_plan_actions.persist", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        "app.payment_plan_actions.supported_scope",
        lambda _job: {
            "profile": PROFILE_COMBINED,
            "scope_ids": ["kept"],
            "spec_hash": "same",
            **subset_scope,
        },
    )

    restored = restore_order(FakeStore(), job["owner"], order["id"], job)

    assert restored["id"] == order["id"]
    assert restored["job_id"] == job["id"]


def test_combined_reselection_preserves_item_scope_and_invalidates_outputs(tmp_path):
    store, job = make_job(tmp_path)
    combined = {
        "profile": PROFILE_COMBINED,
        "items": [policy(targets=["B2", "B3"]), policy(PROFILE_2, ["F3"])],
    }
    plan = build_plan(job, combined)
    job = store.update(
        job,
        job["revision"],
        {
            **job["state"],
            "policy": combined,
            "plan": plan,
            "approval": {"approved": True},
            "delivery": {"delivery_id": "old"},
            "status": "PREVIEW_VALIDATED",
        },
    )
    chosen = [
        patch["candidate_id"]
        for patch in plan["patches"]
        if (patch["profile_version"], patch["cell"]) in {(PROFILE_1, "B2"), (PROFILE_2, "F3")}
    ]

    updated = reselect(
        store,
        job,
        {
            "revision": job["revision"],
            "plan_digest": plan["digest"],
            "candidate_ids": chosen,
        },
        Settings(),
    )

    assert updated["state"]["policy"]["profile"] == PROFILE_COMBINED
    assert [item["targets"] for item in updated["state"]["policy"]["items"]] == [["B2"], ["F3"]]
    assert updated["state"]["approval"] is None
    assert updated["state"].get("delivery") is None
    assert len(updated["state"]["plan"]["patches"]) == 2


def test_rp02_exact_blank_translation_and_digest_invalidates_on_engine(tmp_path):
    store, job = make_job(tmp_path)
    p = policy(PROFILE_2, ["F3"])
    plan = build_plan(job, p)
    assert plan["patches"][0]["after"]["value"] == "=ROUND(C3*D3*(1-E3),0)"
    assert plan["expected_calculated_values"]["검증"]["F3"]["value"] == 6000
    assert plan["expected_calculated_values"]["검증"]["F12"]["value"] == 18200
    job = store.update(job, job["revision"], {**job["state"], "policy": p, "plan": plan})
    assert validate_plan(job)["digest"] == plan["digest"]
    with pytest.raises(WorkbookCareError):
        customer_plan(job, entitled=False)
    assert customer_plan(job, entitled=True)["patches"] == plan["patches"]
    changed = copy.deepcopy(job)
    changed["state"]["plan"]["engine_version"] = "changed"
    with pytest.raises(WorkbookCareError):
        validate_plan(changed)
    changed = copy.deepcopy(job)
    changed["state"]["policy"]["targets"] = ["F5"]
    with pytest.raises(WorkbookCareError):
        validate_plan(changed)


def test_mixed_absolute_discontinuous_reference_translation():
    anchor = "=ROUND($C2*D$2*(1-$E$2),0)"
    assert translate_formula(anchor, "F2", "F3") == "=ROUND($C3*D$2*(1-$E$2),0)"
    assert translate_formula(anchor, "F2", "H5") == "=ROUND($C5*F$2*(1-$E$2),0)"
    with pytest.raises(WorkbookCareError):
        translate_formula("=A1+B1", "B2", "A1")


@pytest.mark.parametrize(
    "formula",
    [
        "=IFERROR(UNKNOWN(A1),0)",
        '=IF(1,0,INDIRECT("A1"))',
        "=OFFSET(A1,1,0)",
        "=SUM(A1:A1048576)",
        "=ROUND(A1,2)",
    ],
)
def test_unsupported_never_becomes_iferror_zero(formula):
    with pytest.raises(WorkbookCareError):
        formula_shape(formula)


def test_circular_reference_and_hard_timeout_cleanup(tmp_path, monkeypatch):
    with pytest.raises(WorkbookCareError):
        calculate({"S": {"A1": {"type": "formula", "value": "=A1"}}})
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    real_popen = subprocess.Popen
    children = []

    def capture(*args, **kwargs):
        p = real_popen(*args, **kwargs)
        children.append(p)
        return p

    monkeypatch.setattr("app.delivery_calculation.subprocess.Popen", capture)
    with pytest.raises(WorkbookCareError) as error:
        calculate({"S": {"A1": {"type": "number", "value": 1}}}, timeout_seconds=0.001)
    assert error.value.code == "ENGINE_TIMEOUT"
    assert children and all(p.poll() is not None for p in children)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.skipif(
    os.name != "nt",
    reason="Windows Job Object exercised on Windows; Linux container limit separately verified",
)
def test_os_memory_limit_prevents_large_allocation():
    p = subprocess.Popen(
        [
            sys._base_executable,
            "-I",
            "-c",
            "import sys,os; print(os.getpid(),flush=True); sys.stdin.read(1); "
            "print('ALLOCATING',flush=True); bytearray(600*1024**2)",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    with process_limits(p):
        output, _ = p.communicate(b"x", timeout=10)
    assert int(output.splitlines()[0]) == p.pid
    assert b"ALLOCATING" in output and p.returncode != 0


def test_real_api_free_projection_cannot_grant_details_or_execution(tmp_path, monkeypatch):
    settings = Settings(
        app_env="internal_beta",
        delivery_beta_enabled=True,
        delivery_data_dir=str(tmp_path),
        cors_origins=["http://testserver"],
    )
    client = make_client(settings, monkeypatch)
    headers = {"Origin": "http://testserver", "X-WorkbookCare-CSRF": "1"}

    def action(body):
        return client.post("/v1/delivery", headers=headers, json=body)

    job = action(
        {
            "action": "create_input",
            "consent": True,
            "request_key": "synthetic-input-key-0001",
            "filename": "synthetic.xlsx",
            "file_base64": base64.b64encode(fixture.workbook_bytes()).decode(),
        }
    ).json()
    job = action(
        {
            "action": "preflight",
            "job_id": job["job_id"],
            "source_hash": job["source_hash"],
            "revision": job["revision"],
            "policy": policy(),
        }
    ).json()
    response = action(
        {
            "action": "prepare_plan",
            "job_id": job["job_id"],
            "source_hash": job["source_hash"],
            "revision": job["revision"],
        }
    )
    assert response.status_code == 200
    job = response.json()
    assert job["plan_summary"]["patch_count"] == 2 and "patches" not in json.dumps(job)
    assert not job["purchase_enabled"] and not job["internal_rehearsal"]
    assert action({"action": "plan_details", "job_id": job["job_id"]}).status_code == 403
    assert (
        action(
            {
                "action": "get",
                "job_id": job["job_id"],
                "internal_grant": {"kind": "INTERNAL_SYNTHETIC"},
            }
        ).status_code
        == 400
    )
    store = get_store()
    with store.connection() as db:
        owner = db.execute("SELECT owner FROM jobs WHERE id=?", (job["job_id"],)).fetchone()[
            "owner"
        ]
    private = store.load(owner, job["job_id"])
    grant = {
        "kind": "INTERNAL_SYNTHETIC",
        "job_id": job["job_id"],
        "source_hash": job["source_hash"],
        "expires_at": time.time() + 600,
    }
    private = store.update(
        private, private["revision"], {**private["state"], "internal_grant": grant}
    )
    assert (
        entitled(private, "internal_beta")
        and not entitled(private, "hosted_beta")
        and not entitled(private, "production")
    )
    assert action({"action": "plan_details", "job_id": job["job_id"]}).status_code == 200
    assert action({"action": "execute", "job_id": job["job_id"]}).status_code >= 400
