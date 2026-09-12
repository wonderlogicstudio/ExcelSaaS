from __future__ import annotations

import base64
import copy
import json
import math
import os
import subprocess
import sys
import tempfile
import time

import pytest
from test_delivery_inputs import ROOT, fixture, make_client, policy

from app.config import Settings
from app.delivery_api import get_store
from app.delivery_calculation import calculate, formula_shape, translate_formula
from app.delivery_inputs import PROFILE_2, inspect_input
from app.delivery_plan import build_plan, customer_plan, plan_digest, validate_plan
from app.delivery_process import process_limits
from app.delivery_rehearsal import entitled
from app.delivery_store import DeliveryStore
from app.errors import WorkbookCareError

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
