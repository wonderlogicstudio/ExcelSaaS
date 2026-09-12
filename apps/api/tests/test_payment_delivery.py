from __future__ import annotations

import copy
import json
import time
from dataclasses import asdict, replace

import httpx
import pytest
from test_comparison_service import prepared as comparison_prepared
from test_delivery_execution import authorized, prepared
from test_delivery_execution import blueprint as blueprint

from app.comparison_service import download_comparison, execute_comparison
from app.config import Settings
from app.delivery_execution import download, execute
from app.delivery_plan import build_plan
from app.delivery_rehearsal import entitled
from app.errors import WorkbookCareError
from app.payment_adapter import PaymentUnknown, TossTestAdapter
from app.payment_plan_actions import reselect, restore_order, validate_paid_scope
from app.payment_service import (
    create_order,
    event_hint,
    get_order,
    list_orders,
    perform,
    project_order,
    request_cancel,
    seed_contract,
    settle,
)


def order_for(store, job, settings, key="synthetic-order-request-01"):
    return create_order(
        store,
        job,
        {"request_key": key, "acknowledge_test_only": True, "acknowledge_limitations": True},
        settings,
    )


def contract_settings(settings):
    return settings.model_copy(update={"payment_mode": "LOCAL_CONTRACT"})


def test_paid_is_not_approval_then_actual_repair_and_no_recharge(tmp_path, blueprint):
    store, job, settings = prepared(tmp_path, blueprint)
    settings = contract_settings(settings)
    order = order_for(store, job, settings)
    assert order_for(store, job, settings)["id"] == order["id"]
    assert not entitled(store.load("owner", job["id"]), settings.app_env)
    order = seed_contract(store, order, settings)
    paid = store.load("owner", job["id"])
    assert paid["state"]["payment"] == "PAID" and paid["state"]["status"] == "WAITING_APPROVAL"
    assert not paid["state"]["approval"]
    assert project_order(store, order)["official_pg_verified"] is False
    with pytest.raises(WorkbookCareError):
        execute(store, paid, settings)
    with pytest.raises(WorkbookCareError):
        download(store, paid, "REPAIRED_XLSX", settings)
    ready = execute(store, authorized(store, paid, settings), settings)
    assert ready["state"]["status"] == "READY"
    first = download(store, ready, "REPAIRED_XLSX", settings)
    assert first == download(store, ready, "REPAIRED_XLSX", settings)
    assert execute(store, ready, settings)["state"]["delivery"] == ready["state"]["delivery"]
    assert len(list_orders(store, "owner")) == 1
    summary = list_orders(store, "owner")[0]
    assert summary["payment"] == "PAID" and summary["artifact_status"] == "READY"
    assert "payment_key" not in summary and "input_hash" not in summary and "owner" not in summary
    assert list_orders(store, "other") == []
    order = request_cancel(store, "owner", order["id"], settings)
    assert order["refund"] == "SUCCEEDED" and order["entitlement"] == "REVOKED"
    with pytest.raises(WorkbookCareError):
        download(store, store.load("owner", job["id"]), "REPAIRED_XLSX", settings)
    with store.connection() as db:
        assert db.execute("SELECT COUNT(*) FROM delivery_artifacts").fetchone()[0] == 0


def test_paid_comparison_cannot_repair_and_real_two_artifacts(tmp_path):
    store, job, settings = comparison_prepared(tmp_path)
    settings = contract_settings(settings)
    order = seed_contract(store, order_for(store, job, settings), settings)
    paid = store.load("owner", job["id"])
    assert not entitled(paid, settings.app_env)
    assert project_order(store, order)["approval"] == "NOT_APPLICABLE"
    with pytest.raises(WorkbookCareError):
        execute(store, paid, settings)
    ready = execute_comparison(store, paid, {"acknowledge_limitations": True}, settings)
    for kind in ["COMPARISON_REPORT_XLSX", "COMPARISON_VERIFICATION_HTML"]:
        assert download_comparison(store, ready, kind, settings)["file_base64"]


def test_unknown_recovers_same_order_and_ignores_duplicate_or_reversed_event(tmp_path):
    store, job, settings = comparison_prepared(tmp_path)
    settings = contract_settings(settings)
    order = order_for(store, job, settings)
    unknown = perform(store, "owner", order["id"], "confirm", settings)
    assert unknown["payment"] == "UNKNOWN" and unknown["entitlement"] == "NONE"
    assert order_for(store, job, settings, key="another-request-0000001")["id"] == order["id"]
    paid = seed_contract(store, unknown, settings)
    for _ in range(2):
        assert event_hint(store, "owner", order["id"], "same-event", settings)["payment"] == "PAID"
    with store.connection() as db:
        receipt = json.loads(
            db.execute("SELECT state FROM payment_contract_receipts").fetchone()[0]
        )
        assert db.execute("SELECT COUNT(*) FROM payment_events").fetchone()[0] == 1
    cancelled = request_cancel(store, "owner", order["id"], settings)
    from app.payment_adapter import PaymentObservation

    stale = settle(store, paid, PaymentObservation(**receipt))
    assert stale["payment"] == cancelled["payment"] == "CANCELLED"
    assert stale["entitlement"] != "ACTIVE"
    with pytest.raises(WorkbookCareError):
        get_order(store, "other-owner", order["id"])


