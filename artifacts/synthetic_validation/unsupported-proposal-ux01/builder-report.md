# UNSUPPORTED-PROPOSAL-UX01 builder handoff

## Change

- `apps/web/src/components/RepairProposalPicker.tsx`: unsupported formula groups show a refusal reason and, per cell, a collapsed disclosure containing the original formula and actual workbook formulas at recorded comparison locations. The existing local `readSourceCells` helper supplies values. Missing evidence is labeled unavailable. No unsupported draft is prepared.
- `apps/web/src/App.tsx` and `apps/web/src/components/DeliveryWorkspace.tsx`: the manual delivery entry is concealed until an explicit advanced action; the workspace remains mounted so an existing job survives proposal reselection. Supported proposal drafts still open the normal workspace with selected addresses.
- `apps/web/src/proposal-flow.css`: compact disclosure styling.
- `apps/web/src/App.reselect.test.tsx` and new `apps/web/src/components/UnsupportedProposalUx.test.tsx`: unsupported-only, mixed, formula evidence and missing-evidence coverage.

## Exact command sequence and results

1. `npm.cmd --workspace apps/web run test -- --run src/components/UnsupportedProposalUx.test.tsx src/components/ProposalFlow.test.tsx src/App.reselect.test.tsx` in default sandbox: exit 1 before collection, Vite/esbuild `spawn EPERM`.
2. Same command with `require_escalated`: exit 1. App.reselect 2 tests and ProposalFlow 27 tests passed. New UnsupportedProposalUx 3 tests failed: duplicate `=F3+G2` exact query; mixed supported test had `onPrepare` call count 0; missing-evidence exact query did not match an element containing a `현재 수식:` prefix.
3. After changing only the new test's disclosure queries, `npm.cmd --workspace apps/web run test -- --run src/components/UnsupportedProposalUx.test.tsx` with `require_escalated`: exit 1. Formula evidence case passed. Mixed case still had `onPrepare` call count 0 (source evidence had not settled before the click). Missing-evidence exact query still failed because its target text is part of a longer element.
4. `npm.cmd --workspace apps/web run build` with `require_escalated`: exit 1 at TypeScript. New test fixture missing required `formula_pattern.dominant_pattern_id`.
5. After adding that field to the fixture, same build command with `require_escalated`: exit 1 at TypeScript. The fixture uses invalid `pattern_subtype: 'OTHER'`; `GENERIC_PATTERN_DRIFT` is an allowed type.
6. `git diff --check` on edited tracked source/test files: exit 0.

These failures are confined to the newly added test assertions and fixture so far; no product-source failure was observed. Parent/reviewer should resolve the remaining fixture/assertions, rerun focused tests and the build, then inspect actual desktop/mobile behavior. No backend, rule, deployment, Git publication, Excel replay, or full regression was run. The unrelated pre-existing dirty `RepairDelivery.tsx` was preserved.

## Owner-approved bounded correction (2026-09-27)

- Changed only the new `UnsupportedProposalUx.test.tsx` and affected `App.reselect.test.tsx` fixtures/assertions. Both formula fixtures now use typed `GENERIC_PATTERN_DRIFT` and include `dominant_pattern_id`. The missing-evidence assertion matches its full rendered label. Added a nonformula regression proving text cell contents are not displayed as current or comparison formulas.
- The mixed test now waits for the supported B3 source example before confirmation and checks that `onPrepare` receives only `['B3']`. A valid minimal synthetic XLSX supplies that source example. Diagnosis of the earlier failure showed `ProposalDetail` reading the real workbook parser, which rejected the dummy `File(['synthetic'])` with `ORIGINAL_EVIDENCE_UNAVAILABLE`; simply waiting or weakening the draft assertion would not resolve it. Temporary diagnostic logging in `RepairProposalPicker.tsx` was removed. The reviewer-requested product guard (`type === 'formula'`) remains in place.

### Additional exact commands and exits

All npm commands ran from repository root with `require_escalated` for the ExcelSaaS workspace.

1. `npm.cmd --workspace apps/web run test -- --run src/components/UnsupportedProposalUx.test.tsx src/App.reselect.test.tsx`: exit 1. App.reselect 2 passed; new file 2 passed/2 failed (mixed source-read error, missing comparison text matcher).
2. `npm.cmd --workspace apps/web run test -- --run src/components/UnsupportedProposalUx.test.tsx --testNamePattern "mixed supported"`: exit 1. Diagnostic assertion showed only unsupported `[H3,H2]` mock call; supported source read had not hit that mock.
3. `npm.cmd --workspace apps/web run test -- --run src/components/UnsupportedProposalUx.test.tsx`: exit 1. New file 3 passed/1 failed; missing-evidence and nonformula assertions passed, mixed source-read remained.
4. `npm.cmd --workspace apps/web run test -- --run src/components/UnsupportedProposalUx.test.tsx --testNamePattern "mixed supported"`: exit 1. Adding the missing `readSourceSheets` mock export did not fix the mixed source read.
5. Same single-test command with module preload: exit 1. Preload did not fix the mixed source read.
6. Same single-test command with temporary diagnostic logging: exit 1. Caught `ORIGINAL_EVIDENCE_UNAVAILABLE` from real `workbookEvidence.ts` while parsing the dummy file. Logging was immediately reverted.
7. Same single-test command with valid in-memory synthetic XLSX: exit 0, 1 passed/3 skipped.
8. `npm.cmd --workspace apps/web run test -- --run src/components/UnsupportedProposalUx.test.tsx`: exit 0, 4 passed.
9. `npm.cmd --workspace apps/web run build`: exit 0; `tsc -b && vite build` passed.
10. `git diff --check -- apps/web/src/App.reselect.test.tsx apps/web/src/components/RepairProposalPicker.tsx`: exit 0. The new untracked test was read and built by TypeScript; no debug log or invalid subtype remains.

Previous 27 ProposalFlow passes were reused without rerun. App.reselect 2 passes were not rerun after fixture correction; its test payload and type are included in the passing TypeScript build. No backend, Excel, beta, deployment, commit, push, or full regression was performed in this correction.
