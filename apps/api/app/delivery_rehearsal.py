"""Operator-only local synthetic entitlement. No HTTP issuance and never production."""

from __future__ import annotations

import argparse
import time

from .config import get_settings
from .delivery_inputs import reject

SYNTHETIC_SOURCE_HASHES = {
    # Frozen D08 complex synthetic acceptance input.
    "acab2178721eceec8315704b0f668e4fb813bffda23db5656a45dac826573754",
    "7065c57aeb63185f1feff0992e48029ad3c09feb6878fc90bd605c0d79221e83",
    "e48981a5953e24507e60549fd345f208886049d0d677a3fb06b4d8981b3ac070",
}


def entitled(job: dict, app_env: str, hosted_synthetic: bool = False) -> bool:
    if job["product"] != "APPROVED_REPAIR":
        return False
    if job["state"].get("order_id"):
        from .delivery_rights import payment_grant

        return bool(payment_grant(job, app_env))
    grant = job["state"].get("internal_grant") or {}
    return (
        (
            (app_env == "internal_beta" and grant.get("kind") == "INTERNAL_SYNTHETIC")
            or (
                app_env == "hosted_beta"
                and hosted_synthetic
                and grant.get("kind") == "HOSTED_SYNTHETIC"
                and grant.get("owner") == job["owner"]
                and grant.get("plan_digest") == (job["state"].get("plan") or {}).get("digest")
            )
        )
        and job["product"] == "APPROVED_REPAIR"
        and grant.get("job_id") == job["id"]
        and grant.get("source_hash") == job["snapshot"]["source_hash"]
        and grant.get("source_hash") in SYNTHETIC_SOURCE_HASHES
        and grant.get("expires_at", 0) > time.time()
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    args = parser.parse_args()
    if get_settings().app_env != "internal_beta":
        reject("LOCAL_REHEARSAL_ONLY", "내부 합성 검증 환경만 허용합니다.")
    from .delivery_api import get_store

    store = get_store()
    with store.connection() as db:
        row = db.execute("SELECT owner FROM jobs WHERE id=?", (args.job_id,)).fetchone()
    if not row:
        reject("JOB_NOT_FOUND", "합성 검증 작업이 없습니다.")
    job = store.load(row["owner"], args.job_id)
    if job["state"].get("order_id"):
        reject("ORDER_ALREADY_LINKED", "주문에 내부 검증권을 덧붙일 수 없습니다.")
    if job["product"] == "TWO_FILE_COMPARISON":
        from .comparison_service import grant_comparison

        grant_comparison(store, job, get_settings())
        print("Internal synthetic comparison grant issued; no repair right or payment created.")
        return
    if job["snapshot"]["source_hash"] not in SYNTHETIC_SOURCE_HASHES:
        reject("SYNTHETIC_FIXTURE_REQUIRED", "고정된 합성 입력만 허용합니다.")
    state = {
        **job["state"],
        "internal_grant": {
            "kind": "INTERNAL_SYNTHETIC",
            "job_id": job["id"],
            "source_hash": job["snapshot"]["source_hash"],
            "expires_at": job["expires"],
        },
    }
    store.update(job, job["revision"], state)
    print(
        "Internal synthetic rehearsal granted; payment unchanged; change approval still required."
    )


if __name__ == "__main__":
    main()
