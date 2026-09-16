"""Test commerce ledger, independent authorization and recoverable provider operations."""

from __future__ import annotations

import json
import re
import time
import uuid
from dataclasses import asdict
from pathlib import Path

from .delivery_inputs import digest, policy_scope, reject
from .payment_adapter import (
    LocalContractAdapter,
    PaymentObservation,
    PaymentUnknown,
    TossTestAdapter,
)

ORDER_TTL = 24 * 3600
TEST_AMOUNT = 1000
MODES = {"LOCAL_CONTRACT", "TOSS_TEST"}


def install(db):
    db.executescript("""
    CREATE TABLE IF NOT EXISTS payment_orders (
      id TEXT PRIMARY KEY, owner TEXT NOT NULL, job_id TEXT NOT NULL,
      request_key TEXT NOT NULL, expires REAL NOT NULL, state TEXT NOT NULL,
      UNIQUE(owner,request_key));
    CREATE TABLE IF NOT EXISTS payment_outbox (
      order_id TEXT NOT NULL, operation TEXT NOT NULL, state TEXT NOT NULL,
      PRIMARY KEY(order_id,operation));
    CREATE TABLE IF NOT EXISTS payment_events (
      order_id TEXT NOT NULL, event_hash TEXT NOT NULL, created REAL NOT NULL,
      PRIMARY KEY(order_id,event_hash));
    CREATE TABLE IF NOT EXISTS payment_contract_receipts (
      order_id TEXT PRIMARY KEY, state TEXT NOT NULL);
    """)


def require_mode(settings):
    mode = settings.payment_mode
    if (
        mode not in MODES
        or settings.app_env not in {"internal_beta", "hosted_beta"}
        or mode == "LOCAL_CONTRACT"
        and settings.app_env != "internal_beta"
    ):
        reject(
            "PAYMENT_NOT_AVAILABLE", "일반 구매는 준비 중입니다. 실결제를 제공하지 않습니다.", 404
        )
    if mode == "TOSS_TEST" and not settings.toss_test_secret:
        reject("PG_TEST_NOT_CONFIGURED", "공식 테스트 결제 설정을 확인해야 합니다.", 503)
    return mode


def adapter(store, settings):
    mode = require_mode(settings)
    return (
        LocalContractAdapter(store)
        if mode == "LOCAL_CONTRACT"
        else TossTestAdapter(settings.toss_test_secret.get_secret_value())
    )


def fixed_synthetic(job):
    if job["product"] == "APPROVED_REPAIR":
        from .delivery_rehearsal import SYNTHETIC_SOURCE_HASHES

        return job["snapshot"]["source_hash"] in SYNTHETIC_SOURCE_HASHES
    registry = json.loads(
        Path(__file__).with_name("comparison_synthetic_sources.json").read_text(encoding="utf-8")
    )
    return job["snapshot"].get("source_pair_hash") in {
        digest([p["A"], p["B"]]) for p in registry["pairs"]
    }


def supported_scope(job):
    if job["product"] == "APPROVED_REPAIR":
        from .delivery_execution import compatibility_status
        from .delivery_plan import reference_status, validate_plan

        plan = validate_plan(job)
        if reference_status()["status"] != "PASS" or compatibility_status()["status"] != "PASS":
            reject(
                "PRODUCT_NOT_READY",
                "계산·파일 납품 검증이 유효해야 주문을 준비할 수 있습니다.",
                409,
            )
        return {
            "spec_hash": plan["digest"],
            "profile": plan["profile_version"],
            "scope_ids": [p["candidate_id"] for p in plan["patches"]],
            **policy_scope(job["state"]["policy"]),
            "artifact_kinds": plan["required_artifacts"],
            "patch_count": len(plan["patches"]),
        }
    from .comparison_artifacts import REQUIRED
    from .comparison_service import validate_spec

    model = validate_spec(job)
    return {
        "spec_hash": model["spec_hash"],
        "profile": model["profile"],
        "scope_ids": [],
        "artifact_kinds": sorted(REQUIRED),
        "patch_count": 0,
        "limits_required": model["eligibility"] == "ELIGIBLE_WITH_LIMITATIONS",
    }


