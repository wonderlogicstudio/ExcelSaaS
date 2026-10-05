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

from registry_location import normalize_registry_upload_location
from release_gcloud import env_restore_args, gcloud_entrypoint, gcloud_env

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
    TOOLS,
    WORKER_HOST,
)

G = gcloud_entrypoint()
phase = sys.argv[1] if len(sys.argv) > 1 else ""
LIVE_FAILURE_STATE = TOOLS.parent / "live-failure-state.json"
API_RELEASE.mkdir(parents=True, exist_ok=True)
BASE_ENV = gcloud_env({**os.environ, "CLOUDSDK_CORE_DISABLE_PROMPTS": "1", "WRANGLER_SEND_METRICS": "false", "CI": "1"})


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
    p = subprocess.run(argv, cwd=next(parent for parent in Path(__file__).resolve().parents if (parent / "package.json").is_file() and (parent / "apps/api").is_dir()), env=BASE_ENV, capture_output=True, text=True, encoding="utf-8", errors="replace")
    with (API_RELEASE / "commands.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"phase": phase, "command": label, "exit_code": p.returncode}) + "\n")
    if p.returncode:
        print(json.dumps({"provider_codes": re.findall(r"\[code: (\d+)\]", p.stdout + p.stderr)}), flush=True)
        raise SystemExit(p.returncode)
    return json.loads(p.stdout) if parse else p.stdout


def g(*args):
    return run([*G, *args, "--project", PROJECT, "--format=json", "--quiet"], "gcloud " + " ".join(args[:4]))


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


def normalized_container_invariants(container: dict) -> dict:
    return {
        "serviceAccountName": container.get("serviceAccountName"),
        "resources": container.get("resources", {}),
        "ports": container.get("ports", []),
        "volumeMounts": container.get("volumeMounts", []),
        "env_names": sorted(e.get("name") for e in container.get("env", [])),
        "env_value_hash": env_hash_from_container(container),
        "env_value_from_hash": digest([e for e in container.get("env", []) if "valueFrom" in e]),
    }

def normalized_container_without_env(container: dict) -> dict:
    return {
        "serviceAccountName": container.get("serviceAccountName"),
        "resources": container.get("resources", {}),
        "ports": container.get("ports", []),
        "volumeMounts": container.get("volumeMounts", []),
    }

def normalized_service_invariants(svc: dict) -> dict:
    template = svc["spec"]["template"]
    spec = template["spec"]
    meta = template.get("metadata", {})
    container = spec["containers"][0]
    return {
        "ingress": svc.get("metadata", {}).get("annotations", {}).get("run.googleapis.com/ingress"),
        "maxScale": meta.get("annotations", {}).get("autoscaling.knative.dev/maxScale"),
        "containerConcurrency": spec.get("containerConcurrency"),
        "timeoutSeconds": spec.get("timeoutSeconds"),
        "serviceAccountName": spec.get("serviceAccountName"),
        "volumes": spec.get("volumes", []),
        "vpcAccess": template.get("metadata", {}).get("annotations", {}).get("run.googleapis.com/vpc-access-connector"),
        "container": normalized_container_invariants(container),
    }

def normalized_service_without_env(svc: dict) -> dict:
    template = svc["spec"]["template"]
    spec = template["spec"]
    meta = template.get("metadata", {})
    container = spec["containers"][0]
    return {
        "ingress": svc.get("metadata", {}).get("annotations", {}).get("run.googleapis.com/ingress"),
        "maxScale": meta.get("annotations", {}).get("autoscaling.knative.dev/maxScale"),
        "containerConcurrency": spec.get("containerConcurrency"),
        "timeoutSeconds": spec.get("timeoutSeconds"),
        "serviceAccountName": spec.get("serviceAccountName"),
        "volumes": spec.get("volumes", []),
        "vpcAccess": template.get("metadata", {}).get("annotations", {}).get("run.googleapis.com/vpc-access-connector"),
        "container": normalized_container_without_env(container),
    }

def revision_runtime_hashes(container: dict) -> dict:
    return {
        "command": digest(container.get("command", [])),
        "args": digest(container.get("args", [])),
        "startupProbe": digest(container.get("startupProbe")),
        "env": env_hash_from_container(container),
    }


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
        "service_invariant_hash": digest(normalized_service_invariants(s)),
        "baseline_container_invariant_hash": digest(normalized_container_invariants(container)),
    }


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
    # gcloud has no --clear-command/--clear-args in this installation.
    # Empty strings are emitted deliberately and post-deploy revision assertions verify the reset.
    command = container.get("command", [])
    args_value = container.get("args", [])
    return ["--command", ",".join(command), "--args", ",".join(args_value)]


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


def assert_gateway_worker_hashes(baseline: dict) -> None:
    gw, cfg, spec = gateway()
    version = worker()
    assert gw["apiConfig"].endswith("/" + baseline["gateway_config"])
    assert digest(spec) == baseline["gateway_spec"]
    assert digest(cfg["gatewayServiceAccount"]) == baseline["gateway_identity"]
    assert version == baseline["worker_version"]
    assert digest(bindings(version)) == baseline["worker_bindings"]

