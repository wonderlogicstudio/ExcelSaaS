# STOPPED — Core product flow / IA owner review

2026-09-13 승인된 IA 후속 구현·전체 회귀·실제 보호 베타 화면/예상 값·다운로드/Excel 검증 완료. [17항목 review](delivery-v3_2/reviews/CORE_FLOW.md), [사용자 확인 행동](delivery-v3_2/owner_action.md). IA ENGINEERING_VERIFIED_AWAITING_OWNER, D08 전체 PARTIAL. 다음 한 단위는 일반 사용자용 지원 범위 → 의뢰 범위·견적 연결 제안만; D09/다음 단위 자동 실행 금지. 아래 ACTIVE/STOPPED 항목은 역사 기록이다.

---

# ACTIVE APPROVED — Core product flow / IA follow-up

Latest owner attachment approves implementation of the main diagnosis-to-approval delivery flow and separate precision/comparison/automation pages. Scope and acceptance: [51_CORE_PRODUCT_FLOW.md](51_CORE_PRODUCT_FLOW.md). Existing beta deployment authorization applies; no remote push, new commerce, engine, rules or resources. Preserve all prior records and fixed expected inputs. Complete actual beta UI + full regression, selective local commit and stop. Historical milestones below are preserved.

---

# STOPPED AFTER D08 — complex synthetic acceptance verified

2026-09-13 owner-requested complex synthetic follow-up complete: seven XLSX inputs/two CSVs/frozen independent expected workbook+JSON; local12 regression cases and actual Access-beta13 screen checks,13 downloads,8 downloaded XLSX reopened in installed Excel. Full web78/Worker16/API231/M4exact36 exit0. Only fixed synthetic allowlists changed; private API00014-nah, unchanged Worker521ad0aa/Gateway. See delivery-v3_2/reviews/D08.md and owner_action.md. D08 overall PARTIAL: PG/durable commerce/concurrency/all combined limits/commercial gates remain. No D09, remote push or automatic next unit. Next proposed single unit: bounded concurrent-request/cancellation/retry verification with these fixed inputs. Older ACTIVE/STOPPED headings below are historical.

---

# ACTIVE APPROVED — D08 complex synthetic acceptance follow-up

2026-09-13 latest owner request: create substantially more complex synthetic workbooks and independent expected results, then test before commercialization. This is an additional bounded D08 validation unit, not D09 or a feature-scope expansion. Freeze cases/oracles before product execution; include supported dependency chains and partial approval, normal exceptions, realistic unsupported structures and comparison boundaries. Test actual protected beta UI and downloaded XLSX in installed Excel. Fix demonstrated defects within existing capabilities, preserve exclusions, baseline evidence, customer approval and payment OFF. Existing beta deployment authorization applies to verified fixes/registered synthetic hashes only. No remote push, real data/payment/refund, pricing or new paid resource. Record actual commands/exits/failures/limits in D08 review, owner actions and progress; select local commit and stop after this unit.

Baseline: main51d4377, existing full API219/Worker16/M4exact36 and latest web78 pass evidence preserved; rerun relevant baseline and affected tests. Previous stopped/active headings below are historical.

---

# STOPPED AFTER D08 — protected beta verified / owner review pending

2026-09-13: Approved D02–D08 beta deployment and actual hosted synthetic acceptance completed. Worker521ad0aa / private API00011-bav. D08 overall PARTIAL: official PG, durable commerce, combined capacity/deadlines and commercial/owner release gates remain. PAYMENT_MODE OFF; no D09, push or anonymous release. Existing lower ACTIVE headings are historical only. See reviews/D08.md, release_manifest.json and owner_action.md. Next proposed single unit: official PG sandbox verification after owner prepares test account/keys.

---

이하 이전 기록은 당시 상태로 보존합니다. 최신 판정은 위 기록입니다.

# Current milestone

## ACTIVE APPROVED — D02–D08 existing protected beta deployment (2026-09-13)