def get_order(store, owner, order_id, *, db=None):
    if not isinstance(order_id, str) or not re.fullmatch(r"wc_[a-f0-9]{32}", order_id):
        reject("ORDER_NOT_FOUND", "주문이 없거나 이 계정의 주문이 아닙니다.", 404)
    if db is None:
        with store.connection() as connection:
            return get_order(store, owner, order_id, db=connection)
    row = db.execute(
        "SELECT state FROM payment_orders WHERE id=? AND owner=?", (order_id, owner)
    ).fetchone()
    if not row:
        reject("ORDER_NOT_FOUND", "주문이 없거나 이 계정의 주문이 아닙니다.", 404)
    return json.loads(row["state"])


def persist(db, order):
    db.execute(
        "UPDATE payment_orders SET state=?,job_id=? WHERE id=? AND owner=?",
        (json.dumps(order), order["job_id"], order["id"], order["owner"]),
    )


def project_order(store, order):
    with store.connection() as db:
        row = db.execute(
            "SELECT state,expires FROM jobs WHERE id=? AND owner=?",
            (order["job_id"], order["owner"]),
        ).fetchone()
    state = json.loads(row["state"]) if row and row["expires"] > time.time() else None
    delivery = state.get("delivery") if state else None
    broken = False
    if delivery:
        from .delivery_storage_validation import stored_delivery_valid

        broken = not stored_delivery_valid(
            store, order["job_id"], delivery, order["artifact_kinds"]
        )
        if broken:
            delivery = None
    return {
        "order_id": order["id"],
        "job_id": order["job_id"],
        "product_id": order["product_id"],
        "mode": order["mode"],
        "official_pg_verified": order["mode"] == "TOSS_TEST" and order["payment"] == "PAID",
        "amount": str(order["amount"]),
        "currency": "KRW",
        "test_amount_only": True,
        "tax_display": "테스트 총액 · 실제 가격·세금 정책 아님",
        "payment": order["payment"],
        "refund": order["refund"],
        "entitlement": order["entitlement"] if state else "EXPIRED",
        "approval": "NOT_APPLICABLE"
        if order["product_id"] == "TWO_FILE_COMPARISON"
        else (
            "APPROVED"
            if state and state.get("approval") and state["approval"]["expires_at"] > time.time()
            else "NONE"
        ),
        "job_status": "SUCCEEDED"
        if delivery
        else "FAILED"
        if broken
        else state["status"]
        if state
        else "INPUT_EXPIRED",
        "artifact_status": "READY"
        if delivery and order["entitlement"] == "ACTIVE"
        else (
            "EXPIRED"
            if not state
            else "QUARANTINED"
            if broken or state["status"] == "QUARANTINED"
            else "NOT_READY"
        ),
        "validation": "PASS" if delivery else "FAIL" if broken else "NOT_RUN",
        "recovery": order.get("recovery"),
        "quote_hash": order["quote_hash"],
        "profile": order["profile"],
        "patch_count": order["patch_count"],
        "artifact_kinds": order["artifact_kinds"],
        "input_expires_at": row["expires"] if row else None,
        "expires_at": order["expires_at"],
        "scope_change_requires_new_quote": True,
        "delivery": delivery if order["entitlement"] == "ACTIVE" else None,
        "purchase_enabled": False,
        "same_order_retry_no_recharge": True,
    }


