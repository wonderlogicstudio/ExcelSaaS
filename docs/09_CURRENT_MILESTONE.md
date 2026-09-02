# Current milestone

## Status

`M4 COMPLETED — Formula Audit Release Candidate / Hosted Beta Approval Pending`

The product owner approved M4-C after validating the supplied synthetic practical sample pack. This milestone expands only the supported static formula syntax and the evidence subtype classifier inside the existing, separate `FORMULA_PATTERN_OUTLIER` and `FORMULA_PATTERN_GAP` internal-beta audit. Its acceptance corpus is `samples/m4c-evaluation/`: 36 labelled candidate locations and 36 labelled normal exceptions. The required outcome is the exact 36 labelled candidates with no unexpected candidates or normal-exception candidates; “more findings” is not a pass condition.

M4-C does not change the default-off/internal-only exposure boundary, the separate audit envelope, baseline findings/risk/quote/CSV, public UI, rule codes, calculation policy, repair behaviour, or file-retention policy. The internal-beta execution path is now explicit: `scripts/dev.ps1 -InternalFormulaAudit` enables both gates on an automatically selected isolated local port pair (`8010–8090` / `5174–5190`), leaving any stale default `8000` / `5173` stack irrelevant, and shows the separate audit panel before the potentially long free Finding list.

The integrated final evaluator (`scripts/verify-m4c.ps1`) runs both checksum-verified synthetic packs as one 20-file suite. It returns 72/72 expected locations, 72/72 top-level rules, 72/72 subtypes, 0 unexpected candidates, 0 non-target normal-range candidates, 0 clean-control candidates, 0 scan failures, 0 finding-key instabilities, 0 baseline regressions, and 0 raw formula/value exposure fields. The immutable additional-pack manifest still puts expected targets `배부계산!E13` and `배부계산!F22` inside normal ranges `D6:I13` and `D22:I29`. The product owner explicitly accepted this known answer-sheet defect as the narrow waiver `M4C-2026-09-02-source-label-conflict`; `scripts/verify-m4c.ps1 -AcceptProductOwnerFixtureWaiver` may pass only when every other gate passes. Source labels and checksums remain unchanged.

## Completed M4-D scope

M4-D prepared the current two-rule formula audit as `m4-formula-audit-rc1`: release verification, controlled execution limits, safe result states, a support matrix, failure/observability/retention contracts, category-only local feedback, and synthetic manual-review guidance. It did **not** deploy or host the service, accept actual user files, create a server feedback API or database, collect free-text feedback, introduce an account system, add a detection rule, create a repair, payment, or start M5.

The product owner approved M4-B after the M4-A.5 `CONDITIONAL GO`, M4-A.6 Blueprint/Product Contract, and reported completion of five representative synthetic manual checks. M4-B code implementation and automated verification are complete: a separate, opt-in `FormulaAuditResult`, default-off server gate, internal-only UI, candidate evidence cards, and baseline-invariance tests. Desktop/mobile capture remains pending because this environment has no controllable browser runtime. The M4-A engine retains its synthetic accuracy, normal-exception, evidence, privacy, stability, and no-regression checks; the separate audit path's relative time cost remains an explicit documented operating limit.

M2.5 remains the verified product baseline. Its compact one-list Finding UI, scope boundaries, evidence grades, repairability classifications, same-session re-validation, and CSV export remain the default experience and must not show M4 findings.

## M3 and M3.5 status

- **M3:** `Internal Product Review Completed — External User Validation Deferred Until Hosted Beta`
- **M3.5:** `Deferred Until Hosted Beta`

Neither status is a PASS, market validation, price validation, payment signal, or completed user study.

## Completed M4-A.5 scope

1. A reproducible synthetic workbook corpus and fixed expected labels for the two existing M4-A rule classes.
2. An evaluator that runs the actual scanner, reports synthetic-only quality metrics, repeat key stability, privacy-safe output, and small/medium/large timing.
3. Optional value-free structural summaries derived from existing M4-A evidence; unknown subtype remains generic and unpublished.
4. A local-only, ignored manual-review preparation path that writes no filename, sheet, cell, finding key, value, or formula to its output.
5. Minimal warning and performance corrections without expanding detection scope.

## Completed M4 Planning scope

1. `docs/26_DETECTION_COVERAGE_BLUEPRINT.md`: 14-layer long-term detection map, controlled prioritization, prerequisites, quality gates, M4-B exposure boundary, and recommended next batch.
2. `docs/27_DETECTION_RULE_CATALOG.md`: candidate-level purpose, method, context, evidence, exception, risk, actionability, repair, priority, gate, implementation, and exposure metadata.
3. Separation of independent `rule_code` from evidence subtype, engine status from quality-gate status from user exposure status, and recommendation from implementation approval.

