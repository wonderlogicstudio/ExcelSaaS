from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

import httpx

from release_config import API_RELEASE, CONFIRM_MUTATION, PROJECT, REGION, REPO, SERVICE, SOURCE_FREEZE, WEB_RELEASE, WORKER_HOST

G = r"C:\Users\JinwonLee\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
phase = sys.argv[1] if len(sys.argv) > 1 else ""
WEB_RELEASE.mkdir(parents=True, exist_ok=True)
BASE_ENV = {**os.environ, "WRANGLER_SEND_METRICS": "false", "CI": "1", "CLOUDSDK_CORE_DISABLE_PROMPTS": "1"}


def save_new(name: str, value: object) -> None:
    path = WEB_RELEASE / f"{name}.json"
    if path.exists():
        raise SystemExit(f"Refusing to overwrite existing evidence: {path}")
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read(name: str):
    return json.loads((WEB_RELEASE / f"{name}.json").read_text(encoding="utf-8"))


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def source_freeze_sha() -> str:
    return hashlib.sha256(SOURCE_FREEZE.read_bytes()).hexdigest()


def require_mutation() -> None:
    if "--confirm-mutation" not in sys.argv or sys.argv[sys.argv.index("--confirm-mutation") + 1] != CONFIRM_MUTATION:
        raise SystemExit(f"Refusing Worker mutation without --confirm-mutation {CONFIRM_MUTATION}")


