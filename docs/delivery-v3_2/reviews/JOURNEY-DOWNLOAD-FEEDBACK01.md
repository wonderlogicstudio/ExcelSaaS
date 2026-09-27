# JOURNEY-DOWNLOAD-FEEDBACK01 ? CODE VERIFIED / BETA RECEIPT PARTIAL

2026-09-27. Approved one beta synthetic journey and one observed download-feedback defect. Prior records and unrelated dirty changes preserved.

## Result
Actual beta input monthly-rp03-supported-6sheet.xlsx produced structure0/formula1 and exact preview #VALUE! -> -5 at Budget!N18, reached approved READY. Actual repaired XLSX received, source hash unchanged, only business formula N18 changed, numeric cache -5.0. Output hash matches prior native Excel proof (reused, no new COM). Other14 cells differ only through formula cache values. Two other files not received even with individual buttons: all-three receipt and content validation remain PENDING. Core10 activations + beta2 reached download request, NOT successful receipt; two recovery attempts added.

## Actual changes and reuse
Only apps/web/src/components/RepairDelivery.tsx and ProposalFlow.test.tsx changed: visible per-file request state, partial-success retention and individual retry, explicit distinction from browser save, new job/plan reset, stale-response and unmount guard. Existing engine/API/approval/artifacts unchanged. PL work-order and evidence files added; no real customer data or commerce.

## Commands and review
Builder final npm.cmd test -- --run src/components/ProposalFlow.test.tsx:27/27 exit0; npm.cmd run build (tsc-b+Vite):exit0; git diff --check:exit0. Initial sandbox EPERM exit1 then elevated run0. One builder stale-prop correction required repeat checks; independent reviewer found missing unmount invalidation, one lifecycle correction and new deferred-unmount test closed it. Final independent GPT-6 Sol Medium reviewer PASS, no duplicate tests. Configured5.5 unavailable, bounded builder/reviewer used6SolMedium; no current/root model change claimed. Exact existing output excerpts in builder-validation.txt.
Read-only Python OOXML check initially exit1 for string-5 vs-5.0, next exit1 for treating recalculation cache as business edits, both distinct checker assumptions corrected; final exit0. Fixed oracle unchanged. Browser download-event wait timed out20s; browser internal URL denied, not bypassed. These limitations are not product test PASS.

## Evidence / not run / stop
Evidence directory: ../../../artifacts/synthetic_validation/journey-download-feedback01 (beta-journey.md, beta-ready.png, work-order.md, builder-validation.txt, inspect_download.py, download-inspection.json).
No commit/push/deployment in this unit. New feedback live desktop/mobile acceptance pending. Full regression and Excel replay not run because engine/API/approval/artifact content unchanged. Full beta all-three download verification pending. No next defect started. Next proposed single unit: deploy reviewed frontend and verify actual receipt of all3 files plus feedback on beta, investigate browser download refusal within that scope. Human usability/commercial/PG readiness not claimed.
