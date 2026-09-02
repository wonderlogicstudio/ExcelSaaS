# WorkbookCare — Codex-managed Excel diagnosis SaaS starter

> 한국어 전체 안내: [`START_HERE_KO.md`](START_HERE_KO.md)

`WorkbookCare` is a working product name. Rename it before purchasing a domain or filing a trademark.

This repository is a tested vertical slice and a product-development control system for an Excel workbook diagnosis and safe-repair SaaS.

## Fastest product preview

Open `preview/index.html` directly in Chrome or Edge. It is an offline visual replica for product review; the maintained implementation is the React app. Captured views are under `artifacts/screenshots/`.

## What is already included

- A polished Korean-first React landing page and interactive diagnosis demo.
- A real `.xlsx` / `.xlsm` static-analysis API built with FastAPI and `openpyxl`.
- A deterministic risk score, complexity band, issue list, and quote preview.
- Security controls for file type, upload size, OOXML ZIP structure, decompression limits, and path traversal.
- Frontend test specifications, backend tests, a synthetic workbook generator, and visual-review artifacts.
- A milestone-gated Codex workflow: Codex chooses implementation details, while the product owner approves each milestone.
- Product, UX, architecture, privacy, pricing, token-budget, and deployment specifications.

## Product principle

> Codex owns implementation decisions inside an approved milestone. The human owns product direction and milestone approval.

Codex must not silently advance to the next milestone.

## Local startup

### 1. Backend

PowerShell:

```powershell
cd apps/api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

macOS/Linux:

```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --reload --port 8000
```

API docs: `http://localhost:8000/docs`

### 2. Frontend

From the repository root:

```bash
npm install
npm run dev:web
```

Website: `http://localhost:5173`

The website also includes a demo analysis path that works when the API is not running.

## Verification

The supplied environment passed 12 backend tests, Python compilation, TS/TSX syntax checks, and offline desktop/mobile visual QA. Its npm registry was unavailable, so run the real Vitest and Vite build locally after `npm install`. See `docs/MILESTONE_REVIEW.md`.


```bash
npm run verify:web
```

Then, from `apps/api` with the virtual environment activated:

```bash
pytest
ruff check .
```

## Start Codex correctly

1. Open the repository root in the Codex IDE extension.
2. Read `docs/00_CONTEXT_INDEX.md` yourself once.
3. Paste the contents of `prompts/01_FIRST_CODEX_GOAL.md` into Codex Goal mode.
4. Review `docs/MILESTONE_REVIEW.md` when Codex stops.
5. Approve with the short prompt in `prompts/02_APPROVE_AND_CONTINUE.md`.

Do not ask Codex to "finish the whole SaaS." One goal should implement one approved milestone.

## Current product state

The current vertical slice is suitable for usability and value-proposition testing. It is **not production-ready** and does not yet include authentication, cloud object storage, payment, a production repair engine, or legal/compliance documents.

## Recommended Git baseline

After extraction and local verification:

```bash
git init
git add .
git commit -m "WorkbookCare M0-M2 baseline"
```

A clean commit gives Codex a reliable diff and rollback point for each approved milestone.
