# Current progress

## Current override — 2026-09-09

**Hosted Beta H2 is approved and in progress.** This section supersedes the
earlier H1-only stop record below. The product owner created the private
`workbookcare-beta-uploads` R2 bucket with a one-day deletion lifecycle, the
Access-protected `workbookcare-beta` Worker with its `UPLOADS` R2 binding, enabled
Google API Gateway, and granted only
`workbookcare-gateway-invoker@workbookcare-beta.iam.gserviceaccount.com` the Cloud
Run Invoker role on the existing IAM-required `workbookcare-api-beta` service.

Tokyo API Gateway (`asia-northeast1`) is explicitly approved to reach the existing
Seoul Cloud Run service (`asia-northeast3`). The cross-region bridge is
synthetic-only until H2 completes: provider secrets, an updated revision of the
same Cloud Run service, API Gateway, deployed Worker assets/control route, and all
positive/negative/deletion checks remain open. No invitations, real workbook use,
repair, payment, hosted Formula Audit, AI, M5, or H3 work has started.

Current local H2 evidence: standard verification passed with web 25 tests and
production build, Worker 3 tests, API 68 tests, Ruff, and the M4-C supplied pack.
M4 release verification passed under its existing narrow fixture waiver (72/72
locations and top-level rules); M4-A.5 remains `CONDITIONAL_GO`. A freshly built
local H2 container passed synthetic signed-upload, error, health, non-root, and
temporary-file cleanup rehearsals. These results do not prove a deployed gateway,
Access policy, R2 lifecycle, or Cloud Run revision.

## Current step — 2026-09-09

**Cloud Run preparation completed; deployment stopped.** The owner's 2026-09-08
instruction supersedes the broader H2 execution scope for this step. Container
runtime logging is content-free, build context is restricted, and multipart spool
cleanup is verified. Docker rehearsals passed on 8080/9091 and forced 500; web 23,
API 65, build/Ruff, supplied M4-C pack and complete M4 RC verification passed with
the existing fixture waiver. M4-A.5 remains CONDITIONAL_GO. No cloud resources,
image push, frontend deployment, Cloudflare/R2, signup/payment/repair, or scanner
behavior changes. Details: `43_CLOUD_RUN_PREPARATION.md` and `MILESTONE_REVIEW.md`.
Earlier H2 status below is historical; do not resume deployment automatically.


## Completed