Latest owner instruction: deploy to the existing Access beta and start actual site validation. This supersedes the previous deployment stop only for this unit; no D09 or remote Git push. Reuse local passing evidence, package the Linux Java/POI and report runtime, verify fixed synthetic expected values in the authenticated browser and downloaded Excel files. Official PG account/keys are not prepared (owner confirmed); keep PAYMENT_MODE=OFF and label fixed-synthetic rehearsal separately from payment. Keep default-off hosted rehearsal, exact approval, private owner/HMAC/IAM/R2/KV, no real customer input or new paid resources. Docker/Desktop/WSL restart is not authorized. Record failures, fixes, actual checks and unresolved release criteria; do not claim D08 commercial completion.


## STOPPED AFTER D08 — 사용자 확인 대기 (2026-09-13)

D01–D08 승인 범위의 로컬 구현·실제 화면·Excel 검증을 마쳤다. 전체 판정 PARTIAL: D02 이후 beta/Linux/PG/상용 운영의 필수 미완료 증거를 release_manifest.json에 분리했다. 다음 묶음 자동 실행 금지. 원격 push·일반 공개·상용 판매 없음. 다음 한 단위 제안은 기존 Access 베타 납품 배포와 실제 사이트 예상 값 확인이며, Docker 복구와 Linux 패키징/한도를 먼저 해결해야 한다. 이전 ACTIVE 제목은 아래 역사 기록으로만 보존한다.


## ACTIVE APPROVED — D08 (2026-09-13)

D07 local UI/TTL/private access/child reports/recovery verified. Hosted/Linux/PG and commercial policy remain PARTIAL. Read 07_ACCEPTANCE_AND_RELEASE.md and 02_CUSTOMER_OUTPUTS.md. Run new immutable synthetic holdouts through actual UI/API/engine/artifacts, inspect expected on-screen values and installed Excel, add missing negative acceptance, and produce SKU-specific release_manifest. Do not convert NOT_RUN to PASS. Final owner review and stop after D08; no new milestone, remote push, real payment, prices, paid resources or anonymous release.


## ACTIVE APPROVED — D07 (2026-09-13)

D06 local order/separate approval/recovery and actual UI/download/Excel verified; official PG sandbox/SDK and hosted/Linux remain PARTIAL. Read SECURITY_OPERATIONS.md and UX_AND_MENU.md. Reuse existing gates and strengthen UX, TTL, private access, cancellation, resource limits and operating evidence. Latest D01–D08 authorization applies; final owner review after D08. No live payment, remote push, prices, new paid resources or anonymous release.


## ACTIVE APPROVED — D06 (2026-09-13)

D05 actual comparison UI/child engine/two reports and installed Excel verified. D02–D05 hosted/Linux remain pending Docker recovery; no commercial readiness.
Read PAYMENT_APPROVAL_DELIVERY.md and 02_CUSTOMER_OUTPUTS.md. Reuse owner/job/approval/fenced artifacts. Implement missing payment ledger/sandbox adapter/recovery and reconnect; official PG credentials missing means NOT_RUN, never substitute mocks as PG evidence.
Latest D01–D08 authorization applies; final owner review after D08. No remote push/live payment/price decision/new paid resources/public release.


## ACTIVE APPROVED — D05 (2026-09-13)

D04 local exact approval, real separate repair + three artifacts, desktop/mobile UI and installed Excel reopens verified. Hosted D02–D04 and Linux container remain pending Docker recovery; no commerce release.
Read contracts/COMPARISON_AND_BUSINESS.md and reference/v31_contracts/INPUT_ENGINE.md. Reuse existing comparison behavior; implement missing exact text-key / integer KRW report path. B remains another observation, never automatic truth or overwrite. Comparison entitlement must not allow repair.
Latest D01–D08 authorization applies; final owner review after D08. Preserve prior records and pending deployment.


## ACTIVE APPROVED — D04 (2026-09-13)

D03 local actual POI/Excel/desktop/mobile expectations and full regression pass. Hosted D02/D03 release remains pending Docker recovery. No commercial readiness inferred.
Read PATCH_AND_VALIDATION.md and 02_CUSTOMER_OUTPUTS.md. Implement minimal OOXML patch to a separate copy, actual post-calculation/preservation verification, atomic three-file delivery and cancellation/retry fence. Use internal synthetic grants only; no public test bypass.
Latest D01–D08 authorization applies. Preserve prior evidence and pending release work.


