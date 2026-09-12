"""Operator-only local synthetic entitlement. No HTTP issuance and never production."""

from __future__ import annotations

import argparse
import time

from .config import get_settings
from .delivery_inputs import reject

SYNTHETIC_SOURCE_HASHES = {"e48981a5953e24507e60549fd345f208886049d0d677a3fb06b4d8981b3ac070"}


def entitled(job: dict, app_env: str) -> bool:
    grant = job["state"].get("internal_grant", {})
    return (
        app_env == "internal_beta"
        and grant.get("kind") == "INTERNAL_SYNTHETIC"
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
