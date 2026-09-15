import base64, copy, hashlib, json, os, re, subprocess, sys, tempfile
from pathlib import Path
from urllib.parse import urlparse
import httpx, yaml

R = Path("C:/Users/JinwonLee/project/ExcelSaaS")
O = Path("C:/Users/JinwonLee/project/DigitalTwin/.tmp/workbookcare-flow01/release")
O.mkdir(parents=True, exist_ok=True)
G = r"C:\Users\JinwonLee\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
PROJECT = "workbookcare-beta"
SERVICE = "workbookcare-api-beta"
REGION = "asia-northeast3"
API = "workbookcare-beta-api"
GW = "workbookcare-beta-gateway"
LOC = "asia-northeast1"
FLAGS = {"DELIVERY_RUNTIME_VERIFY"}
phase = sys.argv[1]
env = {
    **os.environ,
    "CLOUDSDK_CORE_DISABLE_PROMPTS": "1",
    "WRANGLER_SEND_METRICS": "false",
    "CI": "1",
}


def save(name, v):
    (O / name).write_text(json.dumps(v, indent=2) + "\n", encoding="utf-8")


def read(name):
    return json.loads((O / name).read_text())


def sha(v):
    return hashlib.sha256(json.dumps(v, sort_keys=True).encode()).hexdigest()


