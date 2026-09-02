from __future__ import annotations

from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from app.config import Settings
from app.errors import WorkbookCareError
from app.security import validate_ooxml


def test_rejects_unsupported_extension(risky_workbook_bytes: bytes) -> None:
    with pytest.raises(WorkbookCareError) as exc_info:
        validate_ooxml("workbook.csv", risky_workbook_bytes, Settings())

    assert exc_info.value.code == "UNSUPPORTED_FILE_TYPE"
    assert exc_info.value.status_code == 415


def test_rejects_invalid_zip() -> None:
    with pytest.raises(WorkbookCareError) as exc_info:
        validate_ooxml("workbook.xlsx", b"not-a-zip", Settings())

    assert exc_info.value.code == "INVALID_OOXML"


def test_rejects_zip_path_traversal() -> None:
    stream = BytesIO()
    with ZipFile(stream, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "<Types />")
        archive.writestr("xl/workbook.xml", "<workbook />")
        archive.writestr("../escape.txt", "unsafe")

    with pytest.raises(WorkbookCareError) as exc_info:
        validate_ooxml("workbook.xlsx", stream.getvalue(), Settings())

    assert exc_info.value.code == "UNSAFE_ZIP_PATH"


def test_rejects_payload_over_configured_limit(risky_workbook_bytes: bytes) -> None:
    with pytest.raises(WorkbookCareError) as exc_info:
        validate_ooxml(
            "workbook.xlsx",
            risky_workbook_bytes,
            Settings(max_upload_mb=0),
        )

    assert exc_info.value.code == "FILE_TOO_LARGE"
