from __future__ import annotations

import copy
import hashlib
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

import pytest
from openpyxl import load_workbook
from test_delivery_inputs import ROOT, fixture, monthly_policy, policy

from app.config import Settings
from app.delivery_artifacts import validate_artifacts
from app.delivery_execution import approve, cancel, download, execute
from app.delivery_execution_control import ExecutionControl, controlled_process, execution_scope
from app.delivery_inputs import PROFILE_2, inspect_input
from app.delivery_patch import patch_workbook, verify_output
from app.delivery_plan import build_plan, plan_digest
from app.delivery_store import DeliveryStore
from app.errors import WorkbookCareError


@pytest.fixture(scope="module")
def blueprint(tmp_path_factory):
    store = DeliveryStore(tmp_path_factory.mktemp("blueprint"))
    data = fixture.workbook_bytes()
    job = store.create(
        "owner", data, inspect_input("s.xlsx", data, Settings()), "blueprint-unique-request"
    )
    p = policy(PROFILE_2, ["F3"])
    return job, p, build_plan(job, p)


@pytest.fixture(autouse=True)
def current_patch_compatibility(monkeypatch):
    monkeypatch.setattr(
        "app.delivery_execution.compatibility_status",
        lambda: {"status": "PASS", "excel_version": "test", "profiles": ["test"]},
    )


def prepared(tmp_path, blueprint):
    original, p, plan = blueprint
    store = DeliveryStore(tmp_path)
    job = store.create(
        "owner", original["source"], original["snapshot"], "execution-unique-request"
    )
    plan = copy.deepcopy(plan)
    plan["job_id"] = job["id"]
    plan["expires_at"] = min(time.time() + 600, job["expires"])
    plan["digest"] = plan_digest(plan)
    grant = {
        "kind": "INTERNAL_SYNTHETIC",
        "job_id": job["id"],
        "source_hash": job["snapshot"]["source_hash"],
        "expires_at": job["expires"],
    }
    job = store.update(
        job,
        job["revision"],
        {
            **job["state"],
            "policy": p,
            "plan": plan,
            "status": "PREVIEW_VALIDATED",
            "internal_grant": grant,
        },
    )
    settings = Settings(app_env="internal_beta")
    return store, job, settings


def authorized(store, job, settings):
    plan = job["state"]["plan"]
    return approve(
        store,
        job,
        {
            "revision": job["revision"],
            "plan_digest": plan["digest"],
            "candidate_ids": [p["candidate_id"] for p in plan["patches"]],
            "acknowledge_exact_changes": True,
        },
        settings,
    )


def monthly_source() -> bytes:
    path = ROOT / "artifacts/synthetic_validation/monthly-repair-flow06/stage3"
    return (path / "monthly-rp03-supported-6sheet.xlsx").read_bytes()


def prepared_monthly(tmp_path):
    source = monthly_source()
    store = DeliveryStore(tmp_path)
    job = store.create(
        "owner",
        source,
        inspect_input("monthly.xlsx", source, Settings()),
        "monthly-execution-request",
    )
    plan = build_plan(job, monthly_policy())
    grant = {
        "kind": "INTERNAL_SYNTHETIC",
        "job_id": job["id"],
        "source_hash": job["snapshot"]["source_hash"],
        "expires_at": job["expires"],
    }
    job = store.update(
        job,
        job["revision"],
        {
            **job["state"],
            "policy": monthly_policy(),
            "plan": plan,
            "status": "PREVIEW_VALIDATED",
            "internal_grant": grant,
        },
    )
    return store, job, Settings(app_env="internal_beta")


