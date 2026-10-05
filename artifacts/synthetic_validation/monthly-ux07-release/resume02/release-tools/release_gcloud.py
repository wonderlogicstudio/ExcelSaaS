from __future__ import annotations

import os
from pathlib import Path

CLOUD_SDK_ROOT = Path(r"C:\Users\JinwonLee\AppData\Local\Google\Cloud SDK\google-cloud-sdk")
GCLOUD_PYTHON = CLOUD_SDK_ROOT / "platform" / "bundledpython" / "python.exe"
GCLOUD_PY = CLOUD_SDK_ROOT / "lib" / "gcloud.py"


def gcloud_entrypoint() -> list[str]:
    if not GCLOUD_PYTHON.is_file():
        raise SystemExit(f"Missing bundled gcloud Python: {GCLOUD_PYTHON}")
    if not GCLOUD_PY.is_file():
        raise SystemExit(f"Missing gcloud.py: {GCLOUD_PY}")
    return [str(GCLOUD_PYTHON), "-S", str(GCLOUD_PY)]


def gcloud_env(base_env: dict[str, str]) -> dict[str, str]:
    env = dict(base_env)
    env["CLOUDSDK_ROOT_DIR"] = str(CLOUD_SDK_ROOT)
    sdk_bin = str(CLOUD_SDK_ROOT / "bin" / "sdk")
    env["PATH"] = sdk_bin + os.pathsep + env.get("PATH", "")
    return env


def delimited_gcloud_arg(values: dict[str, str]) -> str:
    delimiter = "@"
    if any(delimiter in k or delimiter in v for k, v in values.items()):
        delimiter = "|"
    if any(delimiter in k or delimiter in v for k, v in values.items()):
        raise SystemExit("Baseline env contains unsupported delimiter for gcloud argument construction")
    return f"^{delimiter}^" + delimiter.join(f"{k}={v}" for k, v in sorted(values.items()))


def env_restore_args(container: dict) -> list[str]:
    literal: dict[str, str] = {}
    secrets: dict[str, str] = {}
    for item in container.get("env", []):
        name = item["name"]
        if "value" in item:
            literal[name] = item.get("value", "")
            continue
        ref = item.get("valueFrom", {}).get("secretKeyRef")
        if not ref:
            raise SystemExit(f"Unsupported env valueFrom shape for {name}")
        secrets[name] = f"{ref['name']}:{ref.get('key', 'latest')}"
    args: list[str] = []
    if literal:
        args += ["--set-env-vars", delimited_gcloud_arg(literal)]
    else:
        args += ["--clear-env-vars"]
    if secrets:
        args += ["--set-secrets", delimited_gcloud_arg(secrets)]
    else:
        args += ["--clear-secrets"]
    return args