## ACTIVE APPROVED — D03 (2026-09-13)

D02 input/preflight actual local desktop/mobile expected values and full regression pass. D02 hosted deployment is explicitly pending local Docker recovery, not reported as verified.
D03: isolated bounded formula evaluator, RP01/RP02 exact proposals, Excel reference and canonical immutable plans. Read CALCULATION_AND_PLAN + REPAIR_ELIGIBILITY. No purchase/execution based on business confirmation; no outputs until D04.
Latest owner D01–D08 authorization applies; preserve all prior records and pending beta release work.


## ACTIVE APPROVED — D02 (2026-09-13)

D01 hierarchy implementation/regression and local/hosted screen expectations passed; see D01-hierarchy.json.
Proceed with D02 immutable single-file inputs, owner binding, exact profile selection and fail-closed preflight.
Read contracts/REPAIR_ELIGIBILITY.md and contracts/SECURITY_OPERATIONS.md. Reuse existing Access/HMAC/file validation.
D03 calculation evidence absent means preliminary only, no repair quote/sale. Latest D01–D08 authorization below applies.


## APPROVED — D01 hierarchy refinement and D02–D08 execution (2026-09-13)

Latest owner instruction approves summary → type groups → cell evidence, then development through D08.
Proceed sequentially only after the current unit's implementation, targeted/regression tests and actual UI checks.
Compare available synthetic expected values on the real screen; record mismatches and repair them before advancing.
Owner review is deferred until the requested sequence is finished. This latest instruction supersedes prior D01-only/
per-bundle stop instructions for development, not customer change approval or commercial/production readiness.
Use existing code/evidence and preserve owner work, history, original fixtures/waivers, free CSV/score and security.
Deploy verified units to the existing Access-protected beta under standing authorization; no remote Git push,
real customer data/payment/refund, price decisions, new paid resources, anonymous release or user invitations.
Unavailable Excel-reference/official PG sandbox evidence remains NOT_RUN and gates live repair/payment readiness;
finish independent authorized engineering instead of replacing actual evidence with package mocks.
Work order: D01 UX, D02, D03, D04, D05, D06, D07, D08; stop after D08. Do not claim market leadership as verified.

## Unified diagnosis UX completed — 2026-09-13 (KST)

Owner-approved D01 single upload/progress/list implemented and deployed to protected beta.
Combined UI: case03=53 (49 structure+4 formula),11=63,01=4,controls10/20=0.
Source categories, groups/full table/filters/keyboard/mobile/handling preserved; base score/quote/CSV/revalidation unchanged.
Final verify.ps1 exit0: web73/Worker14/API77, TypeScript/build/Ruff/main pack36.
Actual local desktop20/mobile4:72 exact,6 screenshots visually reviewed; actual authenticated hosted representative5:12 exact.
Prior all20 hosted/container72 evidence reused, not claimed rerun. Existing strict2 label conflicts/waiver unchanged.
Source `d64c45178cf1`; Worker `f9be71f3-d035-48cb-b9a9-7fcaa1e7469a`100%; all13 bindings/Access unchanged; no API/Gateway rollout.
Owner83/sample68 hashes unchanged. No Excel/PG/repair delivery,paid resource,remote push,H2/H3 completion or D02 execution.
D01 ENGINEERING_VERIFIED_AWAITING_OWNER: engineering acceptance done, final owner acceptance pending. Stop after D01.
See `delivery-v3_2/reviews/D01.md` and `delivery-v3_2/reviews/evidence/D01-unified-diagnosis.json`. Prior records preserved below.

## APPROVED — D01 unified diagnosis UX follow-up (2026-09-12)

The owner explicitly approved one upload/progress/result list for structure and M4 findings.
Integrate the existing hosted beta results and filters/table/handling; label each finding source.
Keep underlying API envelopes, original keys, free score/quote/CSV/revalidation semantics,
M4 uncertainty, limits, security/feedback gates, source fixtures and prior records intact.
No engine/new rule/payment/repair/infrastructure redesign. Deploy the verified web to the same
protected beta under standing authorization; verify actual synthetic desktop/mobile flows.
The prior D01 acceptance has engineering evidence. This is its remaining known UX correction;
after passing checks, record ENGINEERING_VERIFIED_AWAITING_OWNER, not owner acceptance.
No D02, remote push, H2/H3 completion, new paid resources or real customer data.

