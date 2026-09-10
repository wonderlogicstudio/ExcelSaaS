# Product P1 — Free-result navigation

## Authorization and selection — 2026-09-10

The owner requested the next bounded product development step, full regression
verification, a Git commit, and GitHub synchronization. H2/H3's remaining
operational checks and all Cloudflare/Google Cloud deployment are explicitly
excluded. Their existing incomplete status is preserved.

Candidates, in recommended order:

1. Make the existing free findings easier to work through by severity, sheet,
   and local handling status. Selected: improves the documented direct-check
   workflow without new analysis, data collection, or infrastructure.
2. Improve location-level detail in same-session re-validation comparisons.
   Deferred as a separate product slice.
3. Define M5's user-declared business-rule contract and evidence. Requires a
   separate scope; business intent must never be inferred from workbook content.

This is a narrow engineering improvement based on the current UI and product
contract, not evidence of user demand, payment intent, or a completed M3 study.

## Acceptance contract

- Default view retains every free finding, in its original order, with the
  existing expandable evidence and local status control.
- Severity, sheet, and handling-status filters combine with AND. A missing
  status means `UNREVIEWED`. Workbook-level findings remain selectable separately
  from actual sheet names, including a synthetic sheet named `all`.
- The priority shortcut clears other filters and shows existing critical and
  warning findings. It is disabled when there are none; it makes no new risk
  judgment or automatic repair recommendation.
- Show total and displayed counts, an explicit reset, and an empty-filter
  message that cannot be mistaken for a clean scan. Truncation notices remain.
- Filtering changes only the list. Summary, quote, type/status totals,
  re-validation, and both existing CSV buttons use the complete current result.
- A local status change immediately updates the filtered list; if its row leaves
  the filter, keyboard focus returns to the status filter. Resetting filters does
  not reset handling statuses. A new analysis ID or scan timestamp resets filters.
- Controls use native labelled selects, visible focus, polite count updates,
  responsive layout, and the existing CSS reduced-motion policy.
- Use only synthetic fixtures and the local demo for checks. Run all of
  `scripts/verify.ps1` after the change and inspect desktop/mobile operation.

## Boundaries and limitations

Filters exist only in React memory. They do not write to a URL, browser storage,
logs, telemetry, feedback, or a server. Sheet options come from existing findings;
this is not a list of every sheet in the original workbook. Filtered export is
not provided: CSV remains the complete result, with its existing format.

No scanner/API/Worker/infra/feature-flag change, new rule, cloud resource,
deployment, public Formula Audit, public feedback, external invitation, real
workbook, long-term history, account, payment, repair, recalculation, AI, M5, or
new retention policy is part of P1. Local regression tests do not establish live
H2/H3 readiness. Do not advance to another milestone after review.

## Verification outcome

`scripts/verify.ps1` passed before implementation (web 30 / Worker 13 / API 72)
and afterward (web 36 / Worker 13 / API 72), including TypeScript, production
build, Ruff, and the supplied M4-C 36-candidate exact-match gate. The existing
Starlette/httpx deprecation warning is unchanged. Six new component regressions
cover combined filters, complete CSV arguments and invariant scan data,
workbook-level location selection, the priority shortcut, local status/focus,
new-scan reset, and zero/information-only behavior. Existing synthetic demo and
internal-only Formula Audit tests also pass.

The connected UI runtime returned `No browser is available` and an empty browser
inventory. Real desktop/mobile rendering and screenshots were not verified;
visual acceptance remains pending. This is an implementation review, not full
P1 acceptance or Hosted Beta Ready. Manual follow-up is listed in
`MILESTONE_REVIEW.md` and does not authorize deployment or real files.
