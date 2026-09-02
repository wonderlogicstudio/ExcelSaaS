from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import PurePosixPath
from zipfile import BadZipFile, ZipFile

from .config import Settings
from .errors import WorkbookCareError

REQUIRED_OOXML_PARTS = {"[Content_Types].xml", "xl/workbook.xml"}
ALLOWED_EXTENSIONS = {".xlsx", ".xlsm"}


@dataclass(frozen=True, slots=True)
class OoxmlEnvelope:
    names: frozenset[str]
    has_macros: bool
    drawing_part_count: int
    external_link_part_count: int
    total_uncompressed_bytes: int


def _safe_zip_name(name: str) -> bool:
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    return not (
        not name
        or "\x00" in name
        or normalized.startswith("/")
        or any(part == ".." for part in path.parts)
    )


def validate_ooxml(filename: str, payload: bytes, settings: Settings) -> OoxmlEnvelope:
    suffix = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if suffix not in ALLOWED_EXTENSIONS:
        raise WorkbookCareError(
            code="UNSUPPORTED_FILE_TYPE",
            message="현재는 .xlsx와 .xlsm 파일만 검사할 수 있습니다.",
            status_code=415,
        )
    if not payload:
        raise WorkbookCareError("EMPTY_FILE", "비어 있는 파일은 검사할 수 없습니다.")
    if len(payload) > settings.max_upload_bytes:
        raise WorkbookCareError(
            "FILE_TOO_LARGE",
            f"파일은 {settings.max_upload_mb}MB 이하여야 합니다.",
            status_code=413,
        )

    source = BytesIO(payload)
    try:
        with ZipFile(source) as archive:
            entries = archive.infolist()
            if len(entries) > settings.max_zip_entries:
                raise WorkbookCareError(
                    "ZIP_ENTRY_LIMIT",
                    "파일 내부 항목 수가 안전 제한을 초과했습니다.",
                    status_code=413,
                )

            total_uncompressed = 0
            names: set[str] = set()
            for entry in entries:
                if not _safe_zip_name(entry.filename):
                    raise WorkbookCareError(
                        "UNSAFE_ZIP_PATH",
                        "파일 내부 경로가 안전하지 않습니다.",
                    )
                if entry.flag_bits & 0x1:
                    raise WorkbookCareError(
                        "ENCRYPTED_ZIP_ENTRY",
                        "암호화된 통합문서는 현재 검사할 수 없습니다.",
                        status_code=415,
                    )
                total_uncompressed += entry.file_size
                if total_uncompressed > settings.max_uncompressed_bytes:
                    raise WorkbookCareError(
                        "UNCOMPRESSED_SIZE_LIMIT",
                        "압축을 해제한 파일 크기가 안전 제한을 초과했습니다.",
                        status_code=413,
                    )
                if entry.file_size > 0:
                    ratio = entry.file_size / max(entry.compress_size, 1)
                    if ratio > settings.max_compression_ratio:
                        raise WorkbookCareError(
                            "COMPRESSION_RATIO_LIMIT",
                            "비정상적으로 높은 압축률의 파일은 검사할 수 없습니다.",
                            status_code=413,
                        )
                names.add(entry.filename)
    except WorkbookCareError:
        raise
    except BadZipFile as exc:
        raise WorkbookCareError(
            "INVALID_OOXML",
            "올바른 Excel OOXML 파일이 아닙니다.",
            status_code=415,
        ) from exc
    finally:
        source.close()

    missing = REQUIRED_OOXML_PARTS.difference(names)
    if missing:
        raise WorkbookCareError(
            "MISSING_OOXML_PART",
            "필수 Excel 구성요소가 없어 파일을 검사할 수 없습니다.",
            status_code=415,
        )

    lower_names = {name.lower() for name in names}
    has_macros = "xl/vbaproject.bin" in lower_names or suffix == ".xlsm"
    drawing_part_count = sum(
        1
        for name in lower_names
        if name.startswith("xl/drawings/")
        or name.startswith("xl/charts/")
        or name.startswith("xl/media/")
    )
    external_link_part_count = sum(
        1
        for name in lower_names
        if name.startswith("xl/externallinks/externallink") and name.endswith(".xml")
    )

    return OoxmlEnvelope(
        names=frozenset(names),
        has_macros=has_macros,
        drawing_part_count=drawing_part_count,
        external_link_part_count=external_link_part_count,
        total_uncompressed_bytes=total_uncompressed,
    )