def test_separate_approval_and_actual_atomic_delivery_redownload(tmp_path, blueprint):
    store, job, settings = prepared(tmp_path, blueprint)
    with pytest.raises(WorkbookCareError) as e:
        execute(store, job, settings)
    assert e.value.code == "CURRENT_APPROVAL_REQUIRED"
    job = authorized(store, job, settings)
    assert job["state"]["payment"] == "NOT_PURCHASED"
    result = execute(store, job, settings)
    assert result["state"]["status"] == "READY"
    for kind in ["REPAIRED_XLSX", "CHANGES_XLSX", "VERIFICATION_HTML"]:
        artifact = download(store, result, kind, settings)
        assert artifact == download(store, result, kind, settings)
    again = execute(store, result, settings)
    assert again["state"]["delivery"]["delivery_id"] == result["state"]["delivery"]["delivery_id"]
    assert store.load("owner", job["id"])["source"] == job["source"]
    with pytest.raises(WorkbookCareError):
        store.load("other-owner", job["id"])
    with store.connection() as db:
        assert db.execute("SELECT COUNT(*) FROM delivery_artifacts").fetchone()[0] == 3
        db.execute("DELETE FROM delivery_artifacts WHERE kind='CHANGES_XLSX'")
    with pytest.raises(WorkbookCareError) as e:
        download(store, result, "REPAIRED_XLSX", settings)
    assert e.value.code == "INCOMPLETE_PACKAGE"
    store.delete("owner", job["id"])
    with store.connection() as db:
        assert db.execute("SELECT COUNT(*) FROM delivery_artifacts").fetchone()[0] == 0


@pytest.mark.parametrize(
    "mutation",
    ["digest", "no_ack", "subset", "expired", "wrong_sku", "production", "policy_changed"],
)
def test_invalid_approval_or_right_is_blocked(tmp_path, blueprint, mutation):
    store, job, settings = prepared(tmp_path, blueprint)
    p = job["state"]["plan"]
    body = {
        "revision": job["revision"],
        "plan_digest": p["digest"],
        "candidate_ids": [v["candidate_id"] for v in p["patches"]],
        "acknowledge_exact_changes": True,
    }
    if mutation == "digest":
        body["plan_digest"] = "0" * 64
    if mutation == "no_ack":
        body["acknowledge_exact_changes"] = False
    if mutation == "subset":
        body["candidate_ids"] = []
    if mutation == "expired":
        job["state"]["internal_grant"]["expires_at"] = time.time() - 1
    if mutation == "wrong_sku":
        job["product"] = "COMPARISON_REPORT"
    if mutation == "production":
        settings = Settings(
            app_env="production",
            cors_origins=["https://synthetic.example"],
            control_plane_hmac_secret="synthetic-test-proof-key-000000000000",
        )
    if mutation == "policy_changed":
        job["state"]["policy"] = {**job["state"]["policy"], "targets": ["F5"]}
    with pytest.raises(WorkbookCareError):
        approve(store, job, body, settings)
    assert not store.load("owner", job["id"])["state"].get("approval")


def test_missing_artifact_quarantines_no_partial_success(tmp_path, blueprint, monkeypatch):
    store, job, settings = prepared(tmp_path, blueprint)
    job = authorized(store, job, settings)
    from app.delivery_artifacts import make_artifacts

    def missing(*args):
        p = make_artifacts(*args)
        p["artifacts"].pop("CHANGES_XLSX")
        return p

    monkeypatch.setattr("app.delivery_execution.make_artifacts", missing)
    with pytest.raises(WorkbookCareError):
        execute(store, job, settings)
    current = store.load("owner", job["id"])
    assert current["state"]["status"] == "QUARANTINED"
    with pytest.raises(WorkbookCareError):
        download(store, current, "REPAIRED_XLSX", settings)
    with store.connection() as db:
        assert db.execute("SELECT COUNT(*) FROM delivery_artifacts").fetchone()[0] == 0


