from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from test_comparison_engine import BASE, spec_for
from test_comparison_service import inputs
from test_comparison_service import prepared as comparison_prepared
from test_delivery_execution import authorized, prepared
from test_delivery_execution import blueprint as blueprint
from test_delivery_inputs import make_client
from test_payment_delivery import contract_settings, order_for

from app.config import Settings
from app.delivery_execution import CONTROLS, CONTROLS_LOCK
from app.delivery_execution_control import ExecutionControl
from app.delivery_operations import DeliveryPrivacyMiddleware, bounded_body, claim_attempt, maintain
from app.delivery_plan import validate_plan
from app.errors import WorkbookCareError
from app.payment_service import get_order, list_orders, project_order, seed_contract


def test_expired_plan_is_scrubbed_and_old_approval_cannot_execute(tmp_path, blueprint):
    store, job, settings = prepared(tmp_path, blueprint)
    job = authorized(store, job, settings)
    before = job["state"]["plan"]["expires_at"]
    maintain(store, before + 1)
    current = store.load("owner", job["id"])
    assert current["state"]["plan"] is None and current["state"]["approval"] is None
    assert current["state"]["status"] == "PLAN_EXPIRED"
    assert current["source"] == job["source"]
    with pytest.raises(WorkbookCareError):
        validate_plan(current)


def test_two_sources_artifacts_and_private_state_expire_but_order_remains(tmp_path):
    store, job, settings = comparison_prepared(tmp_path)
    settings = contract_settings(settings)
    order = seed_contract(store, order_for(store, job, settings), settings)
    sentinel = "SYNTHETIC_PRIVATE_SENTINEL_NEVER_LOG_07"
    with store.connection() as db:
        state = json.loads(db.execute("SELECT state FROM jobs").fetchone()[0])
        state["private_test_value"] = sentinel
        db.execute("UPDATE jobs SET state=?", (json.dumps(state),))
        db.execute(
            "INSERT INTO delivery_artifacts VALUES (?,?,?,?,?)",
            (job["id"], "probe", "opaque", sentinel.encode(), "{}"),
        )
    assert sentinel.encode() in store.path.read_bytes()
    assert maintain(store, job["expires"] + 1) == 1
    with store.connection() as db:
        for table in ["jobs", "secondary_sources", "delivery_artifacts", "delivery_usage"]:
            assert db.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 0
    assert sentinel.encode() not in store.path.read_bytes()
    projected = project_order(store, get_order(store, "owner", order["id"]))
    assert projected["job_status"] == "INPUT_EXPIRED" and projected["payment"] == "PAID"
    assert sentinel not in json.dumps(projected)
    maintain(store, order["expires_at"] + 1)
    assert not list_orders(store, "owner")
    with store.connection() as db:
        for table in [
            "payment_orders",
            "payment_outbox",
            "payment_events",
            "payment_contract_receipts",
        ]:
            assert db.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 0


def test_lost_execution_lease_fences_and_cancels_owned_process(tmp_path, blueprint):
    store, job, settings = prepared(tmp_path, blueprint)
    state = {
        **job["state"],
        "status": "RUNNING",
        "lease_expires_at": time.time() - 1,
        "publication_fence": "old",
    }
    store.update(job, job["revision"], state)
    control = ExecutionControl()
    key = (str(store.path), job["id"])
    with CONTROLS_LOCK:
        CONTROLS[key] = control
    try:
        maintain(store)
        current = store.load("owner", job["id"])
        assert control.cancelled.is_set()
        assert current["state"]["status"] == "QUARANTINED"
        assert current["state"]["publication_fence"] != "old"
        assert current["state"]["approval"] is None
    finally:
        with CONTROLS_LOCK:
            CONTROLS.pop(key, None)


def test_attempt_limit_is_atomic_under_concurrency(tmp_path, blueprint):
    store, job, _ = prepared(tmp_path, blueprint)

    def claim(_):
        try:
            claim_attempt(store, job, "EXECUTION")
            return True
        except WorkbookCareError as error:
            assert error.code == "DELIVERY_ATTEMPT_LIMIT"
            return False

    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(claim, range(12))) == 3
    assert store.load("owner", job["id"])["state"] == job["state"]


def test_streaming_body_limit_stops_before_remaining_payload():
    read = []

    class Request:
        async def stream(self):
            for i in range(20):
                read.append(i)
                yield b"x" * 1024**2

    with pytest.raises(WorkbookCareError) as error:
        asyncio.run(bounded_body(Request()))
    assert error.value.status_code == 413 and len(read) == 6