def create_order(store, job, body, settings):
    mode = require_mode(settings)
    if not fixed_synthetic(job):
        reject("SYNTHETIC_FIXTURE_REQUIRED", "현재 주문 시험은 지정된 합성 자료만 허용합니다.", 409)
    if body.get("acknowledge_test_only") is not True:
        reject("TEST_ORDER_ACK_REQUIRED", "실제 구매가 아닌 합성 주문 시험임을 확인하세요.")
    if job["state"]["status"] in {"RUNNING", "CANCEL_REQUESTED", "READY", "APPROVED"}:
        reject(
            "ORDER_NOT_AVAILABLE", "진행 중인 실행 또는 납품은 새 주문으로 바꾸지 않습니다.", 409
        )
    scope = supported_scope(job)
    key = body.get("request_key", "")
    if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9-]{16,80}", key):
        reject("INVALID_REQUEST_KEY", "주문 요청 식별자를 확인하세요.")
    if scope.get("limits_required") and body.get("acknowledge_limitations") is not True:
        reject("COMPARISON_LIMITATIONS_REQUIRED", "비교에서 보류할 자료의 제한을 확인하세요.")
    now = time.time()
    input_hash = job["snapshot"].get("source_pair_hash", job["snapshot"]["source_hash"])
    with store.connection() as db:
        db.execute("BEGIN IMMEDIATE")
        old = db.execute(
            "SELECT state FROM payment_orders WHERE owner=? "
            "AND (job_id=? OR request_key=?) ORDER BY expires DESC",
            (job["owner"], job["id"], key),
        ).fetchall()
        for row in old:
            order = json.loads(row["state"])
            if order["request_key"] == key or order["payment"] != "CANCELLED":
                if order["input_hash"] != input_hash or order["spec_hash"] != scope["spec_hash"]:
                    reject(
                        "ORDER_SCOPE_CHANGED",
                        "기존 주문 상태를 먼저 확인하세요. 범위 확대에는 새 견적이 필요합니다.",
                        409,
                    )
                return order
        if job["expires"] - now < 120:
            reject(
                "INPUT_TOO_CLOSE_TO_EXPIRY",
                "원본 보관 시간이 부족합니다. 새 입력으로 다시 확인하세요.",
                409,
            )
        if (
            db.execute(
                "SELECT COUNT(*) FROM payment_orders WHERE owner=?", (job["owner"],)
            ).fetchone()[0]
            >= 20
        ):
            reject("ORDER_LIMIT", "합성 주문 보관 한도에 도달했습니다.", 429)
        order = {
            "id": "wc_" + uuid.uuid4().hex,
            "owner": job["owner"],
            "job_id": job["id"],
            "original_job_id": job["id"],
            "product_id": job["product"],
            "input_hash": input_hash,
            "request_key": key,
            "mode": mode,
            "amount": TEST_AMOUNT,
            "currency": "KRW",
            **scope,
            "created_at": now,
            "quote_expires_at": min(now + 600, job["expires"]),
            "expires_at": now + ORDER_TTL,
            "payment": "NONE",
            "refund": "NONE",
            "entitlement": "NONE",
            "cancel_requested": False,
            "lease_until": 0,
            "recovery": None,
            "payment_key": None,
            "confirm_key": str(uuid.uuid4()),
            "cancel_key": str(uuid.uuid4()),
        }
        order["quote_hash"] = digest(
            {
                k: order[k]
                for k in [
                    "id",
                    "owner",
                    "job_id",
                    "product_id",
                    "input_hash",
                    "spec_hash",
                    "amount",
                    "currency",
                    "quote_expires_at",
                    "artifact_kinds",
                ]
            }
        )
        db.execute(
            "INSERT INTO payment_orders VALUES (?,?,?,?,?,?)",
            (order["id"], job["owner"], job["id"], key, order["expires_at"], json.dumps(order)),
        )
        state = {
            **job["state"],
            "order_id": order["id"],
            "payment": "NONE",
            "approval": None,
            "internal_grant": None,
            "comparison_grant": None,
            "payment_grant": None,
        }
        changed = db.execute(
            "UPDATE jobs SET state=?,revision=revision+1 WHERE id=? AND owner=? "
            "AND revision=? AND expires>?",
            (json.dumps(state), job["id"], job["owner"], job["revision"], now),
        ).rowcount
        if changed != 1:
            reject("STALE_JOB", "최신 작업으로 주문을 다시 확인하세요.", 409)
    return order


def sync_job(db, order):
    row = db.execute(
        "SELECT state,snapshot,expires FROM jobs WHERE id=? AND owner=?",
        (order["job_id"], order["owner"]),
    ).fetchone()
    if not row or row["expires"] <= time.time():
        order["entitlement"] = "EXPIRED"
        if order["payment"] == "PAID" and order["refund"] != "SUCCEEDED":
            order["recovery"] = "SOURCE_REUPLOAD_OR_CANCEL"
        return
    state = json.loads(row["state"])
    if state.get("order_id") != order["id"]:
        return
    state["payment"] = order["payment"]
    if order["entitlement"] == "ACTIVE":
        state["payment_grant"] = {
            **{
                k: order[k]
                for k in [
                    "owner",
                    "job_id",
                    "product_id",
                    "input_hash",
                    "spec_hash",
                    "scope_ids",
                    "profile",
                    "mode",
                ]
            },
            "kind": "SANDBOX_ORDER",
            "order_id": order["id"],
            "expires_at": min(row["expires"], order["expires_at"]),
            "policy_base_hash": order.get("policy_base_hash"),
            "policy_item_base_hashes": order.get("policy_item_base_hashes"),
            "policy_target_bindings": order.get("policy_target_bindings"),
        }
        if not state.get("approval") and state["status"] not in {"RUNNING", "READY", "QUARANTINED"}:
            state["status"] = (
                "WAITING_APPROVAL"
                if order["product_id"] == "APPROVED_REPAIR"
                else "COMPARISON_PREFLIGHT"
            )
    else:
        state["payment_grant"] = None
        state["approval"] = None
        if order["cancel_requested"] or order["payment"] == "CANCELLED":
            state["publication_fence"] = str(uuid.uuid4())
            state["delivery"] = None
            state["status"] = (
                "CANCEL_REQUESTED"
                if state["status"] in {"RUNNING", "CANCEL_REQUESTED"}
                else "CANCELLED"
            )
            db.execute("DELETE FROM delivery_artifacts WHERE job_id=?", (order["job_id"],))
    db.execute(
        "UPDATE jobs SET state=?,revision=revision+1 WHERE id=? AND owner=?",
        (json.dumps(state), order["job_id"], order["owner"]),
    )


