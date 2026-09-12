"""Private local adapter. Cloud Run's ephemeral filesystem is NOT durable commerce storage."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

from .delivery_inputs import reject

INPUT_TTL_SECONDS = 15 * 60


class DeliveryStore:
    def __init__(self, directory: Path):
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path = directory / "delivery.sqlite3"
        with self.connection() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, owner TEXT NOT NULL, "
                "product TEXT NOT NULL, source BLOB NOT NULL, snapshot TEXT NOT NULL, state "
                "TEXT NOT NULL, revision INTEGER NOT NULL, expires REAL NOT NULL, request_key "
                "TEXT NOT NULL, UNIQUE(owner,request_key))"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS request_limits (owner TEXT PRIMARY KEY, window "
                "INTEGER NOT NULL, count INTEGER NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS delivery_artifacts (job_id TEXT NOT NULL "
                "REFERENCES jobs(id) ON DELETE CASCADE, kind TEXT NOT NULL, "
                "delivery_id TEXT NOT NULL, data BLOB NOT NULL, manifest TEXT NOT "
                "NULL, PRIMARY KEY(job_id,kind))"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS secondary_sources (job_id TEXT PRIMARY "
                "KEY REFERENCES jobs(id) ON DELETE CASCADE, source BLOB NOT NULL, "
                "snapshot TEXT NOT NULL)"
            )
            from .payment_service import install

            install(db)
            from .delivery_operations import install as install_operations

            install_operations(db)
            from .delivery_receipts import install as install_receipts

            install_receipts(db)
        if os.name != "nt":
            self.path.chmod(0o600)

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA secure_delete=ON")
        db.execute("PRAGMA foreign_keys=ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    def rate_limit(self, owner: str) -> None:
        window = int(time.time()) // 60
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM request_limits WHERE owner=?", (owner,)).fetchone()
            count = row["count"] + 1 if row and row["window"] == window else 1
            if count > 60:
                reject("DELIVERY_RATE_LIMITED", "요청이 많습니다. 잠시 후 다시 시도하세요.", 429)
            db.execute(
                "INSERT OR REPLACE INTO request_limits VALUES (?,?,?)", (owner, window, count)
            )
            db.execute("DELETE FROM request_limits WHERE window < ?", (window - 2,))

    def cleanup(self, now: float | None = None) -> int:
        from .delivery_operations import maintain

        return maintain(self, now)

    def create(
        self,
        owner: str,
        source: bytes,
        snapshot: dict,
        request_key: str,
        *,
        product: str = "APPROVED_REPAIR",
        secondary: tuple[bytes, dict] | None = None,
    ) -> dict:
        if product not in {"APPROVED_REPAIR", "TWO_FILE_COMPARISON"} or (
            product == "TWO_FILE_COMPARISON"
        ) != (secondary is not None):
            reject("INVALID_PRODUCT_SOURCE", "상품과 원본 개수가 일치하지 않습니다.")
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            old = db.execute(
                "SELECT id,snapshot,expires,product FROM jobs WHERE owner=? AND request_key=?",
                (owner, request_key),
            ).fetchone()
            if old:
                if (
                    json.loads(old["snapshot"])["source_hash"] != snapshot["source_hash"]
                    or old["product"] != product
                    or json.loads(old["snapshot"]).get("source_pair_hash")
                    != snapshot.get("source_pair_hash")
                ):
                    reject(
                        "IDEMPOTENCY_CONFLICT", "같은 요청 식별자로 원본을 바꿀 수 없습니다.", 409
                    )
                job_id = old["id"]
            else:
                if (
                    db.execute("SELECT COUNT(*) FROM jobs WHERE owner=?", (owner,)).fetchone()[0]
                    >= 10
                ):
                    reject("JOB_LIMIT", "진행 중인 사전 검사 한도를 초과했습니다.", 429)
                job_id = str(uuid.uuid4())
                state = {
                    "status": "INPUT_READY",
                    "policy": None,
                    "preflight": None,
                    "payment": "NOT_PURCHASED",
                    "approval": None,
                    "artifacts": None,
                }
                db.execute(
                    "INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?)",
                    (
                        job_id,
                        owner,
                        product,
                        source,
                        json.dumps(snapshot),
                        json.dumps(state),
                        1,
                        time.time() + INPUT_TTL_SECONDS,
                        request_key,
                    ),
                )
                if secondary is not None:
                    db.execute(
                        "INSERT INTO secondary_sources VALUES (?,?,?)",
                        (job_id, secondary[0], json.dumps(secondary[1])),
                    )
        return self.load(owner, job_id)

    def load_secondary(self, job: dict) -> bytes:
        with self.connection() as db:
            row = db.execute(
                "SELECT * FROM secondary_sources WHERE job_id=?", (job["id"],)
            ).fetchone()
        if (
            row is None
            or hashlib.sha256(row["source"]).hexdigest()
            != json.loads(row["snapshot"])["source_hash"]
        ):
            reject("INPUT_INTEGRITY_FAILED", "두 번째 원본의 무결성을 확인하지 못했습니다.", 409)
        return row["source"]

    def load(self, owner: str, job_id: str) -> dict:
        with self.connection() as db:
            row = db.execute(
                "SELECT * FROM jobs WHERE id=? AND owner=?", (job_id, owner)
            ).fetchone()
        if not row:
            reject("JOB_NOT_FOUND", "작업이 없거나 이 브라우저 계정의 작업이 아닙니다.", 404)
        if row["expires"] <= time.time():
            self.cleanup()
            reject("INPUT_EXPIRED", "원본 보관 기간이 끝났습니다. 새 파일로 다시 시작하세요.", 410)
        job = dict(row)
        job["snapshot"] = json.loads(job["snapshot"])
        job["state"] = json.loads(job["state"])
        if hashlib.sha256(job["source"]).hexdigest() != job["snapshot"]["source_hash"]:
            reject(
                "INPUT_INTEGRITY_FAILED", "원본 무결성 확인에 실패하여 작업을 차단했습니다.", 409
            )
        if job["product"] == "TWO_FILE_COMPARISON":
            self.load_secondary(job)
        from .delivery_storage_validation import quarantine_broken_delivery

        return quarantine_broken_delivery(self, job)

    def update(self, job: dict, revision: int, state: dict) -> dict:
        with self.connection() as db:
            changed = db.execute(
                "UPDATE jobs SET state=?, revision=revision+1 WHERE id=? AND owner=? AND "
                "revision=? AND expires>?",
                (json.dumps(state), job["id"], job["owner"], revision, time.time()),
            ).rowcount
            if changed != 1:
                reject(
                    "STALE_JOB", "다른 변경이 먼저 반영됐습니다. 최신 작업을 다시 확인하세요.", 409
                )
        return self.load(job["owner"], job["id"])

    def delete(self, owner: str, job_id: str) -> None:
        with self.connection() as db:
            db.execute("DELETE FROM jobs WHERE id=? AND owner=?", (job_id, owner))

    def list_jobs(self, owner: str) -> list[dict]:
        self.cleanup()
        with self.connection() as db:
            ids = [
                row["id"]
                for row in db.execute(
                    "SELECT id FROM jobs WHERE owner=? ORDER BY expires DESC", (owner,)
                )
            ]
        return [self.load(owner, job_id) for job_id in ids]
