from __future__ import annotations

import os
from pathlib import Path

import pytest

from release_gcloud import delimited_gcloud_arg, env_restore_args, gcloud_entrypoint, gcloud_env


def test_gcloud_entrypoint_uses_python_script_not_cmd_wrapper():
    argv = gcloud_entrypoint()
    assert argv[0].endswith("python.exe")
    assert argv[1] == "-S"
    assert argv[2].endswith("gcloud.py")
    assert not any(part.endswith("gcloud.cmd") for part in argv)


def test_gcloud_env_sets_cloudsdk_root_and_sdk_path():
    env = gcloud_env({"PATH": "base"})
    assert Path(env["CLOUDSDK_ROOT_DIR"]).name == "google-cloud-sdk"
    assert env["PATH"].split(os.pathsep)[0].endswith(str(Path("bin") / "sdk"))


def test_env_restore_args_preserve_literal_and_secret_shapes_without_cmd_escaping_loss():
    container = {
        "env": [
            {"name": "BETA_FLAG", "value": "false"},
            {"name": "API_HOST", "value": "https://example.test"},
            {"name": "TOKEN", "valueFrom": {"secretKeyRef": {"name": "token-secret", "key": "latest"}}},
        ]
    }
    args = env_restore_args(container)
    assert args[:2] == ["--set-env-vars", "^@^API_HOST=https://example.test@BETA_FLAG=false"]
    assert args[2:] == ["--set-secrets", "^@^TOKEN=token-secret:latest"]


def test_env_restore_args_switches_delimiter_and_rejects_ambiguous_values():
    assert delimited_gcloud_arg({"A": "one@two"}) == "^|^A=one@two"
    with pytest.raises(SystemExit):
        delimited_gcloud_arg({"A": "one@two|three"})
