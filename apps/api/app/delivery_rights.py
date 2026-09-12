"""Separate paid test entitlement; never grants customer change approval."""

from __future__ import annotations

import time

from .delivery_inputs import digest


def payment_grant(job, app_env):
    state = job["state"]
    grant = state.get("payment_grant") or {}
    if (
        app_env not in {"internal_beta", "hosted_beta"}
        or state.get("payment") != "PAID"
        or grant.get("kind") != "SANDBOX_ORDER"
        or grant.get("mode") not in {"LOCAL_CONTRACT", "TOSS_TEST"}
        or (grant.get("mode") == "LOCAL_CONTRACT" and app_env != "internal_beta")
        or grant.get("owner") != job["owner"]
        or grant.get("job_id") != job["id"]
        or grant.get("order_id") != state.get("order_id")
        or grant.get("product_id") != job["product"]
        or grant.get("expires_at", 0) <= time.time()
    ):
        return None
    expected_input = job["snapshot"].get("source_pair_hash", job["snapshot"]["source_hash"])
    if grant.get("input_hash") != expected_input:
        return None
    if job["product"] == "TWO_FILE_COMPARISON":
        return grant if grant.get("spec_hash") == state.get("spec_hash") else None
    if job["product"] != "APPROVED_REPAIR":
        return None
    plan = state.get("plan") or {}
    policy = state.get("policy") or {}
    ids = {patch["candidate_id"] for patch in plan.get("patches", [])}
    if (
        not ids
        or not ids <= set(grant.get("scope_ids", []))
        or plan.get("profile_version") != grant.get("profile")
        or digest({k: v for k, v in policy.items() if k != "targets"})
        != grant.get("policy_base_hash")
    ):
        return None
    return grant


def effective_repair_grant(job, app_env):
    if job["state"].get("order_id"):
        return payment_grant(job, app_env)
    return job["state"].get("internal_grant")