- [x] Market and competitor research.
- [x] Product positioning and value proposition.
- [x] Milestone-controlled Codex operating model.
- [x] Responsive React conversion prototype.
- [x] Sample diagnosis and quote-preview flow.
- [x] FastAPI static workbook scan endpoint.
- [x] OOXML ZIP safety checks.
- [x] Deterministic initial diagnostic rules.
- [x] Risk score, complexity band, and quote preview.
- [x] Backend automated test suite (12 passing tests in supplied environment).
- [x] Frontend test specifications, TS/TSX syntax verification, and offline visual QA.
- [x] Cloudflare/Cloud Run target design.
- [x] Korean start guide, revenue experiments, and user-test playbook.
- [x] M2.5 service-scope result UX, evidence grades, and four repairability summaries.
- [x] Scanner-generated frontend sample fixture with scanner/fixture consistency test.
- [x] Separate recommendation engine and planned-service catalog with beta price ranges.
- [x] Repair-readiness path derived from existing finding classifications, with planned approval-based repair and re-validation stages.
- [x] M2.5 Extension: rule-based Action Category and direct Excel-check guidance for every current static rule.
- [x] M2.5 Extension: value-free finding keys, same-session manual re-validation comparison, and local handling status.
- [x] M2.5 Extension: browser-generated UTF-8 BOM CSV result download.
- [x] M2.5 UI navigation correction: sticky-header-safe anchor and CTA scrolling on desktop and mobile.
- [x] M2.5 navigation and full-screen section alignment: five exact menu destinations, distinct planned-service pages, and desktop section boundaries.
- [x] M2.5 progressive Finding disclosure: one compact complete list with per-Finding expandable evidence and controls.
- [x] M3-A preparation baseline: verified M2.5, staged 8-person qualitative protocol, de-identified observation forms, and scanner-backed synthetic scenarios.
- [x] M4-A Formula Pattern Audit Prototype + Feedback Capture Readiness (internal, default-off prototype only).
- [x] M4-A.5 Formula Audit Quality Gate (synthetic-only; CONDITIONAL GO operating limit recorded).
- [x] M4 Planning Detection Coverage Blueprint (documentation-only; 14 coverage layers, candidate catalog, release gates, and recommended—not approved—next batch).
- [x] M4-A.6 Detection Coverage Blueprint & M4-B Contract (documentation and readiness review).
- [x] M4-B Formula Pattern Audit Internal Beta code and automated verification (separate optional audit API/UI; default-off and server-gated).
- [x] M4-C Formula Pattern Coverage Extension (value-free literal-category normalization, reference subtype correction, and exact 36-target/36-normal synthetic practical corpus gate).
- [x] M4-C quality remediation (summary-marker handling for formulas that reference a `총계` worksheet, synthetic Holdout recovery, and source-fixture ambiguity recorded).
- [x] M4-C final baseline closure: 72/72 engine contract accepted with the explicit, narrow product-owner fixture waiver `M4C-2026-09-02-source-label-conflict`; source labels remain unchanged.
- [x] M4-D Formula Audit Release Candidate & Hosted Beta Readiness: `m4-formula-audit-rc1`, configurable audit limits, safe no-partial-result states, memo-free category feedback, release verification command, support/failure/hosted-beta/manual-review documents.
- [x] Hosted Beta H1 Deployment Foundation & Security Boundary: strict hosted environment/CORS contract, non-root API container, safe liveness/readiness/error/logging contracts, same-origin hosted-beta configuration, deployment/lifecycle/runbook documents, local container rehearsal, and regression verification. No cloud deployment or user upload.
- [ ] Hosted Beta H2 Cloud Deployment, Private Upload Pipeline & Analysis Execution (scope approved but blocked before deployment: no GCP/Cloudflare targets, authenticated credentials, or required CLIs on this PC; no external invitation).

## Current product state

A local user can open the website, run a sample diagnosis, or upload a supported workbook to the local API and receive a static diagnostic result. The result clearly distinguishes confirmed facts, possible impacts, Excel manual checks, normal conditions, action recommendations, unchecked scope, and recommended precision checks. A user can mark local handling status, directly edit a test workbook, re-scan it with the same rules in the current browser session, compare the two results, and download the current result as CSV. It shows only rules-based risk labels and beta price hypotheses; no customer data should be used during development.

M4-B/M4-C keep the two formula-pattern candidate classes default-off and internal-only. When both server gates and the separate browser visibility flag are enabled in a development/internal-beta environment, a user can explicitly re-send the same in-browser file to `POST /v1/formula-audits`. The response is a separate `FormulaAuditResult`; its candidates never enter the basic finding list, risk score, quote, repairability totals, or CSV. M4-C compares supported numeric/text/logical/error literal categories without exposing their values and adds a value-free fixed-reference subtype; unsupported structures remain fail-closed. In internal-beta mode only, the separate audit panel appears before the potentially long free Finding list so a user cannot mistake free-scan counts for formula-audit candidates. `scripts/dev.ps1 -InternalFormulaAudit` enables the required API/browser gates together on an automatically selected isolated port pair from `8010–8090` and `5174–5190`, so an old default stack on `8000` / `5173` cannot intercept the test.

## Not implemented

- Browser-only scan.
- Production R2 upload.
- Database/state machine.
- Real pricing validation.
- Repair engine.
- Payment.
- Authentication.
- Expert workflow.
- Production legal/privacy pages.
- Production deployment.
- Actual user-understanding / conversion-intent sessions and their results (M3 Round 1/2, deferred until hosted beta).
- Hosted paid-value validation (M3.5, deferred until hosted beta).

## Current blocker