def settle(store, order, observation):
    with store.connection() as db:
        db.execute("BEGIN IMMEDIATE")
        current = get_order(store, order["owner"], order["id"], db=db)
        current["lease_until"] = 0
        if current["payment"] == "CANCELLED" and current["refund"] == "SUCCEEDED":
            # A late or malformed provider response cannot undo a settled full cancellation.
            pass
        elif observation is None:
            if current["payment"] not in {"PAID", "CANCELLED"}:
                current["payment"] = "UNKNOWN"
            current["recovery"] = "RECONCILE_SAME_ORDER"
        elif (
            observation.order_id != current["id"]
            or observation.amount != current["amount"]
            or observation.currency != "KRW"
            or current.get("payment_key") not in {None, observation.payment_key}
        ):
            current.update(payment="UNKNOWN", entitlement="REVOKED", recovery="PROVIDER_MISMATCH")
        elif observation.status == "CANCELED" and observation.balance == 0:
            current.update(
                payment="CANCELLED",
                refund="SUCCEEDED",
                entitlement="REVOKED",
                recovery=None,
                payment_key=observation.payment_key,
                cancel_requested=True,
            )
        elif observation.status == "DONE" and observation.balance == current["amount"]:
            current.update(
                payment="PAID",
                payment_key=observation.payment_key,
                recovery=None,
                entitlement="REVOKED" if current["cancel_requested"] else "ACTIVE",
            )
            if current["cancel_requested"]:
                current.update(refund="PENDING", recovery="CANCEL_PENDING")
        elif observation.status in {"PARTIAL_CANCELED", "CANCELED"}:
            current.update(entitlement="REVOKED", refund="FAILED", recovery="PARTIAL_CANCEL_REVIEW")
        else:
            current.update(payment="PENDING", entitlement="NONE", recovery="RECONCILE_SAME_ORDER")
        sync_job(db, current)
        persist(db, current)
        if not current["recovery"]:
            db.execute("UPDATE payment_outbox SET state='DONE' WHERE order_id=?", (current["id"],))
        db.execute(
            "INSERT OR REPLACE INTO payment_outbox VALUES (?,?,?)",
            (current["id"], "RECONCILE", "PENDING" if current["recovery"] else "DONE"),
        )
    return current


def perform(store, owner, order_id, action, settings, *, payment_key=None):
    mode = require_mode(settings)
    with store.connection() as db:
        db.execute("BEGIN IMMEDIATE")
        order = get_order(store, owner, order_id, db=db)
        if order["mode"] != mode:
            reject("PAYMENT_MODE_CHANGED", "주문과 결제 시험 환경이 다릅니다.", 409)
        if order["expires_at"] <= time.time():
            reject("ORDER_EXPIRED", "주문 시험 보관 기간이 끝났습니다.", 410)
        if order["lease_until"] > time.time():
            return order
        if action == "confirm":
            if order["payment"] in {"PAID", "CANCELLED"}:
                return order
            if order["cancel_requested"] or order["quote_expires_at"] <= time.time():
                reject(
                    "QUOTE_EXPIRED",
                    "견적이 만료되거나 취소되었습니다. 기존 주문부터 확인하세요.",
                    409,
                )
            if order["payment"] == "UNKNOWN":
                action = "query"
            elif payment_key is not None:
                if not isinstance(payment_key, str) or not re.fullmatch(
                    r"[A-Za-z0-9_-]{6,200}", payment_key
                ):
                    reject("INVALID_PAYMENT_REFERENCE", "결제 참조 형식이 다릅니다.")
                if order.get("payment_key") not in {None, payment_key}:
                    reject("PAYMENT_REFERENCE_CHANGED", "같은 주문의 결제 참조가 다릅니다.", 409)
                order["payment_key"] = payment_key
        order["lease_until"] = time.time() + 20
        if order["payment"] == "NONE":
            order["payment"] = "PENDING"
        db.execute(
            "INSERT OR REPLACE INTO payment_outbox VALUES (?,?,?)",
            (order["id"], action.upper(), "PENDING"),
        )
        persist(db, order)
    provider = adapter(store, settings)
    try:
        if action == "confirm":
            observation = provider.confirm(order, payment_key)
        else:
            observation = provider.query(order)
        if order["cancel_requested"] and observation.status == "DONE":
            order["payment_key"] = observation.payment_key
            observation = provider.cancel(order)
    except PaymentUnknown:
        observation = None
    finally:
        provider.close()
    return settle(store, order, observation)


