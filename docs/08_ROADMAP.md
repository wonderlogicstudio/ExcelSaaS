# Product roadmap

Each milestone is independently approved. Codex must stop at the end of every milestone.

## M0 — Research and operating system — COMPLETE

Deliverables:

- Product, positioning, UX, architecture, privacy, pricing, and risk specifications.
- `AGENTS.md` and local milestone skill.
- Current market research and sources.

## M1 — Conversion prototype — COMPLETE IN STARTER

Deliverables:

- Responsive Korean landing page.
- Upload interaction and sample-analysis flow.
- Diagnosis, findings, quote-preview, privacy, FAQ, and comparison sections.
- No fake social proof.
- Frontend tests and production build.

Exit criteria:

- A test user understands the service within 5 seconds.
- Primary CTA is obvious.
- Demo result is accessible without backend/account.
- Mobile and desktop layouts are usable.

## M2 — Static scan vertical slice — COMPLETE IN STARTER

Deliverables:

- FastAPI `.xlsx`/`.xlsm` upload endpoint.
- OOXML envelope validation.
- Static workbook rules.
- Risk/complexity score and quote preview.
- Frontend real-upload integration.
- Backend tests.

Exit criteria:

- Synthetic workbook returns deterministic results.
- Macros/external links are never executed.
- Unsupported/unsafe files fail with user-safe codes.
- API unavailability does not break sample demo.

## M2.5 — Service scope and free-to-paid result UX — COMPLETE

Deliverables:

- Current free static-scan scope and non-scope shown before results.
- Evidence-grade labels, rules-based risk-score explanation, and four repairability classifications.
- Finding cards that separate fact, possible impact, unchecked scope, and next precision checks.
- Separate recommendation engine and planned-service catalog with beta price ranges.
- Scanner-generated frontend fixture and edge-case regression tests.
- Repair-readiness path derived from existing repair classes, plus planned approval-based repair and re-validation service definitions.
- Rule-based Action Category and Excel manual-check guides for every current static rule.
- Same-session, same-rule manual re-validation comparison using value-free finding keys.
- Local-only finding handling status and UTF-8 BOM CSV diagnosis export.

M3 remains unapproved until the product owner explicitly approves it.

## M3 — User understanding and paid-conversion intent test — EXTERNAL VALIDATION DEFERRED

Deliverables:

- Test whether users can explain what the free scan did and did not verify.
- Test whether evidence grades, risk labels, repairability, and planned-service wording are understood.
- Test intent to request or pay for a future precision verification without implementing a request form, payment, or third-party tracking.
- Use synthetic sample results and privacy-preserving notes only.

Internal product review and M3-A preparation are complete. External user validation is deferred until a hosted beta is available. M3 is not `PASS` or `Completed`, and no user outcome may be invented in the meantime.

Approval question:

> Do users understand the free result and see a credible reason to consider precision verification?

## M3.5 — Hosted paid-value validation — DEFERRED UNTIL HOSTED BETA

Purpose: validate real hosted feedback, value of concrete paid deliverables, and price/scope hypotheses without treating local interest as payment evidence.

M3.5 does not begin during M4-A. It requires a separate hosted-beta, privacy, feedback-retention, and commercial approval.

## M4 — Formula-pattern precision scans — COMPLETED AS LOCAL RC / HOSTED BETA APPROVAL PENDING

Deliverables:

- Add deterministic formula-pattern consistency checks after a rule-quality review.
- Consider formula drift and hardcoded-override rules only with synthetic corpus, false-positive review, and clear evidence/repair classifications.
- Preserve M2.5 result language: a pattern signal is not a proof of business correctness.
- M4-A is limited to default-off, internal formula-pattern candidates and synthetic false-positive tests. M4-A.5 adds a labelled synthetic quality gate, value-free explanation summaries, local-only manual-review preparation, and performance measurement. Its result remains `CONDITIONAL GO`: accuracy and safety gates pass, while the predeclared relative performance review gate remains an operating limit rather than a general-performance claim.
- M4 Planning (Detection Coverage Blueprint) is complete as a documentation-only follow-up. It records the 14-layer coverage map, rule/evidence-subtype distinction, controlled priority rationale, quality/release gates, and a recommended—not approved—next implementation batch. It does not enable or expose M4 findings.
- M4-A.6 completes the M4-B internal-beta contract, outcome-state separation, baseline-result separation design, performance limit, and synthetic-only manual-review template.
- M4-B implements only the approved internal-beta path: a default-off server gate, a separate optional `FormulaAuditResult`, two approved candidate rule codes, compact evidence cards, category-only local feedback, and baseline-result invariance tests. It does not expose M4 on the default/public site.
- M4-C extends the existing two-rule internal audit only: value-free literal categories in supported expression contexts and precise reference subtype classification. The supplied 10-file synthetic practical corpus is a fixed exact-match gate: 36 targets, 36 normal exceptions, and no unexpected candidates. Internal-beta recovery makes the separate audit explicit before the free Finding list and verifies the supplied pack through the actual audit endpoint; it does not add rule codes, automatic repair, calculation, public exposure, or a basic-scan change.
- The combined, immutable 20-file M4-C evaluator reports 72/72 location, top-level-rule, and subtype matches; 0 unexpected candidates; 0 non-target candidates in labelled normal ranges; 0 scan failures; 0 base-result regressions; and 0 formula/value exposure fields. The product owner accepted the two known source-label overlaps (`배부계산!E13` / `D6:I13`, `배부계산!F22` / `D22:I29`) through a narrow, explicit evaluator waiver; source labels remain unchanged and all other failures still block.
- M4-D delivers `m4-formula-audit-rc1`: settings-based worksheet/formula/candidate limits, no-partial-result skip states, category-only local feedback with legacy memo cleanup, an M4 release command, support and failure contracts, hosted-beta readiness gates, and synthetic-only manual review instructions. No hosted deployment, user file processing, account, payment, repair, or M5 work begins here.

