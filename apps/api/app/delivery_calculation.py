"""D03: strict reference grammar and isolated, non-saving Apache POI evaluator."""

from __future__ import annotations

import base64
import hashlib
import json
import math
import os
import shutil
import subprocess
import tempfile
import threading
from dataclasses import dataclass
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
CALCULATION_MODE_LEGACY = "legacy_local"
CALCULATION_MODE_MONTHLY_SHEETS = "monthly_sheet_internal"
CALCULATION_MODES = {CALCULATION_MODE_LEGACY, CALCULATION_MODE_MONTHLY_SHEETS}
MONTHLY_SHEETS = frozenset(f"M{month:02d}" for month in range(1, 13))
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
    "M!R": "MONTHLY_DIRECT_REFERENCE",
    "M!R-M!R": "MONTHLY_SAME_MONTH_SUBTRACT",
}


@dataclass(frozen=True)
class _Reference:
    sheet: str
    cell: str
    monthly_sheet: bool = False


def _validate_mode(calculation_mode: str) -> None:
    if calculation_mode not in CALCULATION_MODES:
        reject("ENGINE_UNSUPPORTED", "unsupported calculation mode")


def _parse_monthly_reference(value: str, sheet_names: set[str]) -> _Reference | None:
    if "!" not in value or "[" in value or "]" in value or ":" in value or "$" in value:
        return None
    sheet, cell = value.rsplit("!", 1)
    if sheet.startswith("'") and sheet.endswith("'"):
        sheet = sheet[1:-1].replace("''", "'")
    if sheet not in MONTHLY_SHEETS:
        return None
    if sheet not in sheet_names:
        reject("ENGINE_UNSUPPORTED", "missing monthly sheet")
    return _Reference(sheet, valid_cell(cell.upper()), monthly_sheet=True)


def _validate_monthly_operand(cells: dict, ref: _Reference) -> None:
    record = cells.get(ref.sheet, {}).get(ref.cell)
    if record is None:
        reject("ENGINE_UNSUPPORTED", "missing monthly reference cell")
    if record["type"] == "number":
        try:
            number = float(record["value"])
        except (TypeError, ValueError):
            reject("ENGINE_UNSUPPORTED", "monthly reference must be numeric")
        if not math.isfinite(number):
            reject("ENGINE_UNSUPPORTED", "monthly reference must be finite")
        return
    if record["type"] == "formula":
        return
    reject("ENGINE_UNSUPPORTED", "monthly reference must be numeric")


def _formula_shape(
    formula: str,
    *,
    calculation_mode: str = CALCULATION_MODE_LEGACY,
    current_sheet: str | None = None,
    sheet_names: set[str] | None = None,
) -> tuple[str, set[_Reference]]:
    _validate_mode(calculation_mode)
    if not isinstance(formula, str) or len(formula) > 1024 or not formula.startswith("="):
        reject("ENGINE_UNSUPPORTED", "지원하는 수식 문법과 길이를 벗어났습니다.")
    try:
        tokens = Tokenizer(formula).items
    except Exception:
        reject("ENGINE_UNSUPPORTED", "수식을 안전하게 해석할 수 없습니다.")
    if calculation_mode == CALCULATION_MODE_MONTHLY_SHEETS and current_sheet is None:
        reject("ENGINE_UNSUPPORTED", "missing current sheet")
    sheet_names = set(sheet_names or [])
    shape = []
    references: set[_Reference] = set()
    monthly_references: list[_Reference] = []
    for t in tokens:
        if t.type == "WHITE-SPACE":
            continue
        if t.type == "OPERAND" and t.subtype == "RANGE":
            monthly = (
                _parse_monthly_reference(t.value, sheet_names)
                if calculation_mode == CALCULATION_MODE_MONTHLY_SHEETS
                else None
            )
            if monthly is not None:
                references.add(monthly)
                monthly_references.append(monthly)
                shape.append("M!R")
                continue
            clean = t.value.replace("$", "").upper()
            if "!" in clean:
                reject("ENGINE_UNSUPPORTED", "cross-sheet references require monthly mode")
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
                    _Reference(current_sheet or "", f"{get_column_letter(col)}{row}")
                    for col in range(a, c + 1)
                    for row in range(b, d + 1)
                )
                shape.append("G")
            else:
                references.add(_Reference(current_sheet or "", valid_cell(clean)))
                shape.append("R")
        else:
            shape.append(t.value.upper() if t.type == "FUNC" else t.value)
    signature = "".join(shape)
    if monthly_references and signature == "M!R-M!R" and len(
        {ref.sheet for ref in monthly_references}
    ) != 1:
        reject("ENGINE_UNSUPPORTED", "monthly subtraction requires one source sheet")
    if signature not in SHAPES:
        reject("ENGINE_UNSUPPORTED", "이 수식 조합은 아직 계산 프로필에서 검증하지 않았습니다.")
    return signature, references


