"""Exercise the real multipart/exit-stack cleanup, including disk rollover."""

from __future__ import annotations

import asyncio
from io import BytesIO
from tempfile import SpooledTemporaryFile
from zipfile import ZipFile

import pytest
from fastapi.testclient import TestClient
from starlette import formparsers
from starlette.datastructures import Headers
from starlette.requests import ClientDisconnect

from app import main


@pytest.fixture
def spooled_uploads(monkeypatch):
    uploads = []

    def tracked_file(*args, **kwargs):
        upload = SpooledTemporaryFile(*args, **kwargs)  # noqa: SIM115 - parser owns lifetime
        uploads.append(upload)
        return upload

    monkeypatch.setattr(formparsers, "SpooledTemporaryFile", tracked_file)
    monkeypatch.setattr(formparsers.MultiPartParser, "spool_max_size", 1)
    return uploads


@pytest.mark.parametrize(
    ("scenario", "expected_status"),
    [("success", 200), ("type", 415), ("size", 413), ("envelope", 415), ("parse", 422),
     ("gate", 404), ("missing", 422), ("unexpected", 500)],
)
def test_request_closes_spooled_upload_on_every_terminal_path(
    monkeypatch, spooled_uploads, risky_workbook_bytes, scenario, expected_status,
) -> None:
    endpoint = "/v1/scans"
    field = "file"
    filename = "synthetic.xlsx"
    payload = risky_workbook_bytes
    if scenario == "type":
        filename = "synthetic.txt"
    elif scenario == "size":
        monkeypatch.setattr(main.settings, "max_upload_mb", 0)
    elif scenario == "envelope":
        payload = b"not an OOXML package"
    elif scenario == "parse":
        output = BytesIO()
        with ZipFile(BytesIO(payload)) as source, ZipFile(output, "w") as target:
            for entry in source.infolist():
                content = b"<invalid" if entry.filename == "xl/workbook.xml" else source.read(entry)
                target.writestr(entry, content)
        payload = output.getvalue()
    elif scenario == "gate":
        endpoint = "/v1/formula-audits"
        monkeypatch.setattr(main.settings, "formula_pattern_audit_enabled", False)
    elif scenario == "missing":
        field = "wrong_field"
    elif scenario == "unexpected":
        def fail(*args):
            raise RuntimeError("synthetic private detail")

        monkeypatch.setattr(main, "scan_workbook", fail)

    with TestClient(main.app, raise_server_exceptions=False) as client:
        response = client.post(endpoint, files={field: (filename, payload)})
    assert response.status_code == expected_status
    assert spooled_uploads
    assert all(upload._rolled and upload.closed for upload in spooled_uploads)


def test_partial_multipart_disconnect_closes_spooled_upload(spooled_uploads) -> None:
    async def disconnected_stream():
        yield (
            b'--boundary\r\nContent-Disposition: form-data; name="file"; '
            b'filename="synthetic.xlsx"\r\n\r\npartial workbook bytes'
        )
        raise ClientDisconnect

    parser = formparsers.MultiPartParser(
        Headers({"content-type": "multipart/form-data; boundary=boundary"}),
        disconnected_stream(),
    )
    with pytest.raises(ClientDisconnect):
        asyncio.run(parser.parse())
    assert spooled_uploads
    assert all(upload._rolled and upload.closed for upload in spooled_uploads)