def request_cancel(store, owner, order_id, settings):
    require_mode(settings)
    with store.connection() as db:
        db.execute("BEGIN IMMEDIATE")
        order = get_order(store, owner, order_id, db=db)
        if order["payment"] == "CANCELLED":
            return order
        order.update(
            cancel_requested=True,
            entitlement="REVOKED",
            refund="PENDING",
            recovery="CANCEL_PENDING",
        )
        if order["payment"] == "NONE":
            order.update(payment="CANCELLED", refund="NONE", recovery=None)
        sync_job(db, order)
        persist(db, order)
        db.execute(
            "INSERT OR REPLACE INTO payment_outbox VALUES (?,?,?)",
            (order["id"], "CANCEL", "PENDING"),
        )
    from .delivery_execution import CONTROLS, CONTROLS_LOCK

    with CONTROLS_LOCK:
        control = CONTROLS.get((str(store.path), order["job_id"]))
    if control:
        control.cancel()
    return (
        order
        if order["payment"] == "CANCELLED"
        else perform(store, owner, order_id, "query", settings)
    )


def event_hint(store, owner, order_id, event_id, settings):
    if not isinstance(event_id, str) or not 1 <= len(event_id) <= 200:
        reject("INVALID_EVENT_REFERENCE", "이벤트 참조를 확인하세요.")
    order = get_order(store, owner, order_id)
    with store.connection() as db:
        db.execute(
            "INSERT OR IGNORE INTO payment_events VALUES (?,?,?)",
            (order_id, digest(event_id), time.time()),
        )
        db.execute(
            "DELETE FROM payment_events WHERE order_id=? AND event_hash NOT IN "
            "(SELECT event_hash FROM payment_events WHERE order_id=? "
            "ORDER BY created DESC LIMIT 128)",
            (order_id, order_id),
        )
    # Payload status/amount are never evidence. Always query the fixed provider order.
    return perform(store, owner, order["id"], "query", settings)


def list_orders(store, owner):
    with store.connection() as db:
        rows = db.execute(
            "SELECT state FROM payment_orders WHERE owner=? AND expires>? "
            "ORDER BY expires DESC LIMIT 20",
            (owner, time.time()),
        ).fetchall()
    return [project_order(store, json.loads(row["state"])) for row in rows]


def seed_contract(store, order, settings, status="DONE"):
    if require_mode(settings) != "LOCAL_CONTRACT" or settings.app_env != "internal_beta":
        reject("LOCAL_CONTRACT_ONLY", "내부 계약 모형 기록은 로컬 시험 전용입니다.", 403)
    if order["mode"] != "LOCAL_CONTRACT" or status not in {"DONE", "CANCELED"}:
        reject("LOCAL_CONTRACT_ONLY", "공식 결제 증거를 만들 수 없습니다.", 403)
    receipt = PaymentObservation(
        order["id"],
        "synthetic_" + uuid.uuid4().hex,
        order["amount"],
        "KRW",
        status,
        order["amount"] if status == "DONE" else 0,
    )
    with store.connection() as db:
        old = db.execute(
            "SELECT state FROM payment_contract_receipts WHERE order_id=?", (order["id"],)
        ).fetchone()
        if old:
            value = json.loads(old["state"])
            value.update(status=status, balance=receipt.balance)
        else:
            value = asdict(receipt)
        db.execute(
            "INSERT OR REPLACE INTO payment_contract_receipts VALUES (?,?)",
            (order["id"], json.dumps(value)),
        )
    return perform(store, order["owner"], order["id"], "query", settings)
