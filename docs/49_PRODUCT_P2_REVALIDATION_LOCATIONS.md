# Product P2 — Re-validation location details

## Authorization and selection — 2026-09-12

The owner requested the next bounded product development step, full regression
verification, a Git commit, and GitHub synchronization. Read-only startup found
local and remote main at `47e5e54`, one commit after the supplied `4faae1b`.
The untracked `docs/delivery-v3_2/` is outside this change.

Candidates: location-level re-validation details (selected), finishing P1 visual
review, and a separately scoped M5 user-declared rule contract. P1 filters are
already implemented. The existing comparison holds full findings but displays
only comma-separated rule codes, so repeated rules cannot be distinguished by
location. P2 uses that existing in-memory data without a new product capability
or user-demand claim. M3/M3.5 evidence and M5 approval are not implied.

## Acceptance contract

- Keep the existing three groups and unique rule/location comparison semantics.
- Show each group's full count, an accessible native disclosure when nonempty,
  and each finding's title, rule code, sheet and cell when expanded.
- No-longer-detected entries describe the previous location. Continuing/new
  entries describe the current location. Distinguish workbook-level, sheet-only,
  and missing-sheet locations; do not guess a cell or sheet.
- Preserve all entries and source order, including repeated rules at different
  locations. No arbitrary detail truncation or nested scrolling.
- Use neutral group styling. Disappearance is not proof of repair, recalculation,
  or business correctness. Keep version/truncation warnings and explain that
  renamed sheets or moved cells can appear as disappeared/new findings.
- Empty groups have no useless disclosure. No comparison retains the current
  re-upload instructions. New scans reset disclosure through the result key.
- P1 filtering never filters the comparison. Full summary, risk, quote, CSV and
  local handling statuses are unchanged.
- Native keyboard disclosure, visible focus, long-label wrapping and a single
  column at mobile widths. Use synthetic fixtures and the local sample only.
- Run `scripts/verify.ps1` before/after implementation; inspect the changed local
  desktop/mobile flow and record evidence and limitations honestly.

## Boundaries

Only existing title/rule/location metadata is shown. Do not render additional
descriptions, formula evidence, raw values, filenames or finding keys. No new
storage, URL parameters, clipboard writes, requests, feedback, telemetry or
retention. The existing browser session owns previous/current results.

No scanner, comparison algorithm, API, Worker, infra, dependency, cloud resource,
deployment or feature-gate change. Do not resume H2/H3 checks, inspect cloud
resources, enable Formula Audit/feedback publicly, process real workbooks, invite
users, or begin M3/M3.5/M5, repair, payment, accounts, recalculation or AI.
Hosted Beta remains NOT READY under its separate operational gates.

## Verification

Baseline `scripts/verify.ps1` passed: web 36, Worker 13, API 72, TypeScript/build,
Ruff, and the M4-C supplied-pack gate (36 exact candidates, no extras). The
pre-existing Starlette/httpx warning remains.

After implementation, `scripts/verify.ps1` passed: web 43, Worker 13, API 72,
TypeScript/production build, Ruff and 36 exact M4-C supplied-pack candidates with
no extras. Seven added behavior tests cover repeated-rule locations, previous vs
current metadata, all entries and missing location scopes, excluding description
and key fields, version/truncation/interpretation limits, empty/no-comparison
states, filter/CSV invariance, new-scan reset, and the App's sample re-scan loop.

The changed flow was exercised through component/App interaction tests with
synthetic data. Actual desktop/mobile rendering remains unverified: the browser
connector was unavailable, and Windows computer-use was stopped because its
current-browser-URL check could not confidently enforce policy. No bypass or
other UI automation was attempted after that stop. This is IMPLEMENTED / VISUAL
REVIEW PENDING, not final P2 acceptance. `MILESTONE_REVIEW.md` holds the remaining
local-only checklist; it grants no deployment or live H2/H3 authority.
