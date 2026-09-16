# RESELECT-01 — APPROVED (2026-09-16)

Owner resumes exactly one defect: editing the repair selection must retain the same uploaded source/job instead of deleting/remounting/reuploading it. EFFICIENCY-02 applies. BATCH-01 other defects remain stopped.

Single builder scope: App.tsx, components/DeliveryWorkspace.tsx, and narrowly related web tests (new actual App integration test allowed). Preserve all preceding uncommitted BATCH code. No API/paid-scope/preview/type cleanup unrelated to this cause, no new feature.

Acceptance: actual App restart-proposal action returns to selection without delete/create_input; revised submitted selection runs preflight/prepare_plan on the same job_id, clearing old visible plan/approval progression; explicit source deletion and different-file reset remain separate. Exercise the real restart callback/key/mount path, not only isolated component rerender. Retain safe disabled states and no stale async completion can advance an obsolete selection.

Checks: focused real-flow regression + affected type/static check; classify pre-existing BATCH type errors without unrelated fixes. One builder, one focused reviewer; first attempt plus one correction maximum. No full regression/Excel/browser/deploy now; final integrated UI/expected/download validation remains separately confirmed work. Stop after this result for owner confirmation. No remote push. Do not commit whole WIP files that contain unverified prior BATCH work; retain a precise before/after delta for this defect.


## RESELECT-01 checkpoint: targeted tests passed, independent review pending

The real App restart path retains the uploaded job and reruns preflight/prepare_plan for revised selections. Targeted App reselection and adjacent ProposalFlow tests passed (exit 0); the first test harness run failed and was corrected once. Baseline and final builds both failed (exit 2) with the same pre-existing BATCH type errors. No global build PASS is claimed.

Independent reviewer startup and follow-up both returned `agent thread limit reached`. Independent review is NOT completed; do not treat this checkpoint as final acceptance. Existing BATCH work is preserved. No full regression, Excel, actual browser verification, beta deployment, product commit or push was performed. Current-turn delta and command logs are in DigitalTwin/.tmp/workbookcare-reselect01. Next action is independent review of this same defect, not another defect.
