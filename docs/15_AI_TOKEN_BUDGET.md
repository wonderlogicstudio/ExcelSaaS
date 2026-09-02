# AI and Codex token budget

## M4-A update

M4-A formula-pattern auditing and Feedback Capture Readiness use deterministic local code only. They add no AI API call, model prompt, token budget, third-party analytics, or workbook-data transmission.

## Two separate budgets

1. **Development tokens** used by Codex to build the product.
2. **Runtime AI tokens** used by the SaaS when customers scan or repair files.

Both must be controlled explicitly.

## Development-token policy

- `AGENTS.md` stays concise.
- `docs/00_CONTEXT_INDEX.md` tells Codex which documents to read.
- One approved milestone per `/goal`.
- Codex reads only current-milestone files and related source.
- `docs/10_PROGRESS.md` is a current snapshot, not an append-only journal.
- Use targeted tests before full-suite tests.
- No subagents unless tasks are independent and non-overlapping.
- Stop after acceptance criteria and review package.
- Do not ask Codex to keep improving without a measurable stopping rule.

## Codex milestone workflow

```text
Human approves milestone
→ Codex establishes baseline
→ implements within scope
→ tests and inspects result
→ updates concise progress/review
→ stops
→ human approves or redirects
```

The human should usually type only:

- First goal prompt.
- `승인. 다음 마일스톤으로 진행.`
- A specific rejection/correction when needed.

## Runtime AI policy

### Free scan

Target AI calls: **zero**.

Use deterministic templates for rule explanations, finding guidance, and beta price-range factors. M2.5's recommendation engine must remain limited to discovered facts, possible impact, unchecked scope, next technical checks, and a service code; it must not call an AI API.

The M2.5 Extension also uses deterministic templates for Action Category, Excel manual-check steps, normal-condition notes, and recommended next action. Same-session re-validation compares structured scanner results only; it makes zero AI calls and does not send a workbook or cell values to an AI provider.

### Future precision verification / repair

AI is not implemented for these services. If separately approved later, it may be used only when it adds measurable value:

- Explain unusual combinations of findings.
- Draft a user-friendly repair summary from structured rule output.
- Suggest an expert-review brief.

AI must not be the sole authority for:

- Risk severity.
- Quote price.
- Payment scope.
- Formula replacement.
- Repair verification.

## Per-analysis runtime budget proposal

When AI explanations are enabled:

- Maximum calls: 2.
- Maximum structured input: 3,000 tokens.
- Maximum generated output: 800 tokens.
- Raw workbook cells: prohibited by default.
- Cache common rule explanations by rule-set version and locale.
- Fall back to templates when budget is reached or provider fails.

Final model and currency budget require current API pricing review at implementation time.

## Cost telemetry

Track per analysis:

- model/provider.
- input/output token counts.
- cache hits.
- latency.
- estimated cost.
- feature that triggered the call.
- conversion or support outcome associated with the feature.

Remove AI features that do not improve user trust, conversion, repair success, or support efficiency.
