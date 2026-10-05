from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

import httpx
import yaml

from release_config import (
    API_GATEWAY,
    API_GATEWAY_API,
    API_GATEWAY_LOCATION,
    API_RELEASE,
    CONFIRM_MUTATION,
    EXPECTED_BASE_IMAGE_DIGEST,
    EXPECTED_BASE_REVISION,
    EXPECTED_WORKER_VERSION,
    IMAGE_OUT,
    LIVE_BASELINE,
    PROJECT,
    REGION,
    SERVICE,
    SOURCE_FREEZE,
    WORKER_HOST,
)

G = r"C:\Users\JinwonLee\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
phase = sys.argv[1] if len(sys.argv) > 1 else ""
API_RELEASE.mkdir(parents=True, exist_ok=True)
BASE_ENV = {**os.environ, "CLOUDSDK_CORE_DISABLE_PROMPTS": "1", "WRANGLER_SEND_METRICS": "false", "CI": "1"}


def save_new(name: str, value: object) -> None:
    path = API_RELEASE / name
    if path.exists():
        raise SystemExit(f"Refusing to overwrite existing evidence: {path}")
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read(name: str):
    return json.loads((API_RELEASE / name).read_text(encoding="utf-8"))


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_mutation() -> None:
    if "--confirm-mutation" not in sys.argv or sys.argv[sys.argv.index("--confirm-mutation") + 1] != CONFIRM_MUTATION:
        raise SystemExit(f"Refusing cloud mutation without --confirm-mutation {CONFIRM_MUTATION}")


