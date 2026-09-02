# Risk register

| Risk | Probability | Impact | Mitigation | Trigger/owner action |
|---|---|---|---|---|
| Users expect every logical error to be found | High | High | Static-analysis disclaimer, rule evidence, expert route | Rewrite copy if tests show misunderstanding |
| `openpyxl` rewrite loses workbook objects | High for complex files | Critical | No blind save; fidelity detection; audit-only route; minimal OOXML patching later | Any fidelity regression blocks repair launch |
| Sensitive data uploaded | High | Critical | Local quick scan, consent, private storage, short retention, no content logs | Security/privacy milestone before public files |
| Macro or external code execution | Medium | Critical | Never execute; sandbox only in separately approved future work | Any execution path is release blocker |
| Dynamic pricing feels arbitrary | Medium | High | Show quote factors and exact scope; version rules | Usability feedback indicates distrust |
| Automatic repair changes business intent | Medium | Critical | Confidence thresholds, previews, user selection, expert review | Incorrect-intent incident disables rule |
| Server/AI cost exceeds price | Medium | High | Limits, deterministic scan, cost telemetry, tier repricing | Margin below approved threshold |
| Incumbents copy generic features | High | Medium | Focus on repair contract, evidence, local privacy, expert network | Avoid formula/chat feature race |
| SEO produces free users but few buyers | High | Medium | Problem-specific pages tied to paid repair outcomes | Track scan-to-quote by keyword/problem |
| Fake or weak social proof pressure | Medium | High | No invented metrics; publish transparent synthetic demos and real approved cases | Marketing review gate |
| Payment disputes | Medium | High | Stored scope/quote/approval, no surprise charges, refund policy | Payment milestone legal review |
| File deletion fails | Low/medium | Critical | Lifecycle jobs, deletion audit, monitoring | Failed deletion alert and manual purge |
| Scanner false positives | Medium | Medium/high | Rule tests, confidence, severity review, feedback loop | High dismissal rate for a rule |
| Scanner false negatives | High | High | Never claim completeness; broaden corpus; expert route | User incident used as new regression fixture |
| Brand/trademark conflict | Medium | Medium | Working name only; domain/trademark check | Before public launch/domain purchase |
| Codex scope drift/token waste | Medium | Medium | One milestone goal, context index, stop rule, review gate | Codex begins unapproved milestone |
| Dependency/supply-chain issue | Medium | High | Lockfiles, scanning, minimal dependencies, update policy | Security advisory |
