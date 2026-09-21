"""Build the guarded MONTHLY-01 API overlay image.

This is the RULES-01 image overlay flow with the bounded Monthly01 delta:
only ``apps/api/app/formula_patterns.py`` may differ from the proven base.
"""

from pathlib import Path
import argparse
import gzip
import hashlib
import io
import json
import shutil
import subprocess
import tarfile
from urllib.parse import urljoin, urlparse

import httpx

R = Path("C:/Users/JinwonLee/project/ExcelSaaS")
BASE = Path("C:/Users/JinwonLee/project/DigitalTwin/.tmp/workbookcare-horizontal01/image")
WORK = Path("C:/Users/JinwonLee/project/DigitalTwin/.tmp/workbookcare-monthly01")
O = WORK / "image"
O.mkdir(parents=True, exist_ok=True)
REG = "https://asia-northeast3-docker.pkg.dev"
REPO = "workbookcare-beta/workbookcare-images/workbookcare-api"
API = REG + "/v2/" + REPO
GC = (
    shutil.which("gcloud.cmd")
    or r"C:\Users\JinwonLee\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
)
CHANGED = {"apps/api/app/formula_patterns.py"}
PRESERVED_DIRTY = {"apps/api/engine/dependencies.lock.json"}
FREEZE = R / "artifacts/synthetic_validation/monthly01/integration/source-freeze.json"

parser = argparse.ArgumentParser()
parser.add_argument("--push", action="store_true")
parser.add_argument("--confirm-push", default="")
args = parser.parse_args()


def sha(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def file_sha(path: str) -> str:
    return sha((R / path).read_bytes())


baseline = json.loads((BASE / "build.json").read_text(encoding="utf-8"))
manifest_bytes = (BASE / "manifest.json").read_bytes()
assert baseline["image"].endswith("@" + sha(manifest_bytes)), baseline["image"]
manifest = json.loads(manifest_bytes)
config_bytes = (BASE / "config.json").read_bytes()
assert sha(config_bytes) == manifest["config"]["digest"]
freeze = json.loads(FREEZE.read_text(encoding="utf-8"))["sha256"]

for path, expected_hex in freeze.items():
    if path in PRESERVED_DIRTY:
        continue
    assert hashlib.sha256((R / path).read_bytes()).hexdigest() == expected_hex, path

source_sha = dict(baseline["source_sha256"])
for path, digest in baseline["source_sha256"].items():
    if path in CHANGED or path in PRESERVED_DIRTY:
        continue
    assert file_sha(path) == digest, path

for path in CHANGED:
    current = file_sha(path)
    assert current != baseline["source_sha256"][path], path
    assert freeze[path] == current.removeprefix("sha256:"), path
    source_sha[path] = current

assert sorted(CHANGED) == ["apps/api/app/formula_patterns.py"]

tar_bytes = io.BytesIO()
with tarfile.open(fileobj=tar_bytes, mode="w") as tar:
    for path in sorted(CHANGED):
        data = (R / path).read_bytes()
        entry = tarfile.TarInfo("app/" + Path(path).relative_to("apps/api").as_posix())
        entry.size = len(data)
        entry.mode = 0o644
        entry.mtime = 0
        tar.addfile(entry, io.BytesIO(data))
raw_layer = tar_bytes.getvalue()
layer = gzip.compress(raw_layer, mtime=0)
(O / "registry-layer.tar.gz").write_bytes(layer)

config = json.loads(config_bytes)
config["rootfs"]["diff_ids"].append(sha(raw_layer))
config["history"].append(
    {
        "created": "2026-09-21T00:00:00Z",
        "created_by": "Approved MONTHLY-01 formula pattern overlay",
    }
)
new_config = json.dumps(config, separators=(",", ":")).encode("utf-8")
(O / "config.json").write_bytes(new_config)
manifest["config"].update(digest=sha(new_config), size=len(new_config))
manifest["layers"].append(
    {
        "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
        "digest": sha(layer),
        "size": len(layer),
    }
)
new_manifest = json.dumps(manifest, separators=(",", ":")).encode("utf-8")
(O / "manifest.json").write_bytes(new_manifest)

result = {
    "image": REG.removeprefix("https://") + "/" + REPO + "@" + sha(new_manifest),
    "base_image": baseline["image"],
    "source_sha256": source_sha,
    "changed_sources": sorted(CHANGED),
    "preserved_dirty_exception": sorted(PRESERVED_DIRTY),
    "source_freeze": str(FREEZE),
    "java": baseline["java"],
    "wheels": baseline["wheels"],
    "layer_bytes": len(layer),
    "pushed": False,
    "build": "MONTHLY-01 formula_patterns.py overlay on immutable RULES-01 private beta image",
}

if args.push:
    if args.confirm_push != "MONTHLY01_APPROVED_PUSH":
        raise SystemExit("Refusing registry mutation without --confirm-push MONTHLY01_APPROVED_PUSH")
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
            API + "/manifests/monthly01-" + sha(new_manifest).split(":")[1][:12],
            content=new_manifest,
            headers={"Content-Type": manifest["mediaType"]},
        )
        response.raise_for_status()
        assert response.headers.get("docker-content-digest") == sha(new_manifest)
    result["pushed"] = True

(O / "build.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"image": result["image"], "pushed": result["pushed"], "layer_bytes": len(layer)}))