M4 is complete as a local Release Candidate, not a hosted release. The combined evaluator confirms 72/72 locations, rules, and subtypes with no unexpected candidates, no non-target normal-range candidates, no clean-control findings, no scan failures, no base-result regressions, and no raw formula/value output fields. The additional pack still contains two target/normal overlaps, accepted only by the documented product-owner fixture waiver; a corrected upstream pack remains recommended. The existing M4-B desktop/mobile capture is a hosted-beta manual gate because this environment has no controllable browser runtime. M3 remains internal-review complete with external validation deferred until hosted beta. No external response, PASS decision, market validation, or paid-value result has been collected or inferred. Actual hosting, automatic repair, payment, calculation, new rule codes, and M5 require separate approval.

## Verification status

Completed locally for the M2.5 Extension on 2026-08-31:

- `scripts/verify.ps1`: frontend Vitest 13 passed and Vite production build passed; API pytest 18 passed and Ruff passed.
- `samples/demo-risky-workbook.xlsx` scanner output regenerated into the frontend JSON fixture and checked by API regression test.
- Component tests cover 0, 1, 2, and 3+ findings, `scan_truncated`, information-only-only, all findings display, local user status, and mixed repairability classes.
- Re-validation tests cover no-longer-detected, continuing, newly-detected, duplicate finding keys, scanner/rule-set mismatch, and truncated comparison warnings. CSV tests check UTF-8 BOM and requested fields.
- Navigation and viewport alignment: the header has five named destinations that each contain a matching title; `진단 시작` and page CTAs move to the upload card. Frontend Vitest 15 passed and the Vite production build passed.
- Progressive Finding disclosure: frontend Vitest 16 passed and Vite production build passed. Tests cover one complete, initially closed Finding list and user expansion.

Manual visual screenshots could not be captured in this environment because no controllable browser runtime was available. Required manual review after starting `scripts/dev.ps1`:

- Visit `http://localhost:5173`, run the sample result at desktop and mobile widths, and verify scope → summary → next actions → findings → re-validation → CSV order.
- Upload only `samples/demo-risky-workbook.xlsx` to the local API and compare it with the generated fixture when intentionally refreshing it.

M3-A preparation on 2026-09-01:

- `scripts/verify.ps1` passed before and after preparation. Final result: frontend Vitest 16, Vite production build, API pytest 20 (including 2 M3 fixture checks), and Ruff. The test runner emitted pre-existing `act(...)` and ZipFile resource warnings but no failed checks.
- `samples/m3/low-or-zero-findings.xlsx` is a reproducible 0-Finding, low-risk synthetic scenario.
- `samples/m3/revalidation-before.xlsx` and `revalidation-after.xlsx` create actual removed, continuing, and new rule signals; their JSON fixtures are regenerated by `scripts/generate_m3_test_scenarios.py` and asserted against a fresh scanner run.
- No participant session, UI change, tracking, payment, repair, or new scanner rule was performed.

M4-A verification on 2026-09-01:

- `scripts/verify.ps1`: frontend Vitest 19 passed, Vite production build passed, API pytest 25 passed, Ruff passed.
- Pattern tests cover function/reference/relative/range pattern outliers; constant and blank gaps; boundaries, summary rows, blank dividers, merged cells, Excel Tables, default-off behavior, truncated scans, stable keys, and value-free evidence.
- Feedback tests cover local-only allowlisted fields, memo limit, clear action, and the disabled-by-default Results UI.
- Existing `act(...)`, Starlette `TestClient`, and ZipFile cleanup warnings remain non-failing known test-environment warnings.

M4-A.5 verification on 2026-09-01:

- `samples/m4-evaluation/` contains reproducible synthetic target, normal-exception, unsupported, truncated, and 1k/10k/30k formula performance assets; `manifest.json` has 40 fixed expectation labels.
- `scripts/evaluate_formula_patterns.py --performance-runs 3`: 24 TP, 0 FP, 0 FN; precision/recall/F1 1.00; normal exceptions, unsupported syntax, truncated scans, key stability, and value-free evidence all passed on this synthetic corpus.
- The same timing run measured M4-to-baseline ratios of 2.545×, 2.510×, and 2.198×. This exceeds the 2× relative-review threshold, so the M4-A.5 recommendation is `CONDITIONAL GO`, not automatic M4-B approval.
- `scripts/verify.ps1` after the changes: frontend Vitest 19 and Vite production build passed; API pytest 27 and Ruff passed. React act and ZipFile cleanup warnings were corrected; Starlette TestClient deprecation remains documented for dependency follow-up.