def assert_control_plane_before_mutation(baseline: dict, *, require_old_traffic: bool = True) -> None:
    s = service()
    assert iam_hash() == baseline["iam"]
    assert digest(normalized_service_invariants(s)) == baseline["service_invariant_hash"]
    assert_gateway_worker_hashes(baseline)
    if require_old_traffic:
        assert_old_traffic(s, baseline)

def assert_baseline_revision_runtime(baseline: dict) -> None:
    container = container_from_revision(baseline["revision"])
    assert digest(normalized_container_invariants(container)) == baseline["baseline_container_invariant_hash"]
    assert revision_runtime_hashes(container) == {
        "command": baseline["container_command_hash"],
        "args": baseline["container_args_hash"],
        "startupProbe": baseline["startup_probe_hash"],
        "env": baseline["env_hash"],
    }

def assert_live_recovery_before_mutation(baseline: dict, expected_image: str) -> None:
    s = service()
    assert iam_hash() == baseline["iam"]
    assert_old_traffic(s, baseline)
    assert_gateway_worker_hashes(baseline)
    assert_baseline_revision_runtime(baseline)
    failure = json.loads(LIVE_FAILURE_STATE.read_text(encoding="utf-8"))
    failed_latest = s["status"]["latestCreatedRevisionName"]
    assert failed_latest == failure["latestCreated"]
    assert failed_latest != baseline["revision"]
    failed_container = container_from_revision(failed_latest)
    baseline_container = container_from_revision(baseline["revision"])
    assert failed_container["image"] == expected_image
    current_with_baseline_container = {
        **normalized_service_invariants(s),
        "container": normalized_container_invariants(baseline_container),
    }
    assert digest(current_with_baseline_container) == baseline["service_invariant_hash"]
    assert normalized_container_without_env(failed_container) == normalized_container_without_env(baseline_container)
    failed_runtime = revision_runtime_hashes(failed_container)
    assert failed_runtime["command"] == baseline["container_command_hash"]
    assert failed_runtime["args"] == baseline["container_args_hash"]
    assert failed_runtime["startupProbe"] == baseline["startup_probe_hash"]
    assert failed_runtime["env"] != baseline["env_hash"]

