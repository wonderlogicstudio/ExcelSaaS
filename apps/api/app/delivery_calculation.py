"""D03: strict reference grammar and isolated, non-saving Apache POI evaluator."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path

from openpyxl.formula import Tokenizer
from openpyxl.formula.translate import Translator, TranslatorError
from openpyxl.utils.cell import get_column_letter, range_boundaries

from .delivery_execution_control import check_cancelled, controlled_process
from .delivery_inputs import MAX_CELLS, digest, reject, valid_cell
from .delivery_process import process_limits

ENGINE_VERSION = "apache-poi-5.5.1-adapter-v1"
REGISTRY_VERSION = "integer-repair-combinations-v1"
ENGINE_DIR = Path(__file__).resolve().parents[1] / "engine"
CALC_LOCK = threading.BoundedSemaphore(1)
SHAPES = {
    "SUM(G)": "SUM_INTERNAL_RANGE",
    "ROUND(R*R*(1-R),0)": "ROUND_AMOUNT",
    "ROUND(R*R,0)": "ROUND_PRODUCT",
    "ROUND(R,0)": "ROUND_INTEGER",
    "IF(AND(ISNUMBER(R),ISNUMBER(R),ISNUMBER(R)),ROUND(R*R*(1-R),0),0)": "IF_AND_AMOUNT",
    'IF(OR(R=0,R=""),0,ROUND(R*R,0))': "IF_OR_PRODUCT",
    "IFERROR(R/R,0)": "IFERROR_DIVISION",
    "R/R": "DIVISION",
    "R+R": "ADD",
    "R-R": "SUBTRACT",
    "R*R": "MULTIPLY",
    '""': "EMPTY_STRING",
    "R": "DIRECT_REFERENCE",
}


def formula_shape(formula: str) -> tuple[str, set[str]]:
    if not isinstance(formula, str) or len(formula) > 1024 or not formula.startswith("="):
        reject("ENGINE_UNSUPPORTED", "지원하는 수식 문법과 길이를 벗어났습니다.")
    try:
        tokens = Tokenizer(formula).items
    except Exception:
        reject("ENGINE_UNSUPPORTED", "수식을 안전하게 해석할 수 없습니다.")
    shape = []
    references = set()
    for t in tokens:
        if t.type == "WHITE-SPACE":
            continue
        if t.type == "OPERAND" and t.subtype == "RANGE":
            clean = t.value.replace("$", "").upper()
            if ":" in clean:
                ends = clean.split(":")
                if len(ends) != 2:
                    reject("ENGINE_UNSUPPORTED", "단일 내부 A1 범위만 지원합니다.")
                for end in ends:
                    valid_cell(end)
                a, b, c, d = range_boundaries(clean)
                if a > c or b > d or (c - a + 1) * (d - b + 1) > MAX_CELLS:
                    reject("ENGINE_UNSUPPORTED", "참조 범위가 계산 한도를 넘습니다.")
                references.update(
                    f"{get_column_letter(col)}{row}"
                    for col in range(a, c + 1)
                    for row in range(b, d + 1)
                )
                shape.append("G")
            else:
                references.add(valid_cell(clean))
                shape.append("R")
        else:
            shape.append(t.value.upper() if t.type == "FUNC" else t.value)
    signature = "".join(shape)
    if signature not in SHAPES:
        reject("ENGINE_UNSUPPORTED", "이 수식 조합은 아직 계산 프로필에서 검증하지 않았습니다.")
    return signature, references


def translate_formula(formula: str, anchor: str, target: str) -> str:
    formula_shape(formula)
    try:
        translated = Translator(formula, origin=valid_cell(anchor)).translate_formula(
            valid_cell(target)
        )
    except (TranslatorError, ValueError):
        reject("ENGINE_UNSUPPORTED", "기준 수식을 옮기면 참조가 범위를 벗어납니다.")
    formula_shape(translated)
    return translated


def coverage(cells: dict) -> dict:
    graph = {}
    combinations = set()
    for sheet, rows in cells.items():
        for address, record in rows.items():
            if record["type"] == "date" or record.get("special_format"):
                reject(
                    "ENGINE_UNSUPPORTED",
                    "날짜·백분율 표시가 있는 파일의 전체 계산은 아직 지원하지 않습니다.",
                )
            if record["type"] == "formula":
                shape, refs = formula_shape(record["value"])
                combinations.add(SHAPES[shape])
                graph[(sheet, address)] = {
                    (sheet, ref) for ref in refs if rows.get(ref, {}).get("type") == "formula"
                }
    seen = set()
    visiting = set()

    def walk(node, depth=0):
        if depth > 100 or node in visiting:
            reject("ENGINE_UNSUPPORTED", "순환 참조 또는 계산 깊이 한도를 초과했습니다.")
        if node in seen:
            return
        visiting.add(node)
        for child in graph[node]:
            walk(child, depth + 1)
        visiting.remove(node)
        seen.add(node)

    for node in graph:
        walk(node)
    return {
        "scope": "WHOLE_WORKBOOK",
        "formula_count": len(graph),
        "combinations": sorted(combinations),
        "registry_version": REGISTRY_VERSION,
    }


def engine_fingerprint() -> str:
    paths = [
        ENGINE_DIR / "DeliveryCalc.java",
        ENGINE_DIR / "dependencies.lock.json",
        Path(__file__),
        Path(__file__).with_name("delivery_process.py"),
        Path(__file__).with_name("delivery_execution_control.py"),
        ENGINE_DIR / "classes/DeliveryCalc.class",
    ]
    dependencies = json.loads((ENGINE_DIR / "dependencies.lock.json").read_text(encoding="utf-8"))
    for item in dependencies["artifacts"]:
        jar = ENGINE_DIR / "lib" / f"{item['artifact']}-{item['version']}.jar"
        if not jar.is_file() or hashlib.sha512(jar.read_bytes()).hexdigest() != item["sha512"]:
            reject("ENGINE_INTEGRITY_FAILED", "계산 엔진 파일 검증에 실패했습니다.", 503)
    return digest({p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})


def _encode(value: object) -> str:
    text = "" if value is None else str(value).lower() if isinstance(value, bool) else str(value)
    return base64.b64encode(text.encode()).decode()


def _policy(scratch: Path, java: Path) -> str:
    paths = [ENGINE_DIR.resolve(), java.resolve().parent.parent, scratch.resolve()]
    reads = "\n".join(
        f'permission java.io.FilePermission "{p.as_posix()}/-", "read";' for p in paths
    )
    # No SocketPermission or executable file permission is granted. Child env
    # contains no provider/session credentials. Policy is enforced by JDK 17.
    return (
        """grant {
permission java.util.PropertyPermission "*", "read,write";
permission java.lang.RuntimePermission "accessDeclaredMembers";
permission java.lang.RuntimePermission "getClassLoader";
permission java.lang.RuntimePermission "createClassLoader";
permission java.lang.RuntimePermission "accessClassInPackage.*";
permission java.lang.RuntimePermission "getenv.*";
permission java.lang.RuntimePermission "shutdownHooks";
permission java.lang.reflect.ReflectPermission "suppressAccessChecks";
permission java.util.logging.LoggingPermission "control";
permission java.lang.management.ManagementPermission "monitor";
"""
        + reads
        + "\n};\n"
    )


def calculate(cells: dict, *, timeout_seconds: float = 10.0) -> dict:
    check_cancelled()
    cover = coverage(cells)
    engine_fingerprint()  # Verify executable dependencies before sending any input.
    java = shutil.which("java")
    if not java or not (ENGINE_DIR / "classes/DeliveryCalc.class").is_file():
        reject("ENGINE_NOT_READY", "계산 엔진이 준비되지 않았습니다.", 503)
    if not CALC_LOCK.acquire(timeout=1):
        reject("ENGINE_BUSY", "다른 계산이 진행 중입니다. 잠시 후 다시 시도하세요.", 429)
    try:
        with tempfile.TemporaryDirectory(prefix="workbookcare-calc-") as folder:
            scratch = Path(folder)
            os.chmod(scratch, 0o700)
            policy = scratch / "sandbox.policy"
            policy.write_text(_policy(scratch, Path(java)), encoding="utf-8")
            lines = ["CALC_V1"]
            for sheet, rows in cells.items():
                for address, cell in rows.items():
                    lines.append(
                        "\t".join([_encode(sheet), address, cell["type"], _encode(cell["value"])])
                    )
            payload = ("\n".join(lines) + "\n").encode()
            command = [
                java,
                "-Xmx128m",
                "-XX:MaxMetaspaceSize=96m",
                "-Xss512k",
                "-XX:CompressedClassSpaceSize=32m",
                "-XX:ReservedCodeCacheSize=32m",
                "-XX:MaxDirectMemorySize=16m",
                "-XX:ActiveProcessorCount=1",
                "-Djava.security.manager",
                "-Djava.security.policy==" + str(policy),
                "-Djava.io.tmpdir=" + str(scratch),
                "-Dlog4j2.statusLoggerLevel=OFF",
                "-cp",
                os.pathsep.join([str(ENGINE_DIR / "classes"), str(ENGINE_DIR / "lib/*")]),
                "DeliveryCalc",
            ]
            env = {
                k: v
                for k, v in os.environ.items()
                if k in {"PATH", "Path", "SYSTEMROOT", "SystemRoot", "WINDIR", "JAVA_HOME"}
            }
            env.update(TMPDIR=str(scratch), TEMP=str(scratch), TMP=str(scratch))
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                cwd=scratch,
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            try:
                with controlled_process(process), process_limits(process):
                    output, _ = process.communicate(payload, timeout=timeout_seconds)
            except OSError:
                reject(
                    "ENGINE_RESOURCE_FAILURE",
                    "계산 프로세스의 자원 제한을 적용하지 못했습니다.",
                    503,
                )
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
                reject(
                    "ENGINE_TIMEOUT",
                    "계산 시간 한도를 초과했습니다. 계산 프로세스를 종료했습니다.",
                    422,
                )
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()
            check_cancelled()
            if process.returncode != 0:
                reject(
                    "ENGINE_RESOURCE_FAILURE" if process.returncode == 22 else "ENGINE_UNSUPPORTED",
                    "계산을 완료하지 못했습니다. 오류를 숫자 0으로 대체하지 않습니다.",
                    422,
                )
            if len(output) > 2_000_000 or not output.startswith(b"CALC_RESULT_V1\n"):
                reject("ENGINE_RESOURCE_FAILURE", "계산 결과 한도를 초과했습니다.", 422)
            values = {}
            for line in output.decode().splitlines()[1:]:
                sheet, address, kind, value = line.split("\t")
                sheet = base64.b64decode(sheet).decode()
                value = base64.b64decode(value).decode()
                if kind == "number":
                    value = float(value)
                elif kind == "boolean":
                    value = value == "true"
                elif kind == "blank":
                    value = None
                values.setdefault(sheet, {})[address] = {
                    "type": kind,
                    "value": value,
                    "provenance": "ENGINE_CALCULATED",
                }
            expected = {(s, c) for s, rows in cells.items() for c in rows}
            if expected != {(s, c) for s, rows in values.items() for c in rows}:
                reject("ENGINE_RESOURCE_FAILURE", "전체 계산 결과가 반환되지 않았습니다.", 422)
            return {
                "values": values,
                "coverage": cover,
                "engine_version": ENGINE_VERSION,
                "cached_values_used": False,
            }
    finally:
        CALC_LOCK.release()
