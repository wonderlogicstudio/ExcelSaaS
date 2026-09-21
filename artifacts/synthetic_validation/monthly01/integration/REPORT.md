# MONTHLY-01 integration evidence

Status: VERIFIED_BETA_PENDING_OWNER. Independent final record review PASS: coverage_review6; records only, no duplicate execution.

Prior HORIZONTAL checkpoint fea78b0 pushed and remote main confirmed. New MONTHLY changes remain uncommitted/unpushed.

Full verify.ps1 exit0: web168, Worker16, API259, Ruff PASS, M4 sample36 exact candidates. Final actual-file batch18 unique files:15 frozen normal controls plus4 UI cases (one normal overlaps), all fixed expectations matched. Old out_of_scope truth and635 historical files were not edited.

Actual Excel:2 new files (equivalent -5; hidden #VALUE! CVErr) and2 old normal/mutant cases reused by hash. Raw native-excel.json remains FAIL because hidden Range.Text is empty; native-adjudication.json proves the same numeric CVErr as the independently checked visible #VALUE! case. No rerun or expected-value rewrite. All originals unchanged; macros/links off, read-only, no save.

Actual beta screen: normal0, mutant1 Budget!N18, equivalent0, grouped-hidden0. Structure0 each. Adjacent month formulas, limited scope and auto-repair unsupported visible. Desktop/mobile screenshots viewed in conversation, not saved. This is PL-observed UI proof, not independent browser replay or human usability testing.

API workbookcare-api-beta-00029-dir; Worker 7d353c64-457d-4376-922e-03ecbcc4d0bc. Linux runtime20/2/6 verified before promotion. Private IAM/Access/Gateway/bindings/maxScale1/paymentOFF preserved. Exact rollback recorded in release baselines. Only formula_patterns.py overlaid on verified prior image. Reviewed immediate guarded transition used; standalone traffic disabled.

Commands/exits: command-log.json (parent), regression.log/regression-exit.txt, release/commands.jsonl, web-release/commands.jsonl. Native/serialized evidence: fixture-plan.json, native-excel.json, native-reused.json, native-adjudication.json, file-results.json. Initial file results kept in before-review. Root prepare_fixtures/Excel exit1 from hidden Text assertion; adjudication and final file check exit0. Build image local+push exit0. Git initial add refused ignored generated files; respected ignore, selected55files committed/pushed fea78b0 exit0.

No automatic repair expansion, new customer data, live payment/refund, new paid resources or anonymous release. MONTHLY source commit/push and new repair browser replay not run.

Observed UI limitation: the monthly difference explanation remains English in the Korean UI; record as localization follow-up, not finished UX. Fourth upload first returned a generic hosted-beta request error; one spaced retry succeeded. Rate limiting suspected, not proven.
