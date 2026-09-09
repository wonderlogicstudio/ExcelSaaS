"""Container launcher: one worker and content-free server/dependency logs."""

from __future__ import annotations

import json
import logging
import os

import uvicorn


class RuntimeFormatter(logging.Formatter):
    """Never format arbitrary messages, arguments, tracebacks, or warning text."""

    def format(self, record: logging.LogRecord) -> str:
        event = "runtime_log"
        if record.name == "py.warnings":
            event = "runtime_warning"
        elif record.exc_info or record.exc_text:
            event = "runtime_exception"
        severity = {
            logging.DEBUG: "DEBUG",
            logging.INFO: "INFO",
            logging.WARNING: "WARNING",
            logging.ERROR: "ERROR",
            logging.CRITICAL: "CRITICAL",
        }.get(record.levelno, "DEFAULT")
        return json.dumps({"event": event, "severity": severity}, separators=(",", ":"))


LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "runtime": {"()": "app.runtime.RuntimeFormatter"},
        "safe_event": {"format": "%(message)s"},
    },
    "handlers": {
        "runtime": {"class": "logging.StreamHandler", "formatter": "runtime"},
        "safe_event": {"class": "logging.StreamHandler", "formatter": "safe_event"},
    },
    "root": {"handlers": ["runtime"], "level": "INFO"},
    "loggers": {
        "uvicorn": {"handlers": ["runtime"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"handlers": [], "level": "INFO", "propagate": True},
        "uvicorn.access": {"handlers": [], "propagate": False},
        "workbookcare.safe_events": {
            "handlers": ["safe_event"], "level": "INFO", "propagate": False,
        },
    },
}


def main() -> None:
    try:
        port = int(os.environ.get("PORT", "8080"))
        if not 1 <= port <= 65535:
            raise ValueError
    except ValueError:
        raise SystemExit("PORT must be an integer between 1 and 65535") from None

    # openpyxl warnings can contain workbook-defined names and formula text.
    logging.captureWarnings(True)
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        workers=1,
        access_log=False,
        log_config=LOG_CONFIG,
    )


if __name__ == "__main__":
    main()