def test_actual_private_api_owner_csrf_refund_cache_and_kill_switch(tmp_path, monkeypatch, caplog):
    import app.delivery_api as api

    caplog.set_level("INFO")
    settings = Settings(
        app_env="internal_beta",
        payment_mode="LOCAL_CONTRACT",
        delivery_beta_enabled=True,
        delivery_data_dir=str(tmp_path),
    )
    client = make_client(settings, monkeypatch)
    client.app.add_middleware(DeliveryPrivacyMiddleware)
    headers = {"Origin": "http://localhost:5173", "X-WorkbookCare-CSRF": "1"}
    request = inputs()
    request["sources"]["A"]["filename"] = "SYNTHETIC_PRIVATE_FILENAME_07.csv"
    uploaded = client.post(
        "/v1/delivery", headers=headers, json={"action": "create_comparison", **request}
    )
    assert uploaded.status_code == 200
    job = uploaded.json()
    response = client.post(
        "/v1/delivery",
        headers=headers,
        json={
            "action": "prepare_comparison",
            "job_id": job["job_id"],
            "revision": job["revision"],
            "source_pair_hash": job["source_pair_hash"],
            "spec": spec_for(BASE["A"], BASE["B"]),
        },
    )
    assert response.status_code == 200
    response = client.post(
        "/v1/delivery",
        headers=headers,
        json={
            "action": "order_create",
            "job_id": job["job_id"],
            "request_key": "private-api-order-07",
            "acknowledge_test_only": True,
            "acknowledge_limitations": True,
        },
    )
    assert response.status_code == 200
    order_id = response.json()["order_id"]
    owner = hashlib.sha256(client.cookies.get("workbookcare_local_session").encode()).hexdigest()
    store = api.get_store()
    seed_contract(store, get_order(store, owner, order_id), settings)
    other = make_client(settings, monkeypatch)
    other.app.add_middleware(DeliveryPrivacyMiddleware)
    for body in [
        {"action": "get", "job_id": job["job_id"]},
        {
            "action": "comparison_download",
            "job_id": job["job_id"],
            "kind": "COMPARISON_REPORT_XLSX",
        },
        {"action": "order_get", "order_id": order_id},
        {"action": "order_cancel", "order_id": order_id},
    ]:
        response = other.post("/v1/delivery", headers=headers, json=body)
        assert response.status_code == 404 and "no-store" in response.headers["cache-control"]
    for bad_headers in [
        {},
        {"Origin": "https://evil.invalid", "X-WorkbookCare-CSRF": "1"},
        {"Origin": "http://localhost:5173"},
    ]:
        response = client.post(
            "/v1/delivery", headers=bad_headers, json={"action": "order_get", "order_id": order_id}
        )
        assert response.status_code == 403 and "no-store" in response.headers["cache-control"]
    response = client.post(
        "/v1/delivery",
        headers=headers,
        json={
            "action": "execute_comparison",
            "job_id": job["job_id"],
            "acknowledge_limitations": True,
        },
    )
    assert response.status_code == 200 and response.json()["status"] == "READY"
    assert response.headers["referrer-policy"] == "no-referrer"
    for kind in ["COMPARISON_REPORT_XLSX", "COMPARISON_VERIFICATION_HTML"]:
        response = client.post(
            "/v1/delivery",
            headers=headers,
            json={"action": "comparison_download", "job_id": job["job_id"], "kind": kind},
        )
        assert response.status_code == 200 and "no-store" in response.headers["cache-control"]
        assert base64.b64decode(response.json()["file_base64"])
    assert (
        client.post(
            "/v1/delivery", headers=headers, json={"action": "order_cancel", "order_id": order_id}
        ).json()["refund"]
        == "SUCCEEDED"
    )
    assert (
        client.post(
            "/v1/delivery",
            headers=headers,
            json={
                "action": "comparison_download",
                "job_id": job["job_id"],
                "kind": "COMPARISON_REPORT_XLSX",
            },
        ).status_code
        == 403
    )
    monkeypatch.setattr(
        api, "get_settings", lambda: settings.model_copy(update={"delivery_beta_enabled": False})
    )
    assert (
        client.post("/v1/delivery", headers=headers, json={"action": "orders"}).status_code == 404
    )
    assert "SYNTHETIC_PRIVATE_FILENAME_07" not in caplog.text
    assert "0004" not in caplog.text and "test_sk_" not in caplog.text


