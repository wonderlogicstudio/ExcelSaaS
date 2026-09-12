"""Private IPC entry point. It never creates customer files or uses source formula caches."""

from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.comparison_engine import compare_sources, preview, read_source
from app.config import Settings
from app.errors import WorkbookCareError


def comparison(message):
    sources = {
        side: read_source(
            item["filename"],
            base64.b64decode(item["file_base64"], validate=True),
            Settings(_env_file=None),
        )
        for side, item in message["sources"].items()
    }
    return (
        {"sources": {k: preview(v) for k, v in sources.items()}}
        if message["action"] == "preview"
        else compare_sources(sources, message["spec"])
    )


def report(message):
    if message["action"] == "comparison_artifacts":
        from app.comparison_artifacts import make_comparison_artifacts

        package = make_comparison_artifacts(message["model"], message["job"])
    else:
        from app.delivery_artifacts import make_artifacts

        package = make_artifacts(
            message["job"],
            message["plan"],
            base64.b64decode(message["repaired_base64"], validate=True),
            message["verification"],
        )
    for artifact in package["artifacts"].values():
        artifact["data_base64"] = base64.b64encode(artifact.pop("data")).decode()
    return package


def deny_network_or_process(event, _args):
    if (
        event.startswith("socket.")
        or event.startswith("subprocess.")
        or event in {"os.system", "os.exec", "os.posix_spawn", "os.spawn"}
    ):
        raise PermissionError("Report workers do not access network or create processes")


def main():
    sys.dont_write_bytecode = True
    sys.addaudithook(deny_network_or_process)
    try:
        data = sys.stdin.buffer.read(24 * 1024**2 + 1)
        if len(data) > 24 * 1024**2:
            raise ValueError()
        message = json.loads(data)
        if message["action"] in {"comparison_artifacts", "repair_artifacts"}:
            result = report(message)
        else:
            result = comparison(message)
        encoded = json.dumps(
            {"result": result, "process_id": os.getpid()},
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ).encode()
        if len(encoded) > 16 * 1024**2:
            raise ValueError()
        sys.stdout.buffer.write(encoded)

    except WorkbookCareError as error:
        sys.stdout.write(
            json.dumps(
                {
                    "error": {
                        "code": error.code,
                        "message": error.message,
                        "status": error.status_code,
                    }
                },
                ensure_ascii=True,
            )
        )
        raise SystemExit(2) from None
    except Exception:
        sys.stdout.write(
            json.dumps(
                {
                    "error": {
                        "code": "COMPARISON_PROCESS_FAILED",
                        "message": "전체 처리에 실패했습니다. 자료 형식과 한도를 확인하세요.",
                        "status": 422,
                    }
                },
                ensure_ascii=True,
            )
        )
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