def formula_shape(
    formula: str,
    *,
    calculation_mode: str = CALCULATION_MODE_LEGACY,
    current_sheet: str | None = None,
    sheet_names: set[str] | None = None,
) -> tuple[str, set[str]]:
    shape, references = _formula_shape(
        formula,
        calculation_mode=calculation_mode,
        current_sheet=current_sheet,
        sheet_names=sheet_names,
    )
    if calculation_mode == CALCULATION_MODE_MONTHLY_SHEETS:
        return shape, {f"{ref.sheet}!{ref.cell}" for ref in references}
    return shape, {ref.cell for ref in references}


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


def coverage(cells: dict, *, calculation_mode: str = CALCULATION_MODE_LEGACY) -> dict:
    _validate_mode(calculation_mode)
    graph = {}
    combinations = set()
    sheet_names = set(cells)
    for sheet, rows in cells.items():
        for address, record in rows.items():
            if record["type"] == "date" or record.get("special_format"):
                reject(
                    "ENGINE_UNSUPPORTED",
                    "날짜·백분율 표시가 있는 파일의 전체 계산은 아직 지원하지 않습니다.",
                )
            if record["type"] == "formula":
                shape, refs = _formula_shape(
                    record["value"],
                    calculation_mode=calculation_mode,
                    current_sheet=sheet,
                    sheet_names=sheet_names,
                )
                for ref in refs:
                    if ref.monthly_sheet:
                        _validate_monthly_operand(cells, ref)
                combinations.add(SHAPES[shape])
                graph[(sheet, address)] = {
                    (ref.sheet, ref.cell)
                    for ref in refs
                    if cells.get(ref.sheet, {}).get(ref.cell, {}).get("type") == "formula"
                }
    visiting = set()
    longest_paths = {}

    def walk(node, depth=0):
        if depth > 100:
            reject("ENGINE_UNSUPPORTED", "순환 참조 또는 계산 깊이 한도를 초과했습니다.")
        if node in visiting:
            reject("ENGINE_UNSUPPORTED", "순환 참조 또는 계산 깊이 한도를 초과했습니다.")
        if node in longest_paths:
            if depth + longest_paths[node] > 100:
                reject("ENGINE_UNSUPPORTED", "순환 참조 또는 계산 깊이 한도를 초과했습니다.")
            return longest_paths[node]
        visiting.add(node)
        longest = 0
        for child in graph[node]:
            longest = max(longest, 1 + walk(child, depth + 1))
        visiting.remove(node)
        if longest > 100:
            reject("ENGINE_UNSUPPORTED", "순환 참조 또는 계산 깊이 한도를 초과했습니다.")
        longest_paths[node] = longest
        return longest

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


def calculate(
    cells: dict,
    *,
    timeout_seconds: float = 10.0,
    calculation_mode: str = CALCULATION_MODE_LEGACY,
) -> dict:
    check_cancelled()
    _validate_mode(calculation_mode)
    cover = coverage(cells, calculation_mode=calculation_mode)
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
            if calculation_mode == CALCULATION_MODE_MONTHLY_SHEETS:
                lines[0] += "\t" + calculation_mode
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
            if calculation_mode == CALCULATION_MODE_MONTHLY_SHEETS:
                sheet_names = set(cells)
                for sheet, rows in cells.items():
                    for address, cell in rows.items():
                        if cell["type"] != "formula":
                            continue
                        shape, refs = _formula_shape(
                            cell["value"],
                            calculation_mode=calculation_mode,
                            current_sheet=sheet,
                            sheet_names=sheet_names,
                        )
                        for ref in refs:
                            if ref.monthly_sheet:
                                ref_value = values.get(ref.sheet, {}).get(ref.cell, {})
                                if ref_value.get("type") != "number" or not math.isfinite(
                                    float(ref_value.get("value"))
                                ):
                                    reject(
                                        "ENGINE_UNSUPPORTED",
                                        "monthly operand must resolve to number",
                                    )
                        if SHAPES[shape].startswith("MONTHLY_"):
                            actual = values.get(sheet, {}).get(address, {})
                            if actual.get("type") != "number":
                                reject(
                                    "ENGINE_UNSUPPORTED",
                                    "monthly formula must resolve to number",
                                )
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