def test_report_process_deadline_reaps_child_and_scratch(tmp_path, monkeypatch):
    from app.comparison_process import run_comparison

    store, job, _ = comparison_prepared(tmp_path)
    children = []
    original = subprocess.Popen

    def capture(*args, **kwargs):
        child = original(*args, **kwargs)
        children.append((child, Path(kwargs["cwd"])))
        return child

    monkeypatch.setattr("app.comparison_process.subprocess.Popen", capture)
    with pytest.raises(WorkbookCareError) as error:
        run_comparison(
            {
                "action": "comparison_artifacts",
                "model": job["state"]["comparison_result"],
                "job": {"id": job["id"], "expires": job["expires"]},
            },
            timeout=0.001,
        )
    assert error.value.code == "COMPARISON_TIMEOUT"
    assert len(children) == 1 and children[0][0].poll() is not None
    assert not children[0][1].exists()


def test_order_is_rejected_when_input_lifetime_cannot_cover_delivery(tmp_path):
    store, job, settings = comparison_prepared(tmp_path)
    with store.connection() as db:
        db.execute("UPDATE jobs SET expires=?", (time.time() + 60,))
    with pytest.raises(WorkbookCareError) as error:
        order_for(store, store.load("owner", job["id"]), contract_settings(settings))
    assert error.value.code == "INPUT_TOO_CLOSE_TO_EXPIRY"


def test_corrupted_other_required_file_blocks_whole_delivery(tmp_path):
    from app.comparison_service import download_comparison, execute_comparison, grant_comparison

    store, job, settings = comparison_prepared(tmp_path)
    job = grant_comparison(store, job, settings)
    ready = execute_comparison(store, job, {"acknowledge_limitations": True}, settings)
    with store.connection() as db:
        db.execute(
            "UPDATE delivery_artifacts SET data=? WHERE kind=?",
            (b"corrupted-synthetic-html", "COMPARISON_VERIFICATION_HTML"),
        )
    # The requested XLSX is intact, but its mandatory companion is not.
    with pytest.raises(WorkbookCareError):
        download_comparison(store, ready, "COMPARISON_REPORT_XLSX", settings)
    current = store.load("owner", ready["id"])
    assert current["state"]["status"] == "QUARANTINED" and current["state"]["delivery"] is None


def test_actual_worker_audit_hook_denies_socket_and_child_process():
    import sys
    import sysconfig

    root = Path(__file__).resolve().parents[1]
    setup = (
        "import sys;sys.path.insert(0,"
        + repr(str(root))
        + ");sys.path.insert(0,"
        + repr(sysconfig.get_path("purelib"))
        + ");"
    )
    program = (
        setup
        + """
from app.comparison_worker import deny_network_or_process
import socket,subprocess,os
sys.addaudithook(deny_network_or_process)
denied = 0
for action in [lambda:socket.socket(),lambda:subprocess.run([sys.executable,'-c','pass'])]:
    try:
        action()
    except PermissionError:
        denied += 1
assert denied == 2
print('ACTUAL_DENIED_2',os.getpid())
"""
    )
    result = subprocess.run(
        [sys._base_executable, "-I", "-S", "-c", program],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0 and result.stdout.startswith("ACTUAL_DENIED_2 ")


def test_actual_lifespan_sweeper_removes_expired_source_without_new_request(tmp_path, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from test_delivery_inputs import fixture

    from app.delivery_api import get_store
    from app.delivery_inputs import inspect_input
    from app.delivery_operations import lifespan

    settings = Settings(
        app_env="internal_beta", delivery_beta_enabled=True, delivery_data_dir=str(tmp_path)
    )
    monkeypatch.setattr("app.config.get_settings", lambda: settings)
    monkeypatch.setattr("app.delivery_api.get_settings", lambda: settings)
    store = get_store()
    with TestClient(FastAPI(lifespan=lifespan)):
        raw = fixture.workbook_bytes()
        job = store.create(
            "owner", raw, inspect_input("synthetic.xlsx", raw, settings), "background-expiry-07"
        )
        with store.connection() as db:
            db.execute("UPDATE jobs SET expires=? WHERE id=?", (time.time() + 0.2, job["id"]))
        deadline = time.monotonic() + 35
        remaining = 1
        while time.monotonic() < deadline:
            with store.connection() as db:
                remaining = db.execute("SELECT count(*) FROM jobs").fetchone()[0]
            if remaining == 0:
                break
            time.sleep(0.2)
        assert remaining == 0
