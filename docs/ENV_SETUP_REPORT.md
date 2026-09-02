# Windows local environment setup report

Date: 2026-08-31  
Scope: M0-M2 baseline only. M3, payment, cloud deployment, AI API, and sign-up work were not started.

## Installed runtime versions

- Node.js: `v24.20.0` (LTS)
- npm: `11.19.0`
- Project Python: `Python 3.13.15`, selected explicitly through `py -3.13`
- Existing Python: `Python 3.10.9` remains installed and unchanged.
- Virtual environment: `C:\Users\JinwonLee\project\ExcelSaaS\apps\api\.venv`

## Main installed packages

- Frontend: React 19.1.1, Vite 6.4.3, Vitest 3.2.7
- API: FastAPI 0.141.1, Uvicorn 0.52.4, openpyxl 3.1.5,
  defusedxml 0.7.1, pydantic-settings 2.15.0
- Test and quality: pytest 8.4.2, httpx 0.28.1, Ruff 0.16.5

## Commands run

```powershell
node -v
npm -v
python --version
py -0p
winget --version

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\bootstrap.ps1

.\scripts\dev.ps1

curl.exe --fail --silent --show-error -X POST -F "file=@samples\demo-risky-workbook.xlsx" http://localhost:8000/v1/scans

.\scripts\verify.ps1
```

`NPM_CONFIG_OFFLINE` was set on this PC, so `bootstrap.ps1` now disables it
only for its own `npm install` process. This makes the documented bootstrap
command work without requiring users to alter their global npm configuration.

## Files changed

- `scripts/bootstrap.ps1`
  - Detects Node through `npm.cmd` when the current PowerShell PATH is stale.
  - Selects the highest installed Python 3.12+ via `py`; it cannot select
    Python 3.10.
  - Stops on web-install or virtual-environment creation failure.
  - Disables the local npm offline setting for bootstrap only.
- `scripts/dev.ps1`
  - Starts the web command through `npm.cmd` and hides background windows.
- `scripts/verify.ps1`
  - Uses `npm.cmd` and fails correctly when pytest or Ruff fails.
- `apps/web/src/App.test.tsx`
  - Cleans up the rendered DOM after each test to keep tests isolated.
- `apps/api/app/scanner.py`
  - Removes two Ruff violations and wraps only display-string formatting;
    scanner behavior is unchanged.

## Results

- React home page: HTTP 200 at `http://localhost:5173`
- FastAPI health endpoint: HTTP 200 with
  `{"status":"ok","service":"workbookcare-api"}`
- FastAPI documentation: HTTP 200 and Swagger UI detected at
  `http://localhost:8000/docs`
- Sample diagnosis: `samples/demo-risky-workbook.xlsx` completed through
  `POST /v1/scans` with scanner `0.1.1`, rule set `2026.08.2`, 12 findings,
  and a KRW 39,000 quote preview. No company workbook was used.
- Final `scripts/verify.ps1` result:
  - Frontend: 3/3 Vitest tests passed.
  - Frontend: TypeScript/Vite production build passed.
  - Backend: 12/12 pytest tests passed.
  - Backend: `ruff check .` passed.

## Remaining issues and warnings

- A connected browser was not available to this automation session, so
  desktop/mobile visual screenshots were not captured. HTTP availability was
  verified; perform the manual browser check below before a user test.
- Frontend tests emit React `act(...)` environment warnings, but all tests pass.
- Backend tests emit two non-failing warnings: a Starlette/httpx deprecation
  warning and a Python 3.13 `ZipFile.__del__` cleanup warning.
- `git status` could not run because this folder is not yet a Git repository.
  No Git initialization was performed.

## User verification

Open a new PowerShell window in the repository root and run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\dev.ps1
```

Then verify:

1. Open `http://localhost:5173` on desktop and mobile-width browser windows.
   Use the sample-diagnosis flow and confirm the result and quote preview
   appear.
2. Open `http://localhost:8000/health`; it must return the JSON health body.
3. Open `http://localhost:8000/docs`; Swagger UI must load.
4. In another PowerShell window, run:

   ```powershell
   curl.exe -X POST -F "file=@samples\demo-risky-workbook.xlsx" http://localhost:8000/v1/scans
   ```

   Confirm the response contains `scanner_version`, `findings`, and `quote`.
5. Run `.\scripts\verify.ps1`; it must finish with
   `All verification steps passed.`

No further user action is required for the M0-M2 baseline. Git initialization
is optional and should be performed only when the product owner wants to begin
version tracking.