def test_reselect_recalculates_subset_revokes_approval_and_blocks_expansion(tmp_path, blueprint):
    store, job, settings = prepared(tmp_path, blueprint)
    settings = contract_settings(settings)
    policy = {
        "profile": "RP01_NUMERIC_TEXT_FIELD_V1",
        "sheet": "검증",
        "targets": ["B2", "B3"],
        "role": "AMOUNT",
        "confirmed": True,
    }
    plan = build_plan(job, policy)
    job = store.update(job, job["revision"], {**job["state"], "plan": plan, "policy": policy})
    order = seed_contract(store, order_for(store, job, settings), settings)
    paid = store.load("owner", job["id"])
    paid = authorized(store, paid, settings)
    body = {
        "revision": paid["revision"],
        "plan_digest": plan["digest"],
        "candidate_ids": [plan["patches"][0]["candidate_id"]],
    }
    reduced = reselect(store, paid, body, settings)
    assert reduced["state"]["approval"] is None and reduced["state"]["status"] == "WAITING_APPROVAL"
    assert len(reduced["state"]["plan"]["patches"]) == 1
    assert reduced["state"]["plan"]["digest"] != plan["digest"]
    assert (
        next(i for i in reduced["state"]["plan"]["impact"] if i["cell"] == "H2")["after"]["value"]
        == 12000
    )
    with pytest.raises(WorkbookCareError):
        execute(store, reduced, settings)
    with pytest.raises(WorkbookCareError):
        reselect(store, reduced, {**body, "candidate_ids": []}, settings)
    widened = copy.deepcopy(reduced["state"]["plan"])
    widened["patches"][0]["candidate_id"] = "not-purchased"
    with pytest.raises(WorkbookCareError):
        validate_paid_scope(store, reduced, widened)
    assert get_order(store, "owner", order["id"])["amount"] == 1000


def test_expired_input_restore_same_hash_needs_new_approval(tmp_path, blueprint):
    store, job, settings = prepared(tmp_path, blueprint)
    settings = contract_settings(settings)
    order = seed_contract(store, order_for(store, job, settings), settings)
    source = job["source"]
    snapshot = job["snapshot"]
    policy = job["state"]["policy"]
    with store.connection() as db:
        db.execute("UPDATE jobs SET expires=? WHERE id=?", (time.time() - 1, job["id"]))
    new = store.create("owner", source, snapshot, "new-identical-source-001")
    new = store.update(
        new, new["revision"], {**new["state"], "policy": policy, "plan": build_plan(new, policy)}
    )
    restored = restore_order(store, "owner", order["id"], new)
    actual = store.load("owner", new["id"])
    assert restored["id"] == order["id"] and actual["state"]["status"] == "WAITING_APPROVAL"
    assert actual["state"]["approval"] is None
    assert actual["state"]["payment"] == "PAID" and entitled(actual, settings.app_env)
    wrong = copy.deepcopy(new)
    wrong["snapshot"]["source_hash"] = "0" * 64
    with pytest.raises(WorkbookCareError):
        restore_order(store, "owner", order["id"], wrong)


@pytest.mark.parametrize("mutation", ["amount", "currency", "order", "balance"])
def test_provider_mismatch_never_grants_right(tmp_path, mutation):
    store, job, settings = comparison_prepared(tmp_path)
    settings = contract_settings(settings)
    order = order_for(store, job, settings)
    from app.payment_adapter import PaymentObservation

    proof = PaymentObservation(order["id"], "synthetic-reference", 1000, "KRW", "DONE", 1000)
    proof = replace(
        proof,
        **{
            "amount": {"amount": 1001},
            "currency": {"currency": "USD"},
            "order": {"order_id": "wrong"},
            "balance": {"balance": 500},
        }[mutation],
    )
    result = settle(store, order, proof)
    assert result["entitlement"] != "ACTIVE"


def test_off_and_live_keys_fail_closed(tmp_path):
    store, job, settings = comparison_prepared(tmp_path)
    with pytest.raises(WorkbookCareError):
        order_for(store, job, settings)
    with pytest.raises(ValueError):
        Settings(toss_test_secret="live_sk_synthetic_not_real")
    with pytest.raises(WorkbookCareError):
        TossTestAdapter("live_sk_synthetic_not_real")


