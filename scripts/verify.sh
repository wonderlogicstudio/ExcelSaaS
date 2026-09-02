#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
npm run verify:web
cd apps/api
. .venv/bin/activate
pytest
ruff check .
echo "All verification steps passed."