def run(argv: list[str], label: str, parse: bool = False, extra: dict | None = None):
    p = subprocess.run(argv, cwd=REPO, env=extra or BASE_ENV, capture_output=True, text=True, encoding="utf-8", errors="replace")
    with (WEB_RELEASE / "commands.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"phase": phase, "command": label, "exit_code": p.returncode}) + "\n")
    if p.returncode:
        raise SystemExit(p.returncode)
    return json.loads(p.stdout) if parse else p.stdout


def g(*args):
    return run([G, *args, "--project", PROJECT, "--format=json", "--quiet"], "gcloud " + " ".join(args[:4]), True)


def w(*args, parse=False):
    return run(["npx.cmd", "--offline", "--no-install", "wrangler", *args, "--config", "infra/cloudflare/wrangler.jsonc"], "wrangler " + " ".join(args[:3]), parse)


def iam_hash() -> str:
    data = g("run", "services", "get-iam-policy", SERVICE, "--region", REGION)
    assert not any(m in {"allUsers", "allAuthenticatedUsers"} for b in data.get("bindings", []) for m in b.get("members", []))
    return digest(data)


def service_api() -> dict:
    return g("run", "services", "describe", SERVICE, "--region", REGION)


def api_after() -> dict:
    after = json.loads((API_RELEASE / "after.json").read_text(encoding="utf-8"))
    svc = service_api()
    assert svc["status"]["latestReadyRevisionName"] == after["revision"]
    assert svc["spec"]["template"]["spec"]["containers"][0]["image"] == after["image"]
    assert any(t.get("revisionName") == after["revision"] and t.get("percent") == 100 for t in svc["status"].get("traffic", []))
    return {"revision": after["revision"], "image": after["image"], "iam": iam_hash(), "source_freeze_sha256": after["source_freeze_sha256"]}


def worker() -> str:
    data = w("deployments", "list", "--json", parse=True)
    data = data["deployments"] if isinstance(data, dict) else data
    versions = max(data, key=lambda x: x["created_on"])["versions"]
    assert len(versions) == 1 and versions[0]["percentage"] == 100
    return versions[0]["version_id"]


def bindings(version: str):
    return w("versions", "view", version, "--json", parse=True)["resources"]["bindings"]


def access():
    rows = []
    for path in ["/", "/precision-verification", "/compare", "/automation", "/help", "/orders", "/api/v1/scans", "/api/v1/formula-audits", "/api/v1/delivery"]:
        r = httpx.get(WORKER_HOST + path, follow_redirects=False, timeout=30)
        ok = r.status_code == 302 and urlparse(r.headers.get("location", "")).hostname == "old-breeze-11c7.cloudflareaccess.com"
        assert ok, path
        rows.append({"path": path, "status": r.status_code, "existing_access": ok})
    return rows


def dist_assets() -> dict[str, str]:
    return {p.relative_to(REPO).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in (REPO / "apps/web/dist").rglob("*") if p.is_file()}

def verify_frontend_source_freeze() -> None:
    freeze = json.loads(SOURCE_FREEZE.read_text(encoding="utf-8"))
    frozen = {item["repo_path"]: item["sha256"] for item in freeze.get("frontend_source", [])}
    if not frozen:
        raise SystemExit("frontend source freeze missing")
    current = {path: hashlib.sha256((REPO / path).read_bytes()).hexdigest() for path in frozen}
    assert current == frozen


if phase == "baseline":
    api = api_after(); version = worker()
    save_new("baseline", {"worker": version, "binding_hash": digest(bindings(version)), "api": api, "access": access(), "source_freeze_sha256": source_freeze_sha()})
elif phase == "build":
    b = read("baseline"); assert source_freeze_sha() == b["source_freeze_sha256"]; verify_frontend_source_freeze(); assert api_after() == b["api"]; assert worker() == b["worker"]
    e = {**BASE_ENV, "VITE_PRODUCT_ENV": "hosted_beta", "VITE_API_BASE_URL": "/api", "VITE_FORMULA_AUDIT_HOSTED_BETA_ENABLED": "true", "VITE_FORMULA_AUDIT_INTERNAL_BETA_ENABLED": "false", "VITE_FEEDBACK_CAPTURE_ENABLED": "false", "VITE_HOSTED_BETA_FEEDBACK_ENABLED": "false", "VITE_DELIVERY_BETA_ENABLED": "true"}
    run(["npm.cmd", "run", "build", "--workspace", "@workbookcare/web", "--", "--mode", "hosted_beta"], "npm build hosted beta", extra=e)
    save_new("web", {"flags": {k: v for k, v in e.items() if k.startswith("VITE_")}, "assets": dist_assets(), "source_freeze_sha256": b["source_freeze_sha256"]})
elif phase == "upload":
    require_mutation(); b = read("baseline"); web = read("web"); assert source_freeze_sha() == b["source_freeze_sha256"] == web["source_freeze_sha256"]; verify_frontend_source_freeze(); assert api_after() == b["api"]; assert worker() == b["worker"]; assert dist_assets() == web["assets"]
    overrides = ["--var", "FORMULA_AUDIT_ENABLED:true", "--var", "DELIVERY_BETA_ENABLED:true"]
    w("versions", "upload", "--dry-run", "--keep-vars", "--strict", *overrides)
    out = w("versions", "upload", "--keep-vars", "--strict", *overrides, "--tag", "journey-feedback01", "--message", "JOURNEY feedback verified UI build")
    v = re.search(r"Worker Version ID:\s*([a-f0-9-]{36})", out).group(1)
    assert digest(bindings(v)) == b["binding_hash"]
    save_new("upload", {"worker": v, "all_bindings_equal": True, "api": api_after(), "source_freeze_sha256": b["source_freeze_sha256"]})
elif phase == "deploy":
    require_mutation(); b = read("baseline"); upload = read("upload"); v = upload["worker"]; assert source_freeze_sha() == b["source_freeze_sha256"]; verify_frontend_source_freeze(); assert api_after() == b["api"]; assert worker() == b["worker"]; assert digest(bindings(v)) == b["binding_hash"]
    w("versions", "deploy", v + "@100", "--yes", "--message", "JOURNEY feedback verified UI build")
    assert worker() == v
    save_new("live", {"worker": v, "rollback_worker": b["worker"], "api": api_after(), "all_bindings_equal": True, "access": access(), "source_freeze_sha256": b["source_freeze_sha256"]})
else:
    raise SystemExit("phase: baseline | build | upload | deploy")
