"""Bounded synthetic-beta operation, retention and request privacy controls."""

from __future__ import annotations

import json
import threading
import time
import uuid
from contextlib import asynccontextmanager

from .delivery_inputs import reject

REQUEST_MAX_BYTES = 2 * 1024**2 * 8 // 3 + 64 * 1024
MAX_ATTEMPTS = 3


async def bounded_body(request):
    size = 0
    chunks = []
    async for chunk in request.stream():
        size += len(chunk)
        if size > REQUEST_MAX_BYTES:
            reject("LIMIT_EXCEEDED", "사전 검사 요청 한도를 초과했습니다.", 413)
        chunks.append(chunk)
    return b"".join(chunks)


def install(db):
    db.execute(
        "CREATE TABLE IF NOT EXISTS delivery_usage (job_id TEXT NOT NULL "
        "REFERENCES jobs(id) ON DELETE CASCADE, operation TEXT NOT NULL, "
        "count INTEGER NOT NULL, PRIMARY KEY(job_id,operation))"
    )


def claim_attempt(store, job, operation):
    with store.connection() as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute(
            "SELECT count FROM delivery_usage WHERE job_id=? AND operation=?",
            (job["id"], operation),
        ).fetchone()
        count = row["count"] if row else 0
        if count >= MAX_ATTEMPTS:
            reject(
                "DELIVERY_ATTEMPT_LIMIT",
                "실행 한도에 도달했습니다. 기존 주문 취소 또는 새 범위를 확인하세요.",
                429,
            )
        db.execute(
            "INSERT OR REPLACE INTO delivery_usage VALUES (?,?,?)",
            (job["id"], operation, count + 1),
        )


def maintain(store, now=None):
    now = time.time() if now is None else now
    cancelled = []
    with store.connection() as db:
        db.execute("BEGIN IMMEDIATE")
        for row in db.execute("SELECT id,state,expires FROM jobs").fetchall():
            state = json.loads(row["state"])
            if row["expires"] <= now:
                cancelled.append(row["id"])
                continue
            if state["status"] in {"RUNNING", "CANCEL_REQUESTED"}:
                if state.get("lease_expires_at", 0) > now:
                    continue
                cancelled.append(row["id"])
                state.update(
                    status="QUARANTINED",
                    approval=None,
                    delivery=None,
                    publication_fence=str(uuid.uuid4()),
                    failure_code="EXECUTION_LEASE_EXPIRED",
                )
                db.execute("DELETE FROM delivery_artifacts WHERE job_id=?", (row["id"],))
            elif (
                state["status"] != "READY"
                and (state.get("plan") or {}).get("expires_at", now + 1) <= now
            ):
                state.update(plan=None, approval=None)
                if state["status"] not in {"CANCELLED", "QUARANTINED"}:
                    state["status"] = "PLAN_EXPIRED"
            elif (
                state.get("approval")
                and state["approval"].get("expires_at", 0) <= now
                and state["status"] != "READY"
            ):
                state.update(approval=None, status="WAITING_APPROVAL")
            else:
                continue
            db.execute(
                "UPDATE jobs SET state=?,revision=revision+1 WHERE id=?",
                (json.dumps(state), row["id"]),
            )
        count = db.execute("DELETE FROM jobs WHERE expires<=?", (now,)).rowcount
        # This is a 24-hour synthetic test ledger, not a legal accounting retention policy.
        for table in ["payment_outbox", "payment_events", "payment_contract_receipts"]:
            db.execute(
                f"DELETE FROM {table} WHERE order_id IN "
                "(SELECT id FROM payment_orders WHERE expires<=?)",
                (now,),
            )
        db.execute("DELETE FROM payment_orders WHERE expires<=?", (now,))
        db.execute("DELETE FROM request_limits WHERE window<?", (int(now) // 60 - 2,))
    from .delivery_execution import CONTROLS, CONTROLS_LOCK

    with CONTROLS_LOCK:
        controls = [CONTROLS.get((str(store.path), job_id)) for job_id in cancelled]
    for control in controls:
        if control:
            control.cancel()
    return count


@asynccontextmanager
async def lifespan(_app):
    from .config import get_settings
    from .delivery_api import get_store

    stop = threading.Event()

    def sweep():
        while not stop.wait(30):
            try:
                maintain(get_store())
            except Exception:
                from .observability import log_safe_event

                log_safe_event(
                    "request_failed",
                    execution_status="failed",
                    safe_error_code="DELIVERY_CLEANUP_FAILED",
                )

    worker = None
    if get_settings().delivery_beta_enabled:
        maintain(get_store())
        worker = threading.Thread(target=sweep, name="delivery-ttl", daemon=True)
        worker.start()
    try:
        yield
    finally:
        stop.set()
        if worker:
            worker.join(timeout=6)


class DeliveryPrivacyMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http" or scope.get("path") != "/v1/delivery":
            return await self.app(scope, receive, send)

        async def private_send(message):
            if message["type"] == "http.response.start":
                message = dict(message)
                headers = [
                    (k, v)
                    for k, v in message.get("headers", [])
                    if k.lower() not in {b"cache-control", b"pragma"}
                ]
                headers += [
                    (b"cache-control", b"no-store, private"),
                    (b"pragma", b"no-cache"),
                    (b"referrer-policy", b"no-referrer"),
                ]
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, private_send)
