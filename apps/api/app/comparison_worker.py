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


def main():
    try:
        data = sys.stdin.buffer.read(6 * 1024**2 + 1)
        if len(data) > 6 * 1024**2:
            raise ValueError()
        message = json.loads(data)
        sources = {
            side: read_source(
                item["filename"],
                base64.b64decode(item["file_base64"], validate=True),
                Settings(_env_file=None),
            )
            for side, item in message["sources"].items()
        }
        result = (
            {"sources": {k: preview(v) for k, v in sources.items()}}
            if message["action"] == "preview"
            else compare_sources(sources, message["spec"])
        )
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
