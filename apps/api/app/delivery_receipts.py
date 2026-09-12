"""Server-authenticated approval receipt. It never substitutes for payment or fresh approval."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import uuid

from .delivery_inputs import digest, reject


def install(db):
    db.execute(
        "CREATE TABLE IF NOT EXISTS approval_receipt_key "
        "(singleton INTEGER PRIMARY KEY CHECK(singleton=1), "
        "key_id TEXT NOT NULL, secret BLOB NOT NULL)"
    )
    db.execute(
        "INSERT OR IGNORE INTO approval_receipt_key VALUES (1,?,?)",
        (uuid.uuid4().hex, secrets.token_bytes(32)),
    )


def payload(approval):
    return {
        "kind": "EXACT_APPROVAL_RECEIPT_V1",
        "owner_binding": digest(approval["owner"]),
        **{
            k: approval[k]
            for k in [
                "job_id",
                "product_id",
                "sku",
                "source_hash",
                "plan_digest",
                "candidate_ids",
                "entitlement_digest",
                "created_at",
                "expires_at",
            ]
        },
    }


def sign(store, approval):
    value = payload(approval)
    with store.connection() as db:
        row = db.execute(
            "SELECT key_id,secret FROM approval_receipt_key WHERE singleton=1"
        ).fetchone()
    return {
        "payload": value,
        "key_id": row["key_id"],
        "algorithm": "HMAC-SHA256",
        "signature": hmac.new(row["secret"], digest(value).encode(), hashlib.sha256).hexdigest(),
    }


def valid(store, approval):
    try:
        receipt = approval["receipt"]
        if receipt["payload"] != payload(approval) or receipt["algorithm"] != "HMAC-SHA256":
            return False
        expected = sign(store, approval)
        return receipt["key_id"] == expected["key_id"] and hmac.compare_digest(
            receipt["signature"], expected["signature"]
        )
    except (KeyError, TypeError, ValueError):
        return False


def verify_current(store, job):
    approval = job["state"].get("approval")
    if job["product"] != "APPROVED_REPAIR" or not approval or not valid(store, approval):
        reject(
            "APPROVAL_RECEIPT_INVALID",
            "원본·변경계획에 연결된 승인 기록을 확인하지 못했습니다.",
            409,
        )
    return {
        "signature_valid": True,
        "source_hash": approval["source_hash"],
        "plan_digest": approval["plan_digest"],
        "receipt_digest": digest(approval["receipt"]),
        "historical_receipt_only": True,
        "receipt": json.loads(json.dumps(approval["receipt"])),
    }