Approval question:

> Can formula-pattern findings be accurate enough to add useful precision without misleading users?

## Hosted Beta H1 — Deployment foundation and security boundary — COMPLETED

Purpose: prepare an invite-only hosted-beta architecture without deploying or accepting user files.

- Separate local, development, internal-beta, hosted-beta, and future production configuration.
- Prepare a non-root Cloud Run container, content-free liveness/readiness contract, safe error/logging boundary, same-origin frontend configuration, and conservative deployment example.
- Fix the required future chain: Cloudflare Access → Worker control plane → private R2 → authenticated Cloud Run → deletion attempt plus lifecycle backstop.
- Document file lifecycle, cleanup failures, access-control, timeout/isolation, cost controls, deploy/rollback, and the human-owned H2 prerequisites.
- Do not create cloud resources, enable `hosted_beta` formula audit, invite users, accept real files, or begin M3/M3.5, repair, payment, M5, AI, or public launch.

Closure update (2026-09-04): H1 local Docker build, non-root liveness/readiness rehearsal, `verify.ps1`, and M4 RC regression verification passed. H2 deployment remains awaiting separate approval.

## M5 — Business-rule validation

Deliverables:

- Define explicit, user-supplied business-rule checks for bounded workbook regions.
- Separate domain assertions from syntax and structural checks.
- Require a reviewable rule definition and evidence output for each business-rule result.

Approval question:

> Can declared business rules be validated without inventing business intent from workbook contents?

## M6 — Calculation engine and file-version comparisons

Deliverables:

- Research a separately sandboxed recalculation approach with no network and disposable storage.
- Compare selected formula outputs or file versions only after safety, fidelity, and privacy approval.
- Do not treat static scanner results as calculation validation.

Approval question:

> Can recalculation and version comparison be performed faithfully and safely enough to support a new service claim?

## M7 — Approval-gated safe repair

- Implement only approved, bounded modifications with an explicit before-change preview.
- Always create a separate output file with a change log and re-scan verification.
- Route macros, unsupported OOXML parts, external systems, or uncertain business intent away from automatic repair.
- Only if M3 validates the need, consider a separate **review-marked copy** before actual repair: keep the original unchanged, add a navigable review list and limited finding-location markers to a separate file, and label every marker as a review signal rather than a confirmed error.
- A review-marked copy must pass its own fidelity gate. It is unavailable for macros, unsupported OOXML/drawings, external-system dependencies, or files whose preservation safety cannot be demonstrated; those files receive location guidance or expert review instead.

Approval question:

> Can approved deterministic changes remain faithful and reversible across supported workbook types?

## M8 — Payment beta

Deliverables:

- Korean web payment provider integration.
- Checkout and webhook state machine.
- Idempotency and reconciliation.
- Refund path.
- Terms/privacy/refund acknowledgement.

Approval question:

> Will real users pay the quoted amount after diagnosis?

## M9 — Expert and automation consultation

Deliverables:

- Expert consultation for uncertain formula logic, fidelity risk, or business rules.
- Automation consultation for repeated manual processes and workbook redesign.
- Separate scope, privacy, communication, and delivery policies after those services are approved.

Approval question:

> Does automation generate profitable, qualified high-value work?

## M10 — Search acquisition

Deliverables:

- Problem-specific landing pages.
- Technical SEO and structured data.
- Synthetic before/after examples.
- Search Console and privacy-safe analytics.
- Content based on actual issue demand.

Approval question:

> Can high-intent organic traffic produce scans and paid repairs?

## M11 — Accounts and history

Only after repeat usage is proven:

- Optional account creation.
- Order history.
- Team workspaces.
- Retention controls.

## M12 — Enterprise/local agent

- On-device scan/repair.
- No-cloud mode.
- Governance reports.
- SSO and admin controls.
- Contractual security review.

## Explicitly deferred

- Native mobile app.
- Full conversational data analyst.
- Arbitrary VBA execution.
- Large multi-workbook model rebuild.
- Subscription-first pricing.
