"""Public synthetic acceptance oracle, NOT an authorization server or repair engine.
Inputs represent server-verified facts in a specification test, not HTTP payloads.
No workbook, network, payment, secret, storage or production action is performed.
"""
from copy import deepcopy

REQUIRED = {
    "APPROVED_REPAIR": {"repaired_workbook", "change_log", "verification_report"},
    "TWO_FILE_COMPARISON": {"comparison_report", "comparison_verification"},
}

def example_context(product="APPROVED_REPAIR"):
    return dict(product=product, purchased_product=product, owner_ok=True,
        payment="PAID", entitlement="ACTIVE", refund="NONE",
        source_match=True, source_available=True, profile_verified=True,
        plan_ready=True, approval="APPROVED", approval_expired=False,
        approval_plan_match=True, patch_count=2, prevalidation="PASS",
        job="SUCCEEDED", execution_authorized=True, publication_allowed=True,
        validation="PASS", artifact="READY", artifact_expired=False,
        output_plan_match=True, artifacts=sorted(REQUIRED[product]))

def decide(context, action):
    """Return a reasoned allow/deny decision for the illustrative contract only."""
    c=deepcopy(context)
    if action not in {"execute", "download", "publish"}:
        return False,"UNKNOWN_ACTION"
    if c.get("product") not in REQUIRED:
        return False,"UNKNOWN_PRODUCT"
    if not c.get("owner_ok"):
        return False,"OWNER"
    if c.get("purchased_product") != c["product"]:
        return False,"PRODUCT"
    if c.get("payment") != "PAID" or c.get("entitlement") != "ACTIVE" or c.get("refund") != "NONE":
        return False,"ENTITLEMENT"
    if not c.get("publication_allowed"):
        return False,"REVOKED"
    if action == "execute":
        if not c.get("source_available") or not c.get("source_match"):
            return False,"SOURCE"
        if not c.get("profile_verified") or c.get("prevalidation") != "PASS":
            return False,"PREVALIDATION"
        if c["product"] == "APPROVED_REPAIR":
            if not c.get("plan_ready") or c.get("patch_count",0)<=0:
                return False,"NO_PLAN"
            if c.get("approval") != "APPROVED" or c.get("approval_expired"):
                return False,"APPROVAL"
            if not c.get("approval_plan_match"):
                return False,"STALE_APPROVAL"
        return True,"ELIGIBLE_TO_EXECUTE"
    if c.get("job") != "SUCCEEDED" or c.get("validation") != "PASS":
        return False,"NOT_VERIFIED"
    if not c.get("execution_authorized") or not c.get("output_plan_match"):
        return False,"OUTPUT_BINDING"
    if c.get("artifact") != "READY" or c.get("artifact_expired"):
        return False,"ARTIFACT"
    if not REQUIRED[c["product"]].issubset(set(c.get("artifacts",[]))):
        return False,"INCOMPLETE_DELIVERY"
    # An approval that expired AFTER an authorized completed execution does not,
    # by itself, void a still-valid download entitlement.
    return True,"DELIVERABLE"