M4 Planning verification on 2026-09-01:

- `scripts/verify.ps1` baseline passed before documentation work: frontend Vitest 19, Vite production build, API pytest 27, and Ruff. The only warning remains the documented Starlette TestClient deprecation.
- `scripts/evaluate_formula_patterns.py --performance-runs 3` was re-run against the actual scanner: precision 1.00, recall 1.00, decision `CONDITIONAL_GO`. This confirms the existing M4-A.5 result; it does not approve M4-B because the documented relative performance review remains unresolved.
- `docs/26_DETECTION_COVERAGE_BLUEPRINT.md` and `docs/27_DETECTION_RULE_CATALOG.md` add documentation only. No scanner, API, frontend, fixture, configuration, or sample workbook changed; M4 remains default-off and internal-only.

M4-A.6 verification on 2026-09-01:

- `scripts/evaluate_formula_patterns.py --performance-runs 3` passed after the documentation work: precision 1.00, recall 1.00, decision `CONDITIONAL_GO`. It reconfirms the existing synthetic-only M4-A.5 result.
- `scripts/verify.ps1` passed after the documentation work: frontend Vitest 19, Vite production build, API pytest 27, and Ruff. The only warning remains the documented Starlette TestClient deprecation.
- The final M4-A.6 documents only amend product/readiness contracts; no scanner, API, frontend, fixture, configuration, sample workbook, or feature flag changed.
- `docs/28_M4B_PRODUCT_CONTRACT.md` records the required future separation of M4 candidates from baseline findings, risk, quote, repair counts, and default results. `docs/29_M4B_MANUAL_REVIEW_CHECKLIST.md` is intentionally blank and synthetic-only.

M4-B verification on 2026-09-01:

- `scripts/verify.ps1`: frontend Vitest 22 passed, Vite production build passed; API pytest 30 passed and Ruff passed. The only warning is the existing Starlette `TestClient` deprecation.
- API regression tests prove that enabling the internal gate leaves the base finding list, workbook summary, risk score, quote, and limitations unchanged before and after `POST /v1/formula-audits`; M4 candidates are absent from the base list. Failure, unsupported-structure, formula-limit, and truncated-audit outcomes emit no candidates and preserve the base result.
- `scripts/evaluate_formula_patterns.py --performance-runs 3`: synthetic 24 TP / 0 FP / 0 FN, precision/recall/F1 1.00, `CONDITIONAL_GO`. The separate audit path measured average M4/base ratios of 1.771× (1k), 2.158× (10k), and 2.062× (30k), so the relative-cost limit remains documented.
- Local API smoke test on isolated `internal_beta` port 8001: base scan returned no M4 candidates; the optional audit returned `COMPLETED` with only `FORMULA_PATTERN_OUTLIER` and `FORMULA_PATTERN_GAP` on `samples/m4-evaluation/detected-patterns.xlsx`.
- Desktop/mobile browser capture was attempted through the approved browser runtime, but it reported no available browser. No unrelated browser automation was used; responsive component tests and production build passed, while a manual visual capture remains required when a controllable browser is available.

M4-C verification on 2026-09-01:

- `samples/m4c-evaluation/` contains the supplied synthetic 10-workbook practical corpus. The new exact-match regression verifies all 36 labelled target candidates, all 36 normal exceptions, and the clean-control workbook with no unexpected candidate; it also proves M4 remains absent from base findings and that base summary/risk/quote/CSV inputs are unchanged.
- `scripts/evaluate_formula_patterns.py --performance-runs 3`: existing M4-A.5 corpus remains 24 TP / 0 FP / 0 FN with precision/recall/F1 1.00; unsupported and hard-exclusion failures are zero; audit rule-set version is `2026.09.5` while the base rule-set remains `2026.09.4`.