## Completed M4-A.6 scope

1. Amend the existing Detection Coverage Blueprint and Rule Catalog; do not recreate them or implement their candidates.
2. Create the M4-B internal-beta product/API/readiness contract and a blank synthetic-only manual review checklist.
3. Document the current structural gap: M4 candidates are collected with baseline findings today, so M4-B later needs a separate optional audit envelope that cannot affect baseline findings, summary, risk, quote, repair counts, or default Results.
4. Record execution outcomes (`ABSTAIN`, insufficient evidence, unsupported structure, truncated, failed) separately from rule lifecycle, quality, and exposure status.
5. Review UI/API extensibility and propose only the minimum future-compatible change; do not implement it in M4-A.6.

## Completed M4-B scope

1. Add a server-gated, separate optional formula-audit API/result envelope and an internal-beta-only UI entry point.
2. Permit only `FORMULA_PATTERN_OUTLIER` and `FORMULA_PATTERN_GAP`; show no generic drift, unsupported syntax, calculation, business-context, or new-rule findings.
3. Require a completed non-truncated base diagnosis, 1–30,000 formula cells, and a same-browser re-upload; retain no file on the server.
4. Provide only indeterminate “analyzing” UI, explicit execution outcomes, evidence, Excel confirmation guidance, local handling state, and category-only local feedback.
5. Add regression coverage proving the baseline findings, summary, risk, quote, and CSV are unchanged before/after an audit request, including audit failure/abstention/unsupported cases.
6. Verify the internal-beta UI at defined desktop and mobile widths with synthetic fixtures and save captures under `artifacts/screenshots/` when the local browser runtime is available.

## Completed M4-C scope

1. Added the supplied synthetic practical corpus as `samples/m4c-evaluation/`: 36 target candidates, 36 normal exceptions, and one clean-control workbook.
2. Expanded only the existing M4 normalizer to compare supported numeric, text, logical, and error literal categories without preserving literal values; direct static `SUM`/`AVERAGE` operands remain intentionally unsupported.
3. Corrected structural subtype classification: internal `REF` markers no longer appear as functions, changed fixed reference locations use `REFERENCE_CELL_DRIFT`, and a range subtype is emitted only when the changed reference is a range.
4. Preserved the two existing rule codes, default-off/internal-only server boundary, and separated `FormulaAuditResult` envelope. The base scan stays at rule-set `2026.09.4`; the isolated audit reports `2026.09.5`.
5. Added exact target/normal-exception/base-invariance regression coverage and value-free literal handling coverage.
6. Recovered the internal-beta test path after observing that a default free scan could be mistaken for M4-C output: the exact supplied sample pack is now exercised through the API endpoint, a developer command reports free-scan and audit counts separately, and the internal audit is placed before the free Finding list only when the internal-beta browser flag is enabled.
7. Corrected a summary-row exclusion defect exposed by a second supplied synthetic pack: a marker such as `총계` inside a formula's referenced sheet name can no longer exclude its data row. Static row labels remain the only marker source for this exclusion. The regression is covered without adding a new rule code or changing the base scan.
8. The second supplied synthetic pack now returns all 36 exact target candidates, including its 4/4 Holdout result, with no unexpected candidates. Its source manifest has two target/normal range overlaps (`배부계산!E13` and `F22`); these are recorded as source-fixture ambiguities rather than product false positives and must be corrected in the fixture before it becomes a strict automated normal-exception gate.

## Required boundaries

- `formula_pattern_audit_enabled=false` remains the default. The server gate must additionally restrict access to development/internal-beta environments; a browser visibility flag is not an access-control boundary.
- Do not expose the M4 entry point on the public/default site, mix its candidates into free Results, alter baseline risk/quote/CSV, add repair/XLSX output/payment/account/DB/feedback API/cloud/AI/calculation/business-rule work, or start M5. The internal-beta panel may be positioned ahead of the free Finding list solely to make the separate execution step discoverable. The Blueprint's next-batch recommendation is not implementation approval.
- A pattern candidate is not a confirmed formula error, a business-correctness verdict, or a suggested replacement formula.
- Do not represent candidates as confirmed formula errors, correct formulas, automatic repairs, generated repaired workbooks, or incorrect calculation results.

## Stop condition

M4 is complete as a local release candidate. M4-C is accepted as `Completed with Product Owner Fixture Waiver`; the known answer-sheet conflict remains visible in the release record. `scripts/verify-m4-release.ps1 -AcceptProductOwnerFixtureWaiver`, the M4-D documentation, and the synthetic manual RC checklist are complete. Do not begin actual hosted deployment, M5, automatic repair, payment, calculation, AI, or public exposure changes without a new approval.
