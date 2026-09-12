"""A delivery is a complete, matching set, including at later downloads."""

from __future__ import annotations

import hashlib
import json


def stored_delivery_valid(store, job_id, delivery, required):
    if not isinstance(delivery, dict) or set(delivery.get("files", {})) != set(required):
        return False
    with store.connection() as db:
        rows = db.execute(
            "SELECT kind,data,manifest FROM delivery_artifacts WHERE job_id=? AND delivery_id=?",
            (job_id, delivery.get("delivery_id")),
        ).fetchall()
    if {r["kind"] for r in rows} != set(required):
        return False
    try:
        for row in rows:
            manifest = json.loads(row["manifest"])
            info = delivery["files"][row["kind"]]
            if manifest["files"] != delivery["files"] or manifest["job_id"] != job_id:
                return False
            if (
                len(row["data"]) != info["bytes"]
                or hashlib.sha256(row["data"]).hexdigest() != info["sha256"]
            ):
                return False
    except (ValueError, TypeError, KeyError):
        return False
    return True


def quarantine_broken_delivery(store, job):
    if job["state"]["status"] != "READY":
        return job
    required = (
        {"REPAIRED_XLSX", "CHANGES_XLSX", "VERIFICATION_HTML"}
        if job["product"] == "APPROVED_REPAIR"
        else {"COMPARISON_REPORT_XLSX", "COMPARISON_VERIFICATION_HTML"}
    )
    if stored_delivery_valid(store, job["id"], job["state"].get("delivery"), required):
        return job
    return store.update(
        job,
        job["revision"],
        {
            **job["state"],
            "status": "QUARANTINED",
            "delivery": None,
            "failure_code": "STORED_PACKAGE_INTEGRITY_FAILED",
        },
    )