def run(argv, label, parse=False, extra=None):
    p = subprocess.run(
        argv,
        cwd=R,
        env=extra or env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    entry = {"phase": phase, "command": label, "exit_code": p.returncode}
    with (O / "commands.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    print(json.dumps(entry), flush=True)
    if p.returncode:
        print(
            json.dumps(
                {
                    "provider_codes": re.findall(
                        r"\[code: (\d+)\]", p.stdout + p.stderr
                    ),
                    "auth_error": bool(
                        re.search(
                            r"unauthenticated|permission.denied",
                            p.stdout + p.stderr,
                            re.I,
                        )
                    ),
                }
            ),
            flush=True,
        )
        raise SystemExit(p.returncode)
    return json.loads(p.stdout) if parse else p.stdout


def g(*a):
    return run(
        [G, *a, "--project", PROJECT, "--format=json", "--quiet"],
        "gcloud " + " ".join(a[:4]),
        True,
    )


def w(*a, parse=False):
    return run(
        [
            "npx.cmd",
            "--offline",
            "--no-install",
            "wrangler",
            *a,
            "--config",
            "infra/cloudflare/wrangler.jsonc",
        ],
        "wrangler " + " ".join(a[:3]),
        parse,
    )


def service():
    return g("run", "services", "describe", SERVICE, "--region", REGION)


def iam():
    data = g("run", "services", "get-iam-policy", SERVICE, "--region", REGION)
    assert not any(
        m in {"allUsers", "allAuthenticatedUsers"}
        for b in data.get("bindings", [])
        for m in b.get("members", [])
    )
    return sha(data)


def invariant(s):
    assert s["spec"]["template"]["metadata"]["annotations"]["autoscaling.knative.dev/maxScale"] == "1"
    spec = copy.deepcopy(s["spec"]["template"]["spec"])
    c = spec["containers"][0]
    c.pop("image")
    assert c["startupProbe"]["failureThreshold"] in {3, 40}
    c["startupProbe"]["failureThreshold"] = (
        3  # Approved runtime warm-up budget; every other probe field retained.
    )
    c["env"] = sorted(
        [e for e in c.get("env", []) if e["name"] not in FLAGS], key=lambda e: e["name"]
    )
    a = {
        k: v
        for k, v in s["spec"]["template"]["metadata"].get("annotations", {}).items()
        if not k.startswith("run.googleapis.com/client-")
        and k != "autoscaling.knative.dev/maxScale"
    }
    m = {
        k: v
        for k, v in s["metadata"].get("annotations", {}).items()
        if k
        in [
            "run.googleapis.com/ingress",
            "run.googleapis.com/invoker-iam-disabled",
            "run.googleapis.com/default-url-disabled",
        ]
    }
    return sha({"spec": spec, "annotations": a, "metadata": m})


def gateway():
    gw = g("api-gateway", "gateways", "describe", GW, "--location", LOC)
    cfg = g(
        "api-gateway",
        "api-configs",
        "describe",
        gw["apiConfig"].split("/")[-1],
        "--api",
        API,
        "--view=FULL",
    )
    spec = yaml.safe_load(
        base64.b64decode(cfg["openapiDocuments"][0]["document"]["contents"])
    )
    return gw, cfg, spec


def current_worker():
    data = w("deployments", "list", "--json", parse=True)
    if isinstance(data, dict):
        data = data["deployments"]
    versions = max(data, key=lambda x: x["created_on"])["versions"]
    assert len(versions) == 1 and versions[0]["percentage"] == 100
    return versions[0]["version_id"]


def bindings(version):
    return w("versions", "view", version, "--json", parse=True)["resources"]["bindings"]


def access():
    result = []
    for path in ["/", "/api/v1/scans", "/api/v1/formula-audits", "/api/v1/delivery"]:
        res = httpx.get(
            "https://workbookcare-beta.wonderlogic-studio.workers.dev" + path,
            follow_redirects=False,
            timeout=30,
        )
        result.append(
            {
                "path": path,
                "status": res.status_code,
                "existing_access": urlparse(res.headers.get("location", "")).hostname
                == "old-breeze-11c7.cloudflareaccess.com",
            }
        )
    assert all(r["status"] == 302 and r["existing_access"] for r in result)
    return result


if phase == "baseline":
    assert not (O / "baseline.json").exists()
    s = service()
    gw, cfg, spec = gateway()
    v = current_worker()
    assert s["status"]["latestReadyRevisionName"] == "workbookcare-api-beta-00014-nah"
    assert v == "1fa2992b-c75d-400b-8acc-14dd484c7a40"
    assert gw["apiConfig"].endswith("/workbookcare-beta-d08-e6132fcdf496")
    assert any(
        t.get("revisionName") == "workbookcare-api-beta-00014-nah"
        and t.get("percent") == 100
        for t in s["status"]["traffic"]
    )
    save(
        "baseline.json",
        {
            "revision": s["status"]["latestReadyRevisionName"],
            "image": s["spec"]["template"]["spec"]["containers"][0]["image"],
            "invariant": invariant(s),
            "iam": iam(),
            "max_instances": s["spec"]["template"]["metadata"]["annotations"][
                "autoscaling.knative.dev/maxScale"
            ],
            "gateway_config": gw["apiConfig"].split("/")[-1],
            "gateway_spec": sha(spec),
            "gateway_identity": sha(cfg["gatewayServiceAccount"]),
            "worker_version": v,
            "worker_bindings": sha(bindings(v)),
            "access": access(),
        },
    )
elif phase == "stage":
    b = read("baseline.json")
    s = service()
    assert invariant(s) == b["invariant"] and iam() == b["iam"]
    assert any(
        t.get("revisionName") == b["revision"] and t.get("percent") == 100
        for t in s["status"]["traffic"]
    )
    image = json.loads((O.parent / "image/build.json").read_text())
    assert image["pushed"]
    assert image["base_image"] == b["image"]
    for path, digest in image["source_sha256"].items():
        assert (
            "sha256:" + hashlib.sha256((R / path).read_bytes()).hexdigest() == digest
        ), path
    g(
        "run",
        "deploy",
        SERVICE,
        "--region",
        REGION,
        "--image",
        image["image"],
        "--no-traffic",
        "--tag",
        "flow01",
        "--startup-probe",
        "httpGet.path=/health,httpGet.port=8080,failureThreshold=40,periodSeconds=3,timeoutSeconds=1",
        "--update-env-vars",
        "DELIVERY_RUNTIME_VERIFY=true",
    )
    s = service()
    rev = s["status"]["latestCreatedRevisionName"]
    v = g("run", "revisions", "describe", rev, "--region", REGION)
    conditions = {c["type"]: c["status"] for c in v["status"]["conditions"]}
    save(
        "stage.json",
        {
            "revision": rev,
            "conditions": conditions,
            "image": image["image"],
            "rollback_revision": b["revision"],
        },
    )
    assert (
        conditions.get("Ready") == "True"
        and conditions.get("ContainerHealthy") == "True"
    )
    assert invariant(s) == b["invariant"] and iam() == b["iam"]
    assert any(
        t.get("revisionName") == b["revision"] and t.get("percent") == 100
        for t in s["status"]["traffic"]
    )
elif phase == "proof":
    target = read("stage.json")
    logs = g(
        "logging",
        "read",
        f'resource.type="cloud_run_revision" AND resource.labels.revision_name="{target["revision"]}" AND jsonPayload.event="delivery_runtime_verified"',
        "--limit",
        "5",
    )
    proof = [
        {
            k: e["jsonPayload"][k]
            for k in ["event", "reference_cases", "repair_profiles", "artifacts"]
        }
        for e in logs
        if e.get("jsonPayload", {}).get("event") == "delivery_runtime_verified"
    ]
    assert proof
    assert all(
        x["reference_cases"] == 20 and x["repair_profiles"] == 2 and x["artifacts"] == 6
        for x in proof
    )
    save(
        "linux-runtime.json",
        {"revision": target["revision"], "checks": proof, "payment_tested": False},
    )
elif phase == "live":
    b = read("baseline.json")
    tested = read("stage.json")
    assert read("linux-runtime.json")["revision"] == tested["revision"]
    s = service()
    assert invariant(s) == b["invariant"] and iam() == b["iam"]
    assert any(
        t.get("revisionName") == b["revision"] and t.get("percent") == 100
        for t in s["status"]["traffic"]
    )
    g(
        "run",
        "deploy",
        SERVICE,
        "--region",
        REGION,
        "--image",
        tested["image"],
        "--no-traffic",
        "--tag",
        "flow01",
        "--startup-probe",
        "httpGet.path=/health,httpGet.port=8080,failureThreshold=3,periodSeconds=3,timeoutSeconds=1",
        "--update-env-vars",
        "DELIVERY_RUNTIME_VERIFY=false",
    )
    s = service()
    rev = s["status"]["latestCreatedRevisionName"]
    v = g("run", "revisions", "describe", rev, "--region", REGION)
    conditions = {c["type"]: c["status"] for c in v["status"]["conditions"]}
    assert (
        conditions.get("Ready") == "True"
        and conditions.get("ContainerHealthy") == "True"
    )
    assert invariant(s) == b["invariant"] and iam() == b["iam"]
    save(
        "live.json",
        {
            "revision": rev,
            "image": tested["image"],
            "verified_image_revision": tested["revision"],
            "conditions": conditions,
            "rollback_revision": b["revision"],
            "startup_budget_seconds": 9,
        },
    )
    g(
        "run",
        "services",
        "update-traffic",
        SERVICE,
        "--region",
        REGION,
        "--to-revisions",
        rev + "=100",
        "--remove-tags",
        "flow01",
    )
elif phase == "after":
    b = read("baseline.json")
    s = service()
    gw, cfg, spec = gateway()
    v = current_worker()
    assert invariant(s) == b["invariant"] and iam() == b["iam"]
    assert (
        s["spec"]["template"]["metadata"]["annotations"][
            "autoscaling.knative.dev/maxScale"
        ]
        == b["max_instances"]
        == "1"
    )
    assert any(
        t.get("revisionName") == read("live.json")["revision"]
        and t.get("percent") == 100
        for t in s["status"]["traffic"]
    )
    assert (
        gw["state"] == "ACTIVE"
        and gw["apiConfig"].endswith("/" + b["gateway_config"])
        and sha(spec) == b["gateway_spec"]
        and sha(cfg["gatewayServiceAccount"]) == b["gateway_identity"]
    )
    assert v == b["worker_version"] and sha(bindings(v)) == b["worker_bindings"]
    save(
        "after.json",
        {
            "revision": read("live.json")["revision"],
            "worker_version": v,
            "gateway_config": b["gateway_config"],
            "security_invariants_preserved": True,
            "private_iam": True,
            "max_instances": 1,
            "payment_mode": "OFF",
            "access": access(),
        },
    )
else:
    raise SystemExit("Unknown bounded complex release phase")