M4-C execution-path recovery on 2026-09-01:

- Reproduced the reported behaviour against the supplied source folder: free scan counts are `0, 0, 49, 0, 0, 0, 0, 0, 0, 0`, while the separate M4 audit returns `4, 4, 4, 4, 4, 4, 4, 4, 4, 0`. The 49 free findings in scenario 03 are existing M0–M2 rules, not M4 candidates.
- The supplied source pack's expected manifest and workbooks are exercised both by the direct corpus gate and `POST /v1/formula-audits` integration test. `scripts/verify-m4c-sample-pack.ps1` prints both count classes separately and requires 36 exact M4 candidates with no extras.
- The internal-beta panel is rendered before the free Finding list, and a frontend test asserts that order after an uploaded file scan. Public/default mode remains unchanged.
- `scripts/dev.ps1 -InternalFormulaAudit` now sets both child-process gates on an actually bindable port pair selected from `8010–8090` / `5174–5190`, including matching CORS/API-base settings. It checks actual socket binding, so a stale/broken default `8000` / `5173` stack cannot be misrepresented as an enabled internal beta.
- The timing run remains `CONDITIONAL_GO` only because the predeclared relative-cost review limit is exceeded: 1k / 10k / 30k added 0.0400s / 0.4848s / 1.3296s, with 2.038x / 2.244x / 2.102x ratios. These are synthetic local measurements, not production performance claims.
- Final `scripts/verify.ps1`: frontend Vitest 22 and Vite production build passed; API pytest 32 and Ruff passed. The only warning remains the documented Starlette `TestClient` deprecation.

M4-C supplemental synthetic-pack remediation on 2026-09-01:

- A second user-supplied, checksum-verified synthetic pack (22 files) exposed a summary-row exclusion defect: matching `총계` inside formula source text caused every formula row that referenced `총계정원장` to be skipped. The exclusion now inspects only static row-label text, never a formula string. A focused regression test covers this exact condition while preserving labelled subtotal/total row exclusion.
- The additional pack now returns its exact 36 target candidates with 0 extras; its Holdout files return 4/4 and 0/0 candidates. Combined with the original pack, the engine returns 72/72 exact labelled candidates and 0 unexpected candidates.
- All non-conflicting labelled normal-exception ranges produce 0 candidate. The additional source manifest itself has two overlapping labels: expected targets `배부계산!E13` and `배부계산!F22` lie inside its own normal ranges `D6:I13` and `D22:I29`. This is a fixture-contract ambiguity, not an engine false positive; do not claim a strict 72-normal-exception gate until the fixture owner corrects those ranges.
- Final `scripts/verify.ps1`: frontend Vitest 23 and Vite production build passed; API pytest 34 and Ruff passed. The only warning remains the documented Starlette `TestClient` deprecation.

M4-D release-candidate closure on 2026-09-02:

- `scripts/evaluate_m4c_all.py --accept-product-owner-fixture-waiver` returned `PASS_WITH_PRODUCT_OWNER_WAIVER`: 20 files, 72/72 location/Rule/subtype matches, 0 unexpected candidates, 0 non-target normal-range candidates, 0 clean-control candidates, 0 scan failures, 0 base-result regressions, and 0 formula/value exposure fields. The only accepted exception is the two immutable target/normal label overlaps recorded as `M4C-2026-09-02-source-label-conflict`; source labels and checksums remain unchanged.
- `scripts/evaluate_formula_patterns.py --performance-runs 3` returned synthetic 24 TP / 0 FP / 0 FN and `CONDITIONAL_GO`; the relative performance limit remains an internal-beta operating constraint.
- Final `scripts/verify.ps1`: frontend Vitest 23 and Vite production build passed; API pytest 35 and Ruff passed. The non-failing Starlette `TestClient` deprecation warning remains documented.
- `docs/32_M4D_RELEASE_CANDIDATE.md` through `docs/36_M4D_FINAL_RELEASE_CANDIDATE_REPORT.md` record the RC contract, safe skip limits, memo-free local feedback, hosted-beta prerequisites, manual synthetic review, and final closure. No deployment or external user validation was performed.
