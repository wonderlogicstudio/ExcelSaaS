from __future__ import annotations

import json
import logging
import sys

import pytest

from app import runtime


def test_runtime_log_omits_message_arguments_exception_stack_and_extras() -> None:
    private = "SYNTHETIC_PRIVATE filename.xlsx =SUM(Secret!A1) user@example.invalid"
    try:
        raise RuntimeError(private)
    except RuntimeError:
        record = logging.LogRecord(
            "uvicorn.error", logging.ERROR, private, 1, "%s", (private,), sys.exc_info()
        )
    record.stack_info = private
    record.customer_data = private
    assert json.loads(runtime.RuntimeFormatter().format(record)) == {
        "event": "runtime_exception", "severity": "ERROR",
    }


def test_runtime_warning_omits_parser_warning_content() -> None:
    record = logging.LogRecord(
        "py.warnings", logging.WARNING, "private.xlsx", 1,
        "Print area cannot be set: =Secret!A1", (), None,
    )
    assert json.loads(runtime.RuntimeFormatter().format(record)) == {
        "event": "runtime_warning", "severity": "WARNING",
    }


@pytest.mark.parametrize("port", ["0", "65536", "not-a-port", ""])
def test_invalid_container_port_fails_without_echoing_input(monkeypatch, port: str) -> None:
    monkeypatch.setenv("PORT", port)
    with pytest.raises(SystemExit, match="^PORT must be an integer between 1 and 65535$"):
        runtime.main()