## Protected beta M4 follow-up completed — 2026-09-12

The approved expected-results connection is deployed and agent-verified on the actual authenticated beta:
20 unique synthetic uploads,72/72 exact sheet/cell/rule/subtype,no extras; controls10/20 zero.
Free counts03=49/11=59/others0, grouped locations,score/CSV and approval separation are preserved.
Existing engine reused; automatic separate M4, gated API/Worker/Gateway connection and mobile layout repaired.
Final full regression exit0:web69/Worker14/API77,TypeScript/build/Ruff; actual container72 and local UI72 pass.
Strict evaluator remains BLOCKED solely by existing case18 E13/F22 target/normal label conflicts; existing waiver accepted,
no fixture/threshold/waiver edits. Source `0ae6c63c06a7`. Worker `c222ac45-36ab-48c0-a0b1-e0d66f4755d8`,
Cloud Run `workbookcare-api-beta-00004-hhk`, Gateway `workbookcare-beta-m4-0ae6c63c06a7`; Access/IAM/private storage preserved.
Evidence: `delivery-v3_2/reviews/evidence/D01-m4-hosted.json` and `D01-m4-hosted-browser.json`.
Owner83/sample68 hashes unchanged. No Excel/PG/repair delivery,paid resource,remote push,H2/H3 completion or D02 execution.
D01 engineering verified,owner acceptance pending; stop here. Earlier M4-disabled/pending notes are historical.

## Approved follow-up — M4 expected results on protected beta (2026-09-12)

The owner explicitly requested that uploading the supplied Workbook samples
produce their expected findings on the existing beta, after the missing M4
connection was explained. This approves the bounded existing M4 connection and
automatic audit after a supported synthetic upload. Supersedes prior hosted M4
disabled/pending-approval statements only for this Access-protected beta.
Reuse the existing M4 engine, preserve free result/score/CSV and separate M4 output.
Connect the current Worker, Gateway and private Cloud Run service; deploy only
verified components under the standing beta authorization. Production/anonymous
M4 stays off; Access, HMAC, IAM, private R2 cleanup, limits and feedback gates stay.
Do not alter expected labels or the existing two-conflict waiver. Verify all20
unique fixtures against expected locations/rules/subtypes through the actual site.
D02, payments, repair execution, new paid services and Git push remain unapproved.

## D01 authenticated hosted sample verification — 2026-09-12

The connected, logged-in Chrome beta was exercised by the agent using actual
synthetic uploads: all 20 unique Workbook samples plus demo, 21/21 free results
matching local counts and scanned-cell/formula metadata. Case03: 49 deep-nesting
findings, one collapsed group; case11: 59 volatile-function findings, one collapsed
group. All 49/59 locations are retained; case11 full table retains 59 rows. The other
18 samples return free0; demo returns12. Zero screens clearly show M4 not performed.
The supplied M4 expected72 are NOT verified on the hosted site: hosted M4 remains
unavailable/disabled. This is a product-scope/connection gap, not evidence that the
M4 expected findings passed. Browser setup does not approve M4 activation.
No source/deployment/gate changes; prior full regression web63/Worker13/API75 is
reused, not rerun. Owner83 hashes and tracked samples preserved. Actual browser
actions, results, recovered chooser failure and limits are recorded in
`delivery-v3_2/reviews/evidence/D01-hosted-browser.json`. Earlier pending-browser
notes below are historical. D01 owner acceptance, H2/H3 readiness and D02 gate stay unchanged.

> **D01 owner-feedback grouping fix — deployed 2026-09-12.**
> Owner confirms beta case03 free49; local actual API agrees. Same-rule results
> now start as one collapsed group; all locations/evidence/status/CSV retained.
> Source `5828aca`, beta `673f2895-2142-4215-8024-9acb14fa53ae` 100%.
> Full web63/Worker13/API75, actual browser1440/390, synthetic pack M4 72/72
> with existing two-label waiver passed. Post-fix hosted UI awaits owner review.
> Access/storage/API/M4 gates unchanged. See latest D01 review/evidence.
> D01 only; no D02 activation, remote push or further milestone. Prior records
> and standing beta deployment approval below remain preserved.

