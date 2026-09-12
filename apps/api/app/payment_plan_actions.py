"""New plans revoke approval; paid scope is an upper bound, never an instruction to patch."""

from __future__ import annotations

import copy

from .delivery_inputs import reject
from .delivery_plan import build_plan, plan_digest
from .delivery_rights import payment_grant
from .payment_service import get_order, persist, supported_scope, sync_job


def validate_paid_scope(store, job, plan):
    if not job["state"].get("order_id"):
        return
    order = get_order(store, job["owner"], job["state"]["order_id"])
    candidate = {**job, "state": {**job["state"], "plan": plan}}
    if order["payment"] == "PAID" and order["entitlement"] == "ACTIVE":
        grant = candidate["state"].get("payment_grant") or {}
        # Even while selecting criteria, the order's original scope remains fixed.
        candidate["state"]["payment_grant"] = {
            **grant,
            "scope_ids": order["scope_ids"],
            "policy_base_hash": order.get("policy_base_hash"),
            "profile": order["profile"],
        }
        if not payment_grant(
            candidate, "internal_beta" if order["mode"] == "LOCAL_CONTRACT" else "hosted_beta"
        ):
            reject(
                "NEW_QUOTE_REQUIRED",
                "구매 범위보다 넓거나 다른 변경입니다. 새 견적이 필요합니다.",
                409,
            )
    elif order["payment"] not in {"NONE", "CANCELLED"}:
        reject("ORDER_RECONCILIATION_REQUIRED", "기존 주문의 결제 상태를 먼저 확인하세요.", 409)


def reselect(store, job, body, settings):
    if job["product"] != "APPROVED_REPAIR" or job["state"]["status"] in {
        "RUNNING",
        "READY",
        "CANCEL_REQUESTED",
    }:
        reject("RESELECTION_UNAVAILABLE", "현재 작업에서는 대상을 다시 선택할 수 없습니다.", 409)
    old = job["state"].get("plan") or {}
    ids = body.get("candidate_ids")
    if (
        not isinstance(ids, list)
        or not ids
        or any(not isinstance(v, str) for v in ids)
        or len(ids) != len(set(ids))
        or not set(ids) <= {p["candidate_id"] for p in old.get("patches", [])}
        or body.get("plan_digest") != old.get("digest")
        or plan_digest(old) != old.get("digest")
    ):
        reject(
            "EXACT_RESELECTION_REQUIRED",
            "현재 계획에서 한 개 이상을 선택하세요. 전부 거부는 취소를 이용하세요.",
            409,
        )
    policy = copy.deepcopy(job["state"]["policy"])
    policy["targets"] = [p["cell"] for p in old["patches"] if p["candidate_id"] in ids]
    candidate = {**job, "state": {**job["state"], "policy": policy}}
    from .delivery_operations import claim_attempt

    claim_attempt(store, job, "PLAN")
    plan = build_plan(candidate, policy)
    validate_paid_scope(store, candidate, plan)
    return store.update(
        job,
        body.get("revision"),
        {
            **candidate["state"],
            "plan": plan,
            "approval": None,
            "delivery": None,
            "status": "WAITING_APPROVAL"
            if job["state"].get("payment") == "PAID"
            else "PREVIEW_VALIDATED",
        },
    )


def restore_order(store, owner, order_id, new_job):
    order = get_order(store, owner, order_id)
    if order["payment"] != "PAID" or order["cancel_requested"] or order["refund"] != "NONE":
        reject("ORDER_RESTORE_UNAVAILABLE", "원본 재업로드로 복구할 수 없는 주문입니다.", 409)
    import time

    if order["expires_at"] <= time.time():
        reject("ORDER_EXPIRED", "주문 보관 기간이 끝났습니다.", 410)
    scope = supported_scope(new_job)
    input_hash = new_job["snapshot"].get("source_pair_hash", new_job["snapshot"]["source_hash"])
    if (
        new_job["owner"] != owner
        or new_job["product"] != order["product_id"]
        or input_hash != order["input_hash"]
        or scope["profile"] != order["profile"]
        or not set(scope["scope_ids"]) <= set(order["scope_ids"])
        or scope.get("policy_base_hash") != order.get("policy_base_hash")
        or new_job["product"] == "TWO_FILE_COMPARISON"
        and scope["spec_hash"] != order["spec_hash"]
    ):
        reject(
            "ORDER_RESTORE_SOURCE_MISMATCH",
            "원래 자료와 구매 범위가 일치해야 복구할 수 있습니다.",
            409,
        )
    with store.connection() as db:
        db.execute("BEGIN IMMEDIATE")
        current = get_order(store, owner, order_id, db=db)
        if current != order:
            reject("STALE_ORDER", "주문 상태가 바뀌었습니다.", 409)
        old = db.execute("SELECT expires FROM jobs WHERE id=?", (order["job_id"],)).fetchone()
        if old and old["expires"] > time.time():
            reject("ORIGINAL_JOB_STILL_ACTIVE", "기존 작업을 계속 사용할 수 있습니다.", 409)
        row = db.execute(
            "SELECT state,revision FROM jobs WHERE id=? AND owner=?", (new_job["id"], owner)
        ).fetchone()
        if not row or row["revision"] != new_job["revision"] or json_state(row).get("order_id"):
            reject("STALE_JOB", "다른 주문과 연결되지 않은 최신 작업이 필요합니다.", 409)
        state = {
            **new_job["state"],
            "order_id": order_id,
            "approval": None,
            "delivery": None,
            "internal_grant": None,
            "comparison_grant": None,
        }
        import json

        db.execute(
            "UPDATE jobs SET state=?,revision=revision+1 WHERE id=?",
            (json.dumps(state), new_job["id"]),
        )
        order.update(job_id=new_job["id"], entitlement="ACTIVE", recovery=None)
        sync_job(db, order)
        persist(db, order)
    return order


def json_state(row):
    import json

    return json.loads(row["state"])


def retry_delivery(store, job, settings):
    if job["state"]["status"] not in {"READY", "QUARANTINED", "FAILED"}:
        reject(
            "DELIVERY_RETRY_UNAVAILABLE",
            "실패한 납품만 다시 시도할 수 있습니다. 먼저 변경 승인 또는 비교 범위를 확인하세요.",
            409,
        )
    if job["state"]["status"] == "READY":
        delivery = job["state"].get("delivery") or {}
        with store.connection() as db:
            kinds = {
                r["kind"]
                for r in db.execute(
                    "SELECT kind FROM delivery_artifacts WHERE job_id=? AND delivery_id=?",
                    (job["id"], delivery.get("delivery_id")),
                )
            }
        required = (
            {"REPAIRED_XLSX", "CHANGES_XLSX", "VERIFICATION_HTML"}
            if job["product"] == "APPROVED_REPAIR"
            else {"COMPARISON_REPORT_XLSX", "COMPARISON_VERIFICATION_HTML"}
        )
        if kinds != required:
            job = store.update(
                job,
                job["revision"],
                {
                    **job["state"],
                    "status": "QUARANTINED",
                    "delivery": None,
                    "failure_code": "MISSING_REQUIRED_ARTIFACT",
                },
            )
    if job["product"] == "APPROVED_REPAIR":
        from .delivery_execution import execute

        return execute(store, job, settings)
    from .comparison_service import execute_comparison

    # This retries the already confirmed comparison scope; no new purchase or repair approval.
    return execute_comparison(store, job, {"acknowledge_limitations": True}, settings)