def test_cancel_fence_prevents_late_publication_and_duplicate_worker(
    tmp_path, blueprint, monkeypatch
):
    store, job, settings = prepared(tmp_path, blueprint)
    job = authorized(store, job, settings)
    from app.delivery_artifacts import make_artifacts

    waiting = threading.Event()
    release = threading.Event()

    def pause(*args):
        p = make_artifacts(*args)
        waiting.set()
        assert release.wait(30)
        return p

    monkeypatch.setattr("app.delivery_execution.make_artifacts", pause)
    with ThreadPoolExecutor() as pool:
        future = pool.submit(execute, store, job, settings)
        assert waiting.wait(30)
        current = store.load("owner", job["id"])
        assert execute(store, current, settings)["state"]["status"] == "RUNNING"
        requested = cancel(store, current)
        assert requested["state"]["status"] == "CANCEL_REQUESTED"
        release.set()
        with pytest.raises(WorkbookCareError):
            future.result(30)
    assert store.load("owner", job["id"])["state"]["status"] == "CANCELLED"
    with store.connection() as db:
        assert db.execute("SELECT COUNT(*) FROM delivery_artifacts").fetchone()[0] == 0


def test_actual_owned_process_is_killed_before_cancel_finishes():
    control = ExecutionControl()
    child = subprocess.Popen(
        [sys._base_executable, "-c", "import time; time.sleep(60)"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        with execution_scope(control), controlled_process(child):
            control.cancel()
            child.wait(timeout=5)
            assert child.poll() is not None
            assert not control.finished.is_set()
    finally:
        if child.poll() is None:
            child.kill()
            child.wait()


def test_package_references_and_existing_calculation_errors(tmp_path, blueprint):
    store, job, settings = prepared(tmp_path, blueprint)
    bad = copy.deepcopy(job)
    bad["snapshot"]["cells"]["검증"]["F2"]["value"] = "=C2/E3"
    with pytest.raises(WorkbookCareError) as e:
        build_plan(bad, policy())
    assert e.value.code == "EXISTING_CALCULATION_ERROR"
    with pytest.raises(WorkbookCareError):
        validate_artifacts({"manifest": {"files": {}}, "artifacts": {}}, job["state"]["plan"])


def test_monthly_actual_patch_and_verification_resolves_target_candidate(tmp_path):
    source = monthly_source()
    source_hash = hashlib.sha256(source).hexdigest()
    store = DeliveryStore(tmp_path)
    job = store.create(
        "owner",
        source,
        inspect_input("monthly.xlsx", source, Settings()),
        "monthly-actual-patch",
    )
    plan = build_plan(job, monthly_policy())
    repaired = patch_workbook(source, job["snapshot"], plan)
    verification = verify_output(source, repaired, plan, Settings())

    assert hashlib.sha256(source).hexdigest() == source_hash
    assert plan["expected_calculated_values"]["Budget"]["N18"] == {
        "type": "number",
        "value": -5.0,
        "provenance": "ENGINE_CALCULATED",
    }
    assert verification["formula_candidates_remaining"] == 0
    assert verification["detectors"]["formula"]["target_remaining"] == []
    workbook = load_workbook(BytesIO(repaired), data_only=False, read_only=False)
    try:
        assert workbook["Budget"]["N18"].value == "='M10'!B16-'M10'!B15"
        assert workbook["M10"]["B15"].value == 1006
        assert workbook["M10"]["B16"].value == 1001
    finally:
        workbook.close()


def test_monthly_execute_requires_current_approval_and_rule_fingerprint(tmp_path):
    store, job, settings = prepared_monthly(tmp_path)
    with pytest.raises(WorkbookCareError) as missing:
        execute(store, job, settings)
    assert missing.value.code == "CURRENT_APPROVAL_REQUIRED"

    stale_plan = copy.deepcopy(job["state"]["plan"])
    stale_plan["repair_rule_fingerprint"] = "0" * 64
    stale_plan["digest"] = plan_digest(stale_plan)
    stale = {**job, "state": {**job["state"], "plan": stale_plan}}
    with pytest.raises(WorkbookCareError) as stale_error:
        execute(store, stale, settings)
    assert stale_error.value.code == "STALE_PLAN"

    missing_plan = copy.deepcopy(job["state"]["plan"])
    missing_plan.pop("repair_rule_fingerprint")
    missing_plan["digest"] = plan_digest(missing_plan)
    missing = {**job, "state": {**job["state"], "plan": missing_plan}}
    with pytest.raises(WorkbookCareError) as missing_error:
        execute(store, missing, settings)
    assert missing_error.value.code == "STALE_PLAN"