> **D01 owner-feedback follow-up — 2026-09-12: zero-result scope clarification deployed.**
> Owner identified M4 test files. Free scan and unperformed separate formula
> validation are now explicit; partial/empty zero states are differentiated.
> Source `207e09c`, beta version `dc94d91a-e969-479e-9087-f1f9758ec2ef` at 100%.
> Verified web 61 / Worker 13 / API 75, hosted build, local API/browser 0/12 controls.
> M4 hosted remains disabled; authenticated hosted all-files-zero report is not
> independently reproduced. D01 review/evidence records this distinction.
> No further bundle is approved; standing protected-beta deployment approval remains.

> **Latest owner authorization — 2026-09-12: continuing deployment to the existing protected beta is APPROVED.**
> Target: `https://workbookcare-beta.wonderlogic-studio.workers.dev/`.
> After verification of each separately approved development unit, deploy its
> completed changes to this same beta through project completion without asking
> for the same beta deployment approval again. Keep Access, private storage,
> authenticated API, M4/feedback gates and synthetic-only testing boundaries.
> This supersedes earlier beta deployment prohibitions below, but does not start
> D02 or authorize remote Git push, anonymous release, new paid resources, real
> data/payments/refunds, pricing approval, or closure of H2/H3 outstanding gates.
> D01 WEB DEPLOYED: version `9748b413-0acd-4a57-a0fd-9a5e3324f3db`, 100%,
> 2026-09-12 11:40:40 UTC. Cloud Run API revision was not changed; the web build
> supports its older additive response shape. Login-session UI review remains pending.
> Standing workflow: `50_BETA_RELEASE_WORKFLOW.md`. D01 engineering acceptance
> remains awaiting owner review; the next development bundle is not authorized.

> **Current authorization (2026-09-12): V3.2 D01 ONLY — APPROVED / ENGINEERING_VERIFIED_AWAITING_OWNER.**
> The owner selected `docs/delivery-v3_2/bundles/D01.md`: product/deliverable
> boundaries and integration with existing free diagnosis. Follow its working
> rules, product scope and UX contract. Reuse current code and actual evidence;
> missing L01–L08/CF/UXR implementations must not be assumed complete.
> Preserve prior progress/reviews below. Implement only missing D01 acceptance,
> run targeted and relevant integration checks, record review/owner actions and
> a delivery-progress delta, selectively commit locally, then STOP.
> No remote push, deployment, cloud changes, real data/payments/refunds, price
> approval, actual repair/calculation/PG or next bundle is authorized. Diagnosis
> handling, purchase entitlement and exact change approval remain separate.
> Final verification: web 59 / Worker 13 / API 75, build/Ruff/M4-C 36 exact,
> actual local synthetic browser/API at 1440/390 and reviewed screenshots passed.
> Review: `delivery-v3_2/reviews/D01.md`. Owner actions and delivery-progress are
> in that folder. Source commit: `40e2e8998beef87cb844c1fc400f1e75eced2fa1`.
> D02 is recommendation only. Stop after selective LOCAL commits.
> Earlier milestone push/deployment permissions below do not apply to this task.