def assert_remote_manifest_chain(client: httpx.Client, api: str, tag: str, manifest: bytes, manifest_digest: str) -> None:
    r = client.head(api + "/manifests/" + tag, headers={"Accept": "application/vnd.oci.image.manifest.v1+json"})
    r.raise_for_status()
    assert r.headers.get("docker-content-digest") == manifest_digest
    r = client.get(api + "/manifests/" + tag, headers={"Accept": "application/vnd.oci.image.manifest.v1+json"})
    r.raise_for_status()
    assert "sha256:" + hashlib.sha256(r.content).hexdigest() == manifest_digest
    remote = r.json()
    local = json.loads(manifest)
    assert remote["config"]["digest"] == local["config"]["digest"]
    assert [layer["digest"] for layer in remote["layers"]] == [layer["digest"] for layer in local["layers"]]


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
    manifest_digest = sha_bytes(manifest)
    assert meta["image"].endswith("@" + manifest_digest), (meta["image"], manifest_digest)
    assert_control_plane_before_mutation(b)
    with httpx.Client(auth=("oauth2accesstoken", token), timeout=120, follow_redirects=False) as client:
        for data in [config, layer]:
            d = sha_bytes(data); r = client.head(api + "/blobs/" + d)
            if r.status_code != 200:
                assert r.status_code == 404, r.status_code
                r = client.post(api + "/blobs/uploads/"); r.raise_for_status(); loc = normalize_registry_upload_location(registry, r.headers["location"])
                r = client.put(loc + ("&" if "?" in loc else "?") + "digest=" + d, content=data, headers={"Content-Type":"application/octet-stream"})
                assert r.status_code in {201, 202}, r.status_code
            r = client.head(api + "/blobs/" + d)
            assert r.status_code == 200, r.status_code
        tag = "monthly-ux07-" + manifest_digest.split(":")[1][:12]
        r = client.put(api + "/manifests/" + tag, content=manifest, headers={"Content-Type":"application/vnd.oci.image.manifest.v1+json"}); r.raise_for_status(); assert r.headers.get("docker-content-digest") == manifest_digest
        assert_remote_manifest_chain(client, api, tag, manifest, manifest_digest)
    meta["pushed"] = True; meta["registry_tag"] = tag; meta["registry_digest_asserted"] = True
    (IMAGE_OUT / "build.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    save_new("push.json", {"image": meta["image"], "tag": tag, "digest_asserted": True, "same_registry_host": True})
elif phase == "stage":
    require_mutation(); b = read("baseline.json"); meta = image_meta(require_pushed=True); assert meta["source_freeze"] and source_freeze_hash() == b["source_freeze_sha256"]; assert_control_plane_before_mutation(b)
    g("run", "deploy", SERVICE, "--region", REGION, "--image", meta["image"], "--no-traffic", "--tag", "ux07-rp03", "--command", "python", "--args=-m,release_tools.rp03_startup_wrapper", "--startup-probe", "httpGet.path=/health,httpGet.port=8080,failureThreshold=60,periodSeconds=3,timeoutSeconds=1", "--update-env-vars", "DELIVERY_RUNTIME_VERIFY=false")
    s = service(); rev = s["status"]["latestCreatedRevisionName"]; v = revision(rev); cond = {c["type"]: c["status"] for c in v["status"]["conditions"]}
    assert cond.get("Ready") == "True" and cond.get("ContainerHealthy") == "True"; assert_old_traffic(s, b); assert iam_hash() == b["iam"]
    stage_container = container_from_revision(rev); assert stage_container["image"] == meta["image"]; assert digest(normalized_container_invariants(stage_container)) == b["baseline_container_invariant_hash"]
    save_new("stage.json", {"revision": rev, "image": meta["image"], "actual_revision_image": stage_container["image"], "conditions": cond, "rollback_revision": b["revision"], "traffic_unchanged": True, "temporary_command_wrapper": True, "source_freeze_sha256": b["source_freeze_sha256"], "container_invariants_preserved": True})
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
    require_mutation(); b = read("baseline.json"); st = read("stage.json"); proof = read("linux-rp03-runtime.json"); assert proof["revision"] == st["revision"]; assert proof["image"] == st["image"]; assert proof["source_freeze_sha256"] == b["source_freeze_sha256"]
    assert_live_recovery_before_mutation(b, st["image"])
    baseline_container = container_from_revision(b["revision"])
    deploy_args = ["run", "deploy", SERVICE, "--region", REGION, "--image", st["image"], "--no-traffic", "--tag", "ux07-live", *command_args(baseline_container), *startup_probe_arg(baseline_container), *env_restore_args(baseline_container)]
    g(*deploy_args)
    s = service(); rev = s["status"]["latestCreatedRevisionName"]; v = revision(rev); cond = {c["type"]: c["status"] for c in v["status"]["conditions"]}
    assert cond.get("Ready") == "True" and cond.get("ContainerHealthy") == "True"; assert_old_traffic(s, b); assert iam_hash() == b["iam"]; assert_revision_matches_baseline(rev, b)
    live_container = container_from_revision(rev); assert live_container["image"] == st["image"]; assert revision_runtime_hashes(live_container) == {"command": b["container_command_hash"], "args": b["container_args_hash"], "startupProbe": b["startup_probe_hash"], "env": b["env_hash"]}
    save_new("live.json", {"revision": rev, "image": st["image"], "actual_revision_image": live_container["image"], "verified_revision": st["revision"], "rollback_revision": b["revision"], "conditions": cond, "baseline_runtime_hashes_restored": True, "traffic_unchanged": True, "source_freeze_sha256": b["source_freeze_sha256"]})
elif phase == "traffic":
    require_mutation(); b = read("baseline.json"); live = read("live.json"); assert_control_plane_before_mutation(b); assert_live_ready_for_traffic(b, live)
    g("run", "services", "update-traffic", SERVICE, "--region", REGION, "--to-revisions", live["revision"] + "=100")
    remove_release_tags()
    s = service(); assert any(t.get("revisionName") == live["revision"] and t.get("percent") == 100 for t in s["status"].get("traffic", [])); assert iam_hash() == b["iam"]
    save_new("traffic.json", {"revision": live["revision"], "image": live["image"], "rollback_revision": b["revision"], "traffic_hash": digest(s["status"].get("traffic", [])), "temporary_tags_removed": True})
elif phase == "after":
    b = read("baseline.json"); live = read("live.json"); traffic = read("traffic.json"); assert traffic["revision"] == live["revision"]; s = service(); gw, cfg, spec = gateway(); version = worker()
    assert iam_hash() == b["iam"]; assert s["status"]["latestReadyRevisionName"] == live["revision"]; assert s["spec"]["template"]["spec"]["containers"][0]["image"] == live["image"]
    assert any(t.get("revisionName") == live["revision"] and t.get("percent") == 100 for t in s["status"].get("traffic", []))
    assert gw["apiConfig"].endswith("/" + b["gateway_config"]); assert digest(spec) == b["gateway_spec"]; assert digest(cfg["gatewayServiceAccount"]) == b["gateway_identity"]
    assert version == b["worker_version"] and digest(bindings(version)) == b["worker_bindings"]; assert_revision_matches_baseline(live["revision"], b); assert digest(normalized_service_invariants(s)) == b["service_invariant_hash"]
    save_new("after.json", {"revision": live["revision"], "image": live["image"], "worker_version": version, "gateway_config": b["gateway_config"], "security_invariants_preserved": True, "private_iam": True, "access": access(), "rollback_revision": b["revision"], "source_freeze_sha256": b["source_freeze_sha256"]})
else:
    raise SystemExit("phase: baseline | image | push | stage | proof | live | traffic | after")