def run(argv: list[str], label: str, parse: bool = True):
    p = subprocess.run(argv, cwd=Path(__file__).resolve().parents[4], env=BASE_ENV, capture_output=True, text=True, encoding="utf-8", errors="replace")
    with (API_RELEASE / "commands.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"phase": phase, "command": label, "exit_code": p.returncode}) + "\n")
    if p.returncode:
        print(json.dumps({"provider_codes": re.findall(r"\[code: (\d+)\]", p.stdout + p.stderr)}), flush=True)
        raise SystemExit(p.returncode)
    return json.loads(p.stdout) if parse else p.stdout


def g(*args):
    return run([G, *args, "--project", PROJECT, "--format=json", "--quiet"], "gcloud " + " ".join(args[:4]))


def w(*args, parse=True):
    return run(["npx.cmd", "--offline", "--no-install", "wrangler", *args, "--config", "infra/cloudflare/wrangler.jsonc"], "wrangler " + " ".join(args[:3]), parse)


def service():
    return g("run", "services", "describe", SERVICE, "--region", REGION)


def revision(name: str):
    return g("run", "revisions", "describe", name, "--region", REGION)


def container_from_revision(name: str) -> dict:
    return revision(name)["spec"]["containers"][0]


def iam_hash() -> str:
    data = g("run", "services", "get-iam-policy", SERVICE, "--region", REGION)
    assert not any(m in {"allUsers", "allAuthenticatedUsers"} for b in data.get("bindings", []) for m in b.get("members", []))
    return digest(data)


def gateway():
    gw = g("api-gateway", "gateways", "describe", API_GATEWAY, "--location", API_GATEWAY_LOCATION)
    cfg = g("api-gateway", "api-configs", "describe", gw["apiConfig"].split("/")[-1], "--api", API_GATEWAY_API, "--view=FULL")
    spec = yaml.safe_load(base64.b64decode(cfg["openapiDocuments"][0]["document"]["contents"]))
    return gw, cfg, spec


def worker():
    data = w("deployments", "list", "--json")
    data = data["deployments"] if isinstance(data, dict) else data
    versions = max(data, key=lambda x: x["created_on"])["versions"]
    assert len(versions) == 1 and versions[0]["percentage"] == 100
    return versions[0]["version_id"]


def bindings(version: str):
    return w("versions", "view", version, "--json")["resources"]["bindings"]


def env_map_from_container(container: dict) -> dict[str, str]:
    return {item["name"]: item.get("value", "") for item in container.get("env", [])}


def env_hash_from_container(container: dict) -> str:
    return digest(env_map_from_container(container))


def access():
    rows = []
    for path in ["/", "/api/v1/scans", "/api/v1/formula-audits", "/api/v1/delivery"]:
        r = httpx.get(WORKER_HOST + path, follow_redirects=False, timeout=30)
        ok = r.status_code == 302 and urlparse(r.headers.get("location", "")).hostname == "old-breeze-11c7.cloudflareaccess.com"
        assert ok, path
        rows.append({"path": path, "status": r.status_code, "existing_access": ok})
    return rows


def image_meta(require_pushed: bool = False) -> dict:
    meta = json.loads((IMAGE_OUT / "build.json").read_text(encoding="utf-8"))
    if require_pushed:
        assert meta.get("pushed") is True and meta.get("registry_digest_asserted") is True
    return meta


def source_freeze_hash() -> str:
    return file_sha(SOURCE_FREEZE)


def assert_old_traffic(s: dict, baseline: dict) -> None:
    assert any(t.get("revisionName") == baseline["revision"] and t.get("percent") == 100 for t in s["status"].get("traffic", []))


def baseline_record() -> dict:
    live = json.loads(LIVE_BASELINE.read_text(encoding="utf-8"))
    s = service(); gw, cfg, spec = gateway(); version = worker()
    assert s["status"]["latestReadyRevisionName"] == EXPECTED_BASE_REVISION == live["api_revision"]
    assert s["spec"]["template"]["spec"]["containers"][0]["image"].endswith(EXPECTED_BASE_IMAGE_DIGEST)
    assert version == EXPECTED_WORKER_VERSION == live["worker_version"]
    container = container_from_revision(EXPECTED_BASE_REVISION)
    return {
        "revision": EXPECTED_BASE_REVISION,
        "image": s["spec"]["template"]["spec"]["containers"][0]["image"],
        "traffic_hash": digest(s["status"].get("traffic", [])),
        "iam": iam_hash(),
        "gateway_config": gw["apiConfig"].split("/")[-1],
        "gateway_state": gw["state"],
        "gateway_spec": digest(spec),
        "gateway_identity": digest(cfg["gatewayServiceAccount"]),
        "worker_version": version,
        "worker_bindings": digest(bindings(version)),
        "env_hash": env_hash_from_container(container),
        "container_command_hash": digest(container.get("command", [])),
        "container_args_hash": digest(container.get("args", [])),
        "startup_probe_hash": digest(container.get("startupProbe")),
        "max_instances": s["spec"]["template"]["metadata"]["annotations"].get("autoscaling.knative.dev/maxScale"),
        "access": access(),
        "source_freeze_sha256": source_freeze_hash(),
    }


def env_arg(container: dict) -> list[str]:
    values = env_map_from_container(container)
    if not values:
        return ["--clear-env-vars"]
    delimiter = "@"
    if any(delimiter in k or delimiter in v for k, v in values.items()):
        delimiter = "|"
    if any(delimiter in k or delimiter in v for k, v in values.items()):
        raise SystemExit("Baseline env contains unsupported delimiter for gcloud argument construction")
    payload = f"^{delimiter}^" + delimiter.join(f"{k}={v}" for k, v in sorted(values.items()))
    return ["--set-env-vars", payload]


def startup_probe_arg(container: dict) -> list[str]:
    probe = container.get("startupProbe")
    if not probe:
        return ["--startup-probe", ""]
    http = probe.get("httpGet", {})
    parts = []
    if "path" in http: parts.append(f"httpGet.path={http['path']}")
    if "port" in http: parts.append(f"httpGet.port={http['port']}")
    for key in ["failureThreshold", "periodSeconds", "timeoutSeconds", "initialDelaySeconds"]:
        if key in probe:
            parts.append(f"{key}={probe[key]}")
    return ["--startup-probe", ",".join(parts)]


def command_args(container: dict) -> list[str]:
    args: list[str] = []
    if container.get("command"):
        args += ["--command", ",".join(container["command"])]
    if container.get("args"):
        args += ["--args", ",".join(container["args"])]
    return args


def assert_revision_matches_baseline(rev_name: str, baseline: dict) -> None:
    container = container_from_revision(rev_name)
    assert env_hash_from_container(container) == baseline["env_hash"]
    assert digest(container.get("command", [])) == baseline["container_command_hash"]
    assert digest(container.get("args", [])) == baseline["container_args_hash"]
    assert digest(container.get("startupProbe")) == baseline["startup_probe_hash"]


def assert_live_ready_for_traffic(baseline: dict, live: dict) -> None:
    s = service()
    assert iam_hash() == baseline["iam"]
    assert_old_traffic(s, baseline)
    assert live["image"] == image_meta(require_pushed=True)["image"]
    assert_revision_matches_baseline(live["revision"], baseline)
    proof = read("linux-rp03-runtime.json")
    assert proof["revision"] == live["verified_revision"]
    assert proof["image"] == live["image"]
    assert proof["source_freeze_sha256"] == baseline["source_freeze_sha256"]


def remove_release_tags() -> None:
    s = service()
    tags = sorted(t["tag"] for t in s["status"].get("traffic", []) if t.get("tag") in {"ux07-rp03", "ux07-live"})
    if tags:
        g("run", "services", "update-traffic", SERVICE, "--region", REGION, "--remove-tags", ",".join(tags))


if phase == "baseline":
    save_new("baseline.json", baseline_record())
elif phase == "image":
    b = read("baseline.json"); meta = image_meta(); assert meta["base_image"] == b["image"]
    save_new("image.json", {"image": meta["image"], "base_image": meta["base_image"], "overlay_count": meta["overlay_count"], "pushed": meta["pushed"], "source_freeze_sha256": source_freeze_hash()})
elif phase == "push":
    require_mutation(); meta = image_meta(); b = read("baseline.json"); assert meta["base_image"] == b["image"]
    token = run([G, "auth", "print-access-token"], "gcloud auth print-access-token", parse=False).strip()
    registry = "https://asia-northeast3-docker.pkg.dev"; repo = "workbookcare-beta/workbookcare-images/workbookcare-api"; api = registry + "/v2/" + repo
    manifest = (IMAGE_OUT / "manifest.json").read_bytes(); config = (IMAGE_OUT / "config.json").read_bytes(); layer = (IMAGE_OUT / "registry-layer.tar.gz").read_bytes()
    def sha_bytes(data: bytes) -> str: return "sha256:" + hashlib.sha256(data).hexdigest()
    with httpx.Client(auth=("oauth2accesstoken", token), timeout=120, follow_redirects=False) as client:
        for data in [config, layer]:
            d = sha_bytes(data); r = client.head(api + "/blobs/" + d)
            if r.status_code != 200:
                assert r.status_code == 404, r.status_code
                r = client.post(api + "/blobs/uploads/"); r.raise_for_status(); loc = r.headers["location"]
                assert urlparse(loc).hostname == "asia-northeast3-docker.pkg.dev"
                r = client.put(loc + ("&" if "?" in loc else "?") + "digest=" + d, content=data, headers={"Content-Type":"application/octet-stream"})
                assert r.status_code in {201, 202}, r.status_code
        manifest_digest = sha_bytes(manifest); tag = "monthly-ux07-" + manifest_digest.split(":")[1][:12]
        r = client.put(api + "/manifests/" + tag, content=manifest, headers={"Content-Type":"application/vnd.oci.image.manifest.v1+json"}); r.raise_for_status(); assert r.headers.get("docker-content-digest") == manifest_digest
    meta["pushed"] = True; meta["registry_tag"] = tag; meta["registry_digest_asserted"] = True
    (IMAGE_OUT / "build.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    save_new("push.json", {"image": meta["image"], "tag": tag, "digest_asserted": True, "same_registry_host": True})
elif phase == "stage":
    require_mutation(); b = read("baseline.json"); meta = image_meta(require_pushed=True); s = service(); assert_old_traffic(s, b); assert iam_hash() == b["iam"]
    g("run", "deploy", SERVICE, "--region", REGION, "--image", meta["image"], "--no-traffic", "--tag", "ux07-rp03", "--command", "python", "--args", "-m,release_tools.rp03_startup_wrapper", "--startup-probe", "httpGet.path=/health,httpGet.port=8080,failureThreshold=60,periodSeconds=3,timeoutSeconds=1", "--set-env-vars", "DELIVERY_RUNTIME_VERIFY=false")
    s = service(); rev = s["status"]["latestCreatedRevisionName"]; v = revision(rev); cond = {c["type"]: c["status"] for c in v["status"]["conditions"]}
    assert cond.get("Ready") == "True" and cond.get("ContainerHealthy") == "True"; assert_old_traffic(s, b); assert iam_hash() == b["iam"]
    save_new("stage.json", {"revision": rev, "image": meta["image"], "conditions": cond, "rollback_revision": b["revision"], "traffic_unchanged": True, "temporary_command_wrapper": True, "source_freeze_sha256": b["source_freeze_sha256"]})
elif phase == "proof":
    st = read("stage.json"); logs = g("logging", "read", f'resource.type="cloud_run_revision" AND resource.labels.revision_name="{st["revision"]}" AND (jsonPayload.event="delivery_runtime_verified" OR jsonPayload.event="monthly_rp03_runtime_verified")', "--limit", "20")
    events = [e.get("jsonPayload", {}) for e in logs]
    base = [e for e in events if e.get("event") == "delivery_runtime_verified"]
    rp03 = [e for e in events if e.get("event") == "monthly_rp03_runtime_verified"]
    assert base and rp03, events
    assert any(e.get("reference_cases") == 20 and e.get("repair_profiles") == 2 and e.get("artifacts") == 6 for e in base)
    assert any(e.get("patch_count") == 1 and e.get("expected_value_ok") is True and e.get("source_preserved") is True and e.get("monthly_detector_target_candidates") == {"before": 1, "after": 0} and e.get("decoded_artifact_count") == 3 and e.get("decoded_artifacts_nonempty") is True for e in rp03)
    save_new("linux-rp03-runtime.json", {"revision": st["revision"], "image": st["image"], "base_runtime_verified": True, "rp03_runtime_verified": True, "source_freeze_sha256": st["source_freeze_sha256"], "event_count": len(events)})
elif phase == "live":
    require_mutation(); b = read("baseline.json"); st = read("stage.json"); proof = read("linux-rp03-runtime.json"); assert proof["revision"] == st["revision"]; assert proof["image"] == st["image"]
    baseline_container = container_from_revision(b["revision"]); s = service(); assert_old_traffic(s, b); assert iam_hash() == b["iam"]
    deploy_args = ["run", "deploy", SERVICE, "--region", REGION, "--image", st["image"], "--no-traffic", "--tag", "ux07-live", *command_args(baseline_container), *startup_probe_arg(baseline_container), *env_arg(baseline_container)]
    g(*deploy_args)
    s = service(); rev = s["status"]["latestCreatedRevisionName"]; v = revision(rev); cond = {c["type"]: c["status"] for c in v["status"]["conditions"]}
    assert cond.get("Ready") == "True" and cond.get("ContainerHealthy") == "True"; assert_old_traffic(s, b); assert iam_hash() == b["iam"]; assert_revision_matches_baseline(rev, b)
    save_new("live.json", {"revision": rev, "image": st["image"], "verified_revision": st["revision"], "rollback_revision": b["revision"], "conditions": cond, "baseline_runtime_hashes_restored": True, "traffic_unchanged": True, "source_freeze_sha256": b["source_freeze_sha256"]})
elif phase == "traffic":
    require_mutation(); b = read("baseline.json"); live = read("live.json"); assert_live_ready_for_traffic(b, live)
    g("run", "services", "update-traffic", SERVICE, "--region", REGION, "--to-revisions", live["revision"] + "=100")
    remove_release_tags()
    s = service(); assert any(t.get("revisionName") == live["revision"] and t.get("percent") == 100 for t in s["status"].get("traffic", [])); assert iam_hash() == b["iam"]
    save_new("traffic.json", {"revision": live["revision"], "image": live["image"], "rollback_revision": b["revision"], "traffic_hash": digest(s["status"].get("traffic", [])), "temporary_tags_removed": True})
elif phase == "after":
    b = read("baseline.json"); live = read("live.json"); traffic = read("traffic.json"); assert traffic["revision"] == live["revision"]; s = service(); gw, cfg, spec = gateway(); version = worker()
    assert iam_hash() == b["iam"]; assert s["status"]["latestReadyRevisionName"] == live["revision"]; assert s["spec"]["template"]["spec"]["containers"][0]["image"] == live["image"]
    assert any(t.get("revisionName") == live["revision"] and t.get("percent") == 100 for t in s["status"].get("traffic", []))
    assert gw["apiConfig"].endswith("/" + b["gateway_config"]); assert digest(spec) == b["gateway_spec"]; assert digest(cfg["gatewayServiceAccount"]) == b["gateway_identity"]
    assert version == b["worker_version"] and digest(bindings(version)) == b["worker_bindings"]; assert_revision_matches_baseline(live["revision"], b)
    save_new("after.json", {"revision": live["revision"], "image": live["image"], "worker_version": version, "gateway_config": b["gateway_config"], "security_invariants_preserved": True, "private_iam": True, "access": access(), "rollback_revision": b["revision"], "source_freeze_sha256": b["source_freeze_sha256"]})
else:
    raise SystemExit("phase: baseline | image | push | stage | proof | live | traffic | after")