> **Current product scope (2026-09-12): Product P2 — Re-validation location details is APPROVED; implementation and automated verification passed, visual review is pending.**
> The owner's new instruction authorizes a bounded next product improvement,
> full local regression verification, commit, and GitHub synchronization. This
> supersedes P1's instruction to stop before a next product slice only for P2.
> P2 presents existing comparison findings by title, rule, sheet, and cell in
> three expandable groups, with previous/current location labels and explicit
> comparison limits. It does not change comparison semantics or analysis.
> Contract: `49_PRODUCT_P2_REVALIDATION_LOCATIONS.md`. Required checks:
> `scripts/verify.ps1` and local synthetic desktop/mobile interaction review.
> Full local verification passed: web 43, Worker 13, API 72, TypeScript/build,
> Ruff, and 36 exact M4-C supplied-pack candidates with no extras. Seven new
> behavior tests cover the details, warnings, filter/CSV invariance and sample loop.
> Windows computer-use stopped because it could not determine the current browser
> URL confidently enough to enforce policy. No real-browser verification or
> screenshots are claimed; follow-up is recorded in `MILESTONE_REVIEW.md`.
> P1's visual acceptance is still pending and is not inferred from P2 approval.
> H2/H3 operational checks, cloud access/deployment, public Formula Audit or
> feedback, real files, M3/M3.5/M5, repair, payment, accounts, calculation, and
> AI remain outside this task. Stop after the P2 review/commit/GitHub sync.

> **Previous product scope (2026-09-10): Product P1 — Free-result navigation is APPROVED; implementation and automated verification passed, visual review is pending.**
> The owner's current instruction authorizes a bounded next product improvement,
> local regression verification, commit, and GitHub synchronization. P1 adds only
> in-memory severity/sheet/handling-status filters to the existing free Finding
> list, an explicit priority shortcut, match counts, reset, and safe empty states.
> Acceptance: combine filters; preserve full scan summary, quote, CSV and local
> statuses; reset filters for a new scan; keep keyboard/mobile operation usable;
> pass `scripts/verify.ps1` and exercise the synthetic sample flow.
>
> H2/H3 operational work continues separately. Do not resume its remaining
> verification, inspect live cloud resources, deploy, enable public Formula Audit
> or feedback, invite users, process real files, or start M3/M3.5/M5, repair,
> payment, accounts, calculation, or AI. The existing Hosted Beta NOT READY status
> and its unresolved gates remain unchanged. Scope and rationale:
> [`48_PRODUCT_P1_RESULT_NAVIGATION.md`](48_PRODUCT_P1_RESULT_NAVIGATION.md).
> Full local verification passed: web 36, Worker 13, API 72, TypeScript/build,
> Ruff, and the supplied M4-C pack (36 exact candidates, no extras). The connected
> computer-use runtime reports no browsers, so desktop/mobile visual acceptance
> is pending rather than claimed. Review: `MILESTONE_REVIEW.md`. Stop after the
> authorized commit/GitHub synchronization; do not advance to another milestone.

> **Separate operational scope (2026-09-09): Hosted Beta H3 is APPROVED and IN PROGRESS.**
> H3 hardens the already-deployed, synthetic-only hosted beta before any external
> invitation. It may add privacy-safe operations, protected category-only feedback
> persistence, public beta notices, safe-error and monitoring contracts, final
> synthetic verification, and rollback/go-no-go materials. It must not invite or
> contact external users, process a real workbook, start M3/M3.5/M5, expose the
> Formula Audit publicly, add account/payment/repair/AI capability, or weaken the
> Access, private-R2, Gateway, or non-anonymous Cloud Run boundaries.
>
> **H2 dependency retained:** H2's deployed infrastructure is a prerequisite, but
> its observed one-day R2 lifecycle expiration remains open. The owner-session
> HMAC-negative confirmation passed and its temporary route was removed. H3 may
> implement and verify its own controls, but it cannot receive a Hosted Beta Ready
> verdict until the lifecycle gate is evidenced.
> The authoritative H3 scope, additions, and acceptance gates are in
> [`44_HOSTED_BETA_H3_OPERATIONAL_HARDENING.md`](44_HOSTED_BETA_H3_OPERATIONAL_HARDENING.md).

> **Current H2 implementation status:** provider secrets, the existing Cloud Run
> service's H2 revision, Gateway, and Access-protected Worker are deployed.
> A browser upload exposed a Gateway path-translation defect (backend `POST /`
> instead of `/v1/scans`). Its correction is deployed and the Gateway is ACTIVE.
> An authenticated synthetic upload completed with an analysis result (Cloud Run
> `POST /v1/scans` 200), and a deliberately malformed synthetic `.xlsx` was
> rejected (415); after each request R2 returned to zero objects/zero bytes. H2
> has an authenticated-session rate limit of five uploads per minute, and the
> existing KRW 10,000 budget alerts are visible at 50%, 90%, and 100%. Browser
> CSV download has been reported successful. The product owner also completed
> browser re-validation of the synthetic comparison, whose summary changed from
> `3/3` to `2/1`. The direct-Gateway HMAC-negative verification using a valid
> Access assertion passed, and its temporary Worker route was removed. H2 still
> awaits observation of the remote lifecycle probe's one-day expiration (created
> 2026-09-09 12:37 UTC). See
> `42_HOSTED_BETA_H2_PREFLIGHT.md`.

