from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import tarfile
from pathlib import Path

from release_config import BASE_IMAGE_DIR, IMAGE_OUT, REPO, SOURCE_FREEZE, image_path_for

REGISTRY = "asia-northeast3-docker.pkg.dev"
REPO_NAME = "workbookcare-beta/workbookcare-images/workbookcare-api"


def sha(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()

parser = argparse.ArgumentParser(description="Build a local, non-pushed MONTHLY-UX07 OCI overlay package.")
parser.add_argument("--base-dir", type=Path, default=BASE_IMAGE_DIR)
parser.add_argument("--out", type=Path, default=IMAGE_OUT)
args = parser.parse_args()
base = args.base_dir
out = args.out
out.mkdir(parents=True, exist_ok=True)
freeze = json.loads(SOURCE_FREEZE.read_text(encoding="utf-8"))
baseline = json.loads((base / "build.json").read_text(encoding="utf-8"))
manifest_bytes = (base / "manifest.json").read_bytes()
config_bytes = (base / "config.json").read_bytes()
manifest = json.loads(manifest_bytes)
assert baseline["image"].endswith("@" + sha(manifest_bytes)), baseline["image"]
assert baseline["image"] == freeze["live_base"]["image"], (baseline["image"], freeze["live_base"]["image"])
assert sha(config_bytes) == manifest["config"]["digest"]

tar_bytes = io.BytesIO()
previous = json.loads((out / "build.json").read_text(encoding="utf-8")) if (out / "build.json").exists() else None
with tarfile.open(fileobj=tar_bytes, mode="w") as tar:
    for item in freeze["overlay"]:
        source = REPO / item["repo_path"]
        data = source.read_bytes()
        assert hashlib.sha256(data).hexdigest() == item["sha256"], item["repo_path"]
        entry = tarfile.TarInfo(item["image_path"])
        entry.size = len(data)
        entry.mode = 0o644
        entry.mtime = 0
        tar.addfile(entry, io.BytesIO(data))
    manifest_data = SOURCE_FREEZE.read_bytes()
    entry = tarfile.TarInfo("app/verification/monthly-ux07-source-freeze.json")
    entry.size = len(manifest_data)
    entry.mode = 0o644
    entry.mtime = 0
    tar.addfile(entry, io.BytesIO(manifest_data))
raw_layer = tar_bytes.getvalue()
layer = gzip.compress(raw_layer, mtime=0)
(out / "registry-layer.tar.gz").write_bytes(layer)
config = json.loads(config_bytes)
config["rootfs"]["diff_ids"].append(sha(raw_layer))
config["history"].append({"created": "2026-09-23T00:00:00Z", "created_by": "MONTHLY-UX07 RP03 API overlay; local build only"})
new_config = json.dumps(config, separators=(",", ":")).encode("utf-8")
(out / "config.json").write_bytes(new_config)
manifest["config"].update(digest=sha(new_config), size=len(new_config))
manifest["layers"].append({"mediaType": "application/vnd.oci.image.layer.v1.tar+gzip", "digest": sha(layer), "size": len(layer)})
new_manifest = json.dumps(manifest, separators=(",", ":")).encode("utf-8")
(out / "manifest.json").write_bytes(new_manifest)
result = {
    "image": REGISTRY + "/" + REPO_NAME + "@" + sha(new_manifest),
    "base_image": baseline["image"],
    "overlay_count": len(freeze["overlay"]),
    "overlay": freeze["overlay"],
    "layer_bytes": len(layer),
    "pushed": False,
    "network_mutation": False,
    "source_freeze": str(SOURCE_FREEZE),
    "packaged_source_freeze": "app/verification/monthly-ux07-source-freeze.json",
    "supersedes_image": previous["image"] if previous else None,
}
(out / "build.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"image": result["image"], "pushed": False, "overlay_count": result["overlay_count"]}, ensure_ascii=False))
