"""Local Docker rehearsal only. Uses synthetic bytes; never invokes cloud tools."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import subprocess
import sys
import time
import warnings
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4
from zipfile import ZIP_STORED, ZipFile

from openpyxl import Workbook
from openpyxl.workbook.defined_name import DefinedName

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

PRIVATE = "SYNTHETIC_PRIVATE"
CONTROL_PLANE_TEST_SECRET = "synthetic-container-control-plane-secret-at-least-32-characters"


def docker(*args: str) -> str:
    result = subprocess.run(
        ["docker", *args], check=True, capture_output=True, text=True, encoding="utf-8",
    )
    return result.stdout.strip()


def request(base: str, path: str, payload: bytes | None = None,
            filename: str = f"{PRIVATE}_filename.xlsx") -> tuple[int, dict]:
    headers = {}
    if payload is not None:
        boundary = "workbookcare-synthetic-boundary"
        payload = (
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
            f'filename="{filename}"\r\nContent-Type: application/octet-stream\r\n\r\n'
        ).encode() + payload + f"\r\n--{boundary}--\r\n".encode()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        if path in {"/v1/scans", "/v1/formula-audits"}:
            timestamp = str(int(time.time()))
            body_hash = hashlib.sha256(payload).hexdigest()
            canonical = f"v1\n{timestamp}\nPOST\n{path}\n{body_hash}".encode("ascii")
            signature = hmac.new(
                CONTROL_PLANE_TEST_SECRET.encode("utf-8"), canonical, hashlib.sha256
            ).hexdigest()
            headers["X-WorkbookCare-Timestamp"] = timestamp
            headers["X-WorkbookCare-Signature"] = f"v1={signature}"
    try:
        response = urlopen(Request(base + path, data=payload, headers=headers), timeout=30)
    except HTTPError as exc:
        response = exc
    with response:
        return response.status, json.load(response)


def wait_ready(base: str) -> None:
    deadline = time.monotonic() + 40
    while time.monotonic() < deadline:
        try:
            if request(base, "/health/ready")[0] == 200:
                return
        except (URLError, ConnectionError, TimeoutError):
            pass
        time.sleep(0.25)
    raise AssertionError("container readiness timeout")


def assert_no_temporary_uploads(name: str) -> None:
    # Directory listing alone misses still-open, unlinked Linux temporary files.
    code = (
        "import os,pathlib,stat; p=pathlib.Path(os.environ['TMPDIR']); "
        "assert os.getuid()!=0; assert stat.S_IMODE(p.stat().st_mode)==0o700; "
        "assert not list(p.iterdir()); "
        "targets=[os.readlink(f) for f in pathlib.Path('/proc/1/fd').iterdir()]; "
        "assert not any(t.startswith(str(p)) for t in targets); "
        "assert not pathlib.Path('/app/.env').exists(); "
        "assert not pathlib.Path('/app/tests').exists()"
    )
    docker("exec", name, "python", "-c", code)


def synthetic_warning_workbook() -> bytes:
    workbook = Workbook()
    workbook.active.title = f"{PRIVATE}_sheet"
    workbook.active["A1"] = f"{PRIVATE}_value"
    workbook.active["A2"] = f'="{PRIVATE}_formula"'
    workbook.defined_names.add(DefinedName(
        "_xlnm.Print_Area", localSheetId=0, attr_text=f"{PRIVATE}_print_area",
    ))
    output = BytesIO()
    workbook.save(output)
    workbook.close()
    # Exceed Starlette's spool threshold without a high-compression ZIP member.
    with ZipFile(output, "a") as archive:
        archive.writestr("synthetic-padding.bin", b"x" * (2 * 1024 * 1024), ZIP_STORED)
    return output.getvalue()


def normalized(result: dict) -> dict:
    result = {
        key: value for key, value in result.items() if key not in {"analysis_id", "scanned_at"}
    }
    if "findings" in result:
        result["findings"] = [
            {key: value for key, value in finding.items() if key != "id"}
            for finding in result["findings"]
        ]
    return result


def rehearse(image: str, port: int, *, inject_failure: bool = False) -> dict:
    name = f"workbookcare-prep-{uuid4().hex[:12]}"
    args = [
        "run", "-d", "--name", name, "--memory=1g", "--cpus=1",
        "--cap-drop=ALL", "--security-opt=no-new-privileges:true",
        "--health-interval=1s", "--health-start-period=1s",
        "-p", f"127.0.0.1::{port}",
        "-e", "APP_ENV=hosted_beta", "-e", "CORS_ORIGINS=https://beta.example.invalid",
        "-e", "AI_EXPLANATIONS_ENABLED=false", "-e", "FORMULA_PATTERN_AUDIT_ENABLED=false",
        "-e", f"WORKBOOKCARE_CONTROL_PLANE_HMAC_SECRET={CONTROL_PLANE_TEST_SECRET}",
    ]
    if port != 8080:
        args += ["-e", f"PORT={port}"]
    args.append(image)
    if inject_failure:
        # Ephemeral in-memory fault injection; no product endpoint or image change.
        args += ["python", "-c", (
            "from app import main,runtime\n"
            "def fail(*args):\n"
            f"    raise RuntimeError('{PRIVATE}_exception')\n"
            "main.scan_workbook=fail\n"
            "runtime.main()\n"
        )]
    docker(*args)
    try:
        binding = docker("port", name, f"{port}/tcp")
        base = f"http://{binding}"
        wait_ready(base)
        for path, status in [("/health", "ok"), ("/health/live", "live"),
                             ("/health/ready", "ready")]:
            code, result = request(base, path)
            assert code == 200 and result["status"] == status
        assert_no_temporary_uploads(name)

        payload = synthetic_warning_workbook()
        if inject_failure:
            code, result = request(base, "/v1/scans", payload)
            assert code == 500 and result["error"]["code"] == "INTERNAL_ERROR"
            assert PRIVATE not in json.dumps(result)
            assert_no_temporary_uploads(name)
        else:
            from app.config import Settings
            from app.recommendation_engine import enrich_scan_result
            from app.scanner import scan_workbook

            for content in [(ROOT / "samples/demo-risky-workbook.xlsx").read_bytes(), payload]:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    expected = enrich_scan_result(scan_workbook(
                        f"{PRIVATE}_filename.xlsx", content, Settings(_env_file=None),
                    )).model_dump(mode="json")
                code, result = request(base, "/v1/scans", content)
                assert code == 200 and normalized(result) == normalized(expected)
                assert_no_temporary_uploads(name)

            for endpoint, content, filename, status, error in [
                ("/v1/scans", payload, f"{PRIVATE}.txt", 415, "UNSUPPORTED_FILE_TYPE"),
                ("/v1/scans", b"x" * (10 * 1024 * 1024 + 1), f"{PRIVATE}.xlsx", 413,
                 "FILE_TOO_LARGE"),
                ("/v1/scans", b"not a zip", f"{PRIVATE}.xlsx", 415, "INVALID_OOXML"),
                ("/v1/formula-audits", payload, f"{PRIVATE}.xlsx", 404,
                 "FORMULA_AUDIT_NOT_AVAILABLE"),
            ]:
                code, result = request(base, endpoint, content, filename)
                assert code == status, (code, status)
                assert result["error"]["code"] == error
                assert_no_temporary_uploads(name)

        assert request(base, f"/health?filename={PRIVATE}_query")[0] == 200
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if docker("inspect", "-f", "{{.State.Health.Status}}", name) == "healthy":
                break
            time.sleep(0.25)
        else:
            raise AssertionError("Docker HEALTHCHECK did not become healthy")

        docker("stop", "--time", "10", name)
        assert docker("inspect", "-f", "{{.State.ExitCode}}", name) == "0"
        logs = subprocess.run(
            ["docker", "logs", name], check=True, capture_output=True, text=True,
        )
        combined = logs.stdout + logs.stderr
        assert PRIVATE not in combined
        assert "Traceback" not in combined
        assert "runtime_exception" in combined if inject_failure else "runtime_warning" in combined
        return {"port": port, "forced_500": inject_failure, "status": "passed"}
    finally:
        docker("rm", "-f", name)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default="workbookcare-api:cloudrun-prep")
    args = parser.parse_args()
    platform = docker("image", "inspect", "-f", "{{.Os}}/{{.Architecture}}", args.image)
    assert platform == "linux/amd64"
    results = []
    for port, failure in [(8080, False), (9091, False), (9091, True)]:
        result = rehearse(args.image, port, inject_failure=failure)
        results.append(result)
        print(json.dumps(result), flush=True)
    print(json.dumps({"local_container_rehearsal": "passed", "runs": results}), flush=True)


if __name__ == "__main__":
    main()