> **Active scope override (2026-09-08): COMPLETED (2026-09-09) — Cloud Run preparation only; STOPPED BEFORE DEPLOYMENT.**
> The current owner instruction narrows work to the existing FastAPI API container,
> privacy/temporary-upload review, local container rehearsal, and full regression
> verification. No Google Cloud resources, frontend deployment, Cloudflare/R2,
> authentication features, signup, payment, or repair are authorized in this step.
> Earlier H2 deployment approval/preflight below is historical and does not authorize
> resuming deployment now. Stop after the preparation review.

> **Status override (2026-09-04): `H2 BLOCKED — awaiting dedicated cloud targets, operator credentials, and H2 authentication configuration`.** The product owner approved H2 scope, but this PC has neither the required deployment CLIs nor authenticated Cloudflare/Google Cloud targets. H2 must not bypass this with an anonymous Cloud Run service or a long-lived Google service-account key in Cloudflare.

## Approved H2 scope

H2 implements the private hosted-beta upload/control plane, Cloud Run analysis execution, deletion and lifecycle controls, and synthetic end-to-end/security-negative validation. The browser remains same-origin and Access-protected. A Cloudflare Worker validates the Access application token and forwards it to Google API Gateway, which validates the exact Cloudflare JWT issuer/audience and invokes Cloud Run through its own least-privilege service account. The Worker additionally signs the internal analysis request with a short-lived HMAC shared only through provider secret stores. This preserves no-anonymous Cloud Run and prevents a user from bypassing the Worker via the API Gateway.

H2 must keep R2 private with opaque keys, avoid filename metadata, preserve all existing static-scan limits, use only synthetic workbooks for deployment verification, clean up each object on every terminal path, and retain the lifecycle backstop. It must not add a public account/dashboard, payment, repair, new rules, calculation, AI, VBA, Power Query, M3/M3.5 user sessions, or H3 hardening features.

The approved implementation route is documented in `docs/42_HOSTED_BETA_H2_PREFLIGHT.md`: Cloudflare Access JWT validation in the Worker, the same exact issuer/audience validation in Google API Gateway, an API-Gateway-only Cloud Run Invoker service account, and a separate short-lived Worker HMAC signature checked by FastAPI. H2 resumes only after its named prerequisites are supplied.

## Status

`HOSTED BETA H2 IN PROGRESS — synthetic-only; deployment and verification gates remain open`

`HOSTED BETA H1 COMPLETED — H2 Deployment Awaiting Product Owner Approval`

## Completed H1 scope

H1 prepares an invite-only hosted-beta foundation without deploying it. It may add environment separation, production container/readiness preparation, same-origin frontend configuration, safe logging/error contracts, file-lifecycle/timeout/access-control architecture, deployment and rollback guidance, and tests for those contracts. It does **not** create Cloudflare, R2, Google Cloud, Cloud Run, Artifact Registry, Secret Manager, domain, account, bucket, user upload, session, database, analytics, payment, repair, M3/M3.5 study, M5 rule, AI, VBA, or Power Query capability.

The H1 architecture boundary is Cloudflare Access-protected beta hostname → Worker control plane → private R2 → authenticated Cloud Run. The browser must use same-origin `/api`, never a Cloud Run URL; Cloud Run must not gain an anonymous invoker as a shortcut. Formula audit remains default-off and unavailable in `hosted_beta` until the entire access path is separately verified in H2.

H1 must preserve every M4 RC behavior and finish with a documented local container rehearsal outcome. If Docker or a required cloud account is unavailable, record the exact manual prerequisite; do not claim a cloud deployment or container test that did not occur.

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