def test_toss_transport_contract_paths_keys_and_response_loss():
    calls = []
    order = {
        "id": "wc_" + "a" * 32,
        "amount": 1000,
        "confirm_key": "confirm-fixed-idempotency",
        "cancel_key": "cancel-fixed-idempotency",
        "payment_key": "synthetic-payment-reference",
    }

    def handler(request):
        calls.append(request)
        if len(calls) == 4:
            raise httpx.ReadTimeout("synthetic transport loss")
        cancelled = request.url.path.endswith("/cancel")
        return httpx.Response(
            200,
            json={
                "orderId": order["id"],
                "paymentKey": order["payment_key"],
                "currency": "KRW",
                "totalAmount": 1000,
                "balanceAmount": 0 if cancelled else 1000,
                "status": "CANCELED" if cancelled else "DONE",
                "customerEmail": "ignored-synthetic@example.invalid",
            },
        )

    provider = TossTestAdapter(
        "test_sk_synthetic_contract_only", transport=httpx.MockTransport(handler)
    )
    try:
        observation = provider.confirm(order, order["payment_key"])
        assert observation.status == "DONE" and "customerEmail" not in asdict(observation)
        assert provider.query(order).amount == 1000
        assert provider.cancel(order).status == "CANCELED"
        assert [r.url.path for r in calls] == [
            "/v1/payments/confirm",
            "/v1/payments/orders/" + order["id"],
            "/v1/payments/" + order["payment_key"] + "/cancel",
        ]
        assert calls[0].headers["Idempotency-Key"] == order["confirm_key"]
        assert calls[2].headers["Idempotency-Key"] == order["cancel_key"]
        with pytest.raises(PaymentUnknown):
            provider.query(order)
    finally:
        provider.close()


def test_missing_paid_artifact_has_failed_order_axis_and_same_right_retry(tmp_path, blueprint):
    from app.payment_plan_actions import retry_delivery

    store, job, settings = prepared(tmp_path, blueprint)
    settings = contract_settings(settings)
    order = seed_contract(store, order_for(store, job, settings), settings)
    ready = execute(store, authorized(store, store.load("owner", job["id"]), settings), settings)
    with store.connection() as db:
        db.execute("DELETE FROM delivery_artifacts WHERE kind='CHANGES_XLSX'")
    shown = project_order(store, order)
    assert shown["payment"] == "PAID"
    assert shown["artifact_status"] == "QUARANTINED" and shown["validation"] == "FAIL"
    assert shown["job_status"] == "FAILED"
    retried = retry_delivery(store, ready, settings)
    assert retried["state"]["status"] == "READY"
    assert retried["state"]["delivery"]["delivery_id"] != ready["state"]["delivery"]["delivery_id"]
    assert len(list_orders(store, "owner")) == 1
    assert project_order(store, order)["artifact_status"] == "READY"


def test_cancel_paid_during_publication_never_exposes_late_files(tmp_path, monkeypatch):
    import threading
    from concurrent.futures import ThreadPoolExecutor

    from app.comparison_artifacts import make_comparison_artifacts

    store, job, settings = comparison_prepared(tmp_path)
    settings = contract_settings(settings)
    order = seed_contract(store, order_for(store, job, settings), settings)
    paid = store.load("owner", job["id"])
    waiting = threading.Event()
    release = threading.Event()

    def pause(*args):
        package = make_comparison_artifacts(*args)
        waiting.set()
        assert release.wait(20)
        return package

    monkeypatch.setattr("app.comparison_service.make_comparison_artifacts", pause)
    with ThreadPoolExecutor() as pool:
        future = pool.submit(
            execute_comparison, store, paid, {"acknowledge_limitations": True}, settings
        )
        assert waiting.wait(20)
        cancelled = request_cancel(store, "owner", order["id"], settings)
        assert cancelled["entitlement"] == "REVOKED" and cancelled["refund"] == "SUCCEEDED"
        release.set()
        with pytest.raises(WorkbookCareError):
            future.result(20)
    current = store.load("owner", job["id"])
    assert current["state"]["status"] == "CANCELLED"
    with store.connection() as db:
        assert db.execute("SELECT COUNT(*) FROM delivery_artifacts").fetchone()[0] == 0


def test_cancelled_order_is_terminal_even_after_malformed_late_receipt(tmp_path):
    from app.payment_adapter import PaymentObservation

    store, job, settings = comparison_prepared(tmp_path)
    settings = contract_settings(settings)
    order = order_for(store, job, settings, key="terminal-order-request")
    paid = seed_contract(store, order, settings)
    cancelled = request_cancel(store, job["owner"], paid["id"], settings)
    malformed = PaymentObservation(
        cancelled["id"], cancelled["payment_key"], 999, "USD", "DONE", 999
    )
    for observation in [
        malformed,
        None,
        replace(malformed, amount=1000, currency="KRW", balance=1000),
    ]:
        current = settle(store, cancelled, observation)
        assert current["payment"] == "CANCELLED"
        assert current["refund"] == "SUCCEEDED"
        assert current["entitlement"] == "REVOKED"


def test_retry_cannot_start_a_fresh_paid_comparison(tmp_path):
    from app.payment_plan_actions import retry_delivery

    store, job, settings = comparison_prepared(tmp_path)
    settings = contract_settings(settings)
    order = order_for(store, job, settings, key="no-first-retry-request")
    seed_contract(store, order, settings)
    with pytest.raises(WorkbookCareError) as error:
        retry_delivery(store, store.load(job["owner"], job["id"]), settings)
    assert error.value.code == "DELIVERY_RETRY_UNAVAILABLE"
