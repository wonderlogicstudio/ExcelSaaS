"""Bounded child process with credential-free environment, deadline, kill and cleanup."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import sysconfig
import tempfile
import threading
from pathlib import Path

from .delivery_execution_control import check_cancelled, controlled_process
from .delivery_inputs import reject
from .delivery_process import process_limits

LOCK = threading.BoundedSemaphore(1)


def run_comparison(message: dict, *, timeout: float = 30) -> dict:
    check_cancelled()
    if not LOCK.acquire(timeout=1):
        reject("COMPARISON_BUSY", "다른 비교가 진행 중입니다. 잠시 후 다시 시도하세요.", 429)
    try:
        with tempfile.TemporaryDirectory(prefix="workbookcare-compare-") as folder:
            Path(folder).chmod(0o700)
            env = {
                k: v
                for k, v in os.environ.items()
                if k in {"PATH", "Path", "SYSTEMROOT", "SystemRoot", "WINDIR"}
            }
            env.update(TMPDIR=folder, TEMP=folder, TMP=folder)
            executable = sys._base_executable if os.name == "nt" else sys.executable
            bootstrap = (
                "import sys,runpy;sys.path.insert(0,"
                + repr(sysconfig.get_path("purelib"))
                + ");runpy.run_path("
                + repr(str(Path(__file__).with_name("comparison_worker.py")))
                + ",run_name='__main__')"
            )
            child = subprocess.Popen(
                [executable, "-I", "-S", "-c", bootstrap],
                cwd=folder,
                env=env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            try:
                with controlled_process(child), process_limits(child):
                    output, _ = child.communicate(
                        json.dumps(message, ensure_ascii=False, allow_nan=False).encode(),
                        timeout=timeout,
                    )
            except subprocess.TimeoutExpired:
                child.kill()
                child.communicate()
                reject(
                    "COMPARISON_TIMEOUT",
                    "시간 초과로 비교를 종료했습니다. 일부 결과를 제공하지 않습니다.",
                    422,
                )
            except OSError:
                reject(
                    "COMPARISON_RESOURCE_LIMIT", "비교 실행의 자원 한도를 적용하지 못했습니다.", 503
                )
            finally:
                if child.poll() is None:
                    child.kill()
                    child.wait()
            check_cancelled()
            if len(output) > 16 * 1024**2:
                reject("COMPARISON_OUTPUT_LIMIT", "전체 비교 결과가 출력 한도를 초과했습니다.", 422)
            try:
                result = json.loads(output)
            except (ValueError, UnicodeError):
                reject("COMPARISON_PROCESS_FAILED", "전체 비교를 완료하지 못했습니다.", 422)
            if "error" in result:
                error = result["error"]
                reject(error["code"], error["message"], error["status"])
            if result.get("process_id") != child.pid:
                reject(
                    "COMPARISON_PROCESS_BOUNDARY",
                    "실제 실행 프로세스의 자원 제한 경계를 확인하지 못했습니다.",
                    503,
                )
            if child.returncode or not isinstance(result.get("result"), dict):
                reject("COMPARISON_PROCESS_FAILED", "전체 비교를 완료하지 못했습니다.", 422)
            return result["result"]
    finally:
        LOCK.release()
