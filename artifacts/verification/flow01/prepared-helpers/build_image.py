"""Overlay only verified synthetic registries on the already tested private beta image."""

from pathlib import Path
import argparse, base64, gzip, hashlib, io, json, os, shutil, subprocess, tarfile
from urllib.parse import urljoin, urlparse
import httpx

R = Path("C:/Users/JinwonLee/project/ExcelSaaS")
BASE = R / "artifacts/verification/d08-complex/image"
O = Path("C:/Users/JinwonLee/project/DigitalTwin/.tmp/workbookcare-flow01/image")
O.mkdir(parents=True, exist_ok=True)
REG = "https://asia-northeast3-docker.pkg.dev"
REPO = "workbookcare-beta/workbookcare-images/workbookcare-api"
API = REG + "/v2/" + REPO
GC = (
    shutil.which("gcloud.cmd")
    or r"C:\Users\JinwonLee\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
)
parser = argparse.ArgumentParser()
parser.add_argument("--push", action="store_true")
args = parser.parse_args()


def sha(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


import sys
sys.path.insert(0, str(R / "apps/api"))
from app.delivery_execution import compatibility_status, patch_fingerprint
proof = json.loads((O.parent / "excel-bound-evidence.json").read_text(encoding="utf-8"))
assert proof["status"] == "PASS" and proof["patch_fingerprint"] == patch_fingerprint()
assert compatibility_status()["status"] == "PASS"
baseline = json.loads((BASE / "build.json").read_text())
manifest_bytes = (BASE / "manifest.json").read_bytes()
assert baseline["image"].endswith("@" + sha(manifest_bytes))
assert (
    sha(manifest_bytes)
    == "sha256:12edb4bea80533d20ddd59fe6cb71fb0749320422ee3f04b78de5ed182acecc2"
)
manifest = json.loads(manifest_bytes)
config_bytes = (BASE / "config.json").read_bytes()
assert sha(config_bytes) == manifest["config"]["digest"]
changed = {
    "apps/api/app/delivery_patch.py",
    "apps/api/app/delivery_artifacts.py",
    "apps/api/app/delivery_verification_template.html",
    "apps/api/app/delivery_patch_reference.json",
}
for path, digest in baseline["source_sha256"].items():
    if path not in changed:
        assert sha((R / path).read_bytes()) == digest, path
tar_bytes = io.BytesIO()
source_sha = dict(baseline["source_sha256"])
with tarfile.open(fileobj=tar_bytes, mode="w") as tar:
    for path in sorted(changed):
        data = (R / path).read_bytes()
        source_sha[path] = sha(data)
        entry = tarfile.TarInfo("app/app/" + Path(path).name)
        entry.size = len(data)
        entry.mode = 0o644
        entry.mtime = 0
        tar.addfile(entry, io.BytesIO(data))
layer = gzip.compress(tar_bytes.getvalue(), mtime=0)
(O / "registry-layer.tar.gz").write_bytes(layer)
config = json.loads(config_bytes)
config["rootfs"]["diff_ids"].append(sha(tar_bytes.getvalue()))
config["history"].append(
    {
        "created": "2026-09-15T00:00:00Z",
        "created_by": "Approved FLOW-01 same-detector revalidation",
    }
)
new_config = json.dumps(config, separators=(",", ":")).encode()
(O / "config.json").write_bytes(new_config)
manifest["config"].update(digest=sha(new_config), size=len(new_config))
manifest["layers"].append(
    {
        "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
        "digest": sha(layer),
        "size": len(layer),
    }
)
new_manifest = json.dumps(manifest, separators=(",", ":")).encode()
(O / "manifest.json").write_bytes(new_manifest)
result = {
    "image": REG.removeprefix("https://") + "/" + REPO + "@" + sha(new_manifest),
    "base_image": baseline["image"],
    "source_sha256": source_sha,
    "changed_sources": sorted(changed),
    "java": baseline["java"],
    "wheels": baseline["wheels"],
    "layer_bytes": len(layer),
    "pushed": False,
    "build": "FLOW-01 verified revalidation overlay on immutable private beta image",
}
if args.push:
    token = subprocess.run(
        [GC, "auth", "print-access-token"], capture_output=True, text=True, check=True
    ).stdout.strip()
    with httpx.Client(
        auth=("oauth2accesstoken", token), timeout=120, follow_redirects=False
    ) as client:
        for data in [new_config, layer]:
            digest = sha(data)
            response = client.head(API + "/blobs/" + digest)
            if response.status_code == 200:
                continue
            assert response.status_code == 404, response.status_code
            response = client.post(API + "/blobs/uploads/")
            response.raise_for_status()
            loc = urljoin(REG, response.headers["location"])
            assert urlparse(loc).hostname == urlparse(REG).hostname
            response = client.put(
                loc + ("&" if "?" in loc else "?") + "digest=" + digest,
                content=data,
                headers={"Content-Type": "application/octet-stream"},
            )
            assert response.status_code in {201, 202}, response.status_code
        response = client.put(
            API + "/manifests/flow01-" + sha(new_manifest).split(":")[1][:12],
            content=new_manifest,
            headers={"Content-Type": manifest["mediaType"]},
        )
        response.raise_for_status()
        assert response.headers.get("docker-content-digest") == sha(new_manifest)
    result["pushed"] = True
(O / "build.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(
    json.dumps(
        {
            "image": result["image"],
            "pushed": result["pushed"],
            "layer_bytes": len(layer),
        }
    )
)
