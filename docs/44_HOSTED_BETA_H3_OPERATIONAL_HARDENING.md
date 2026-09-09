# Hosted Beta H3 — Operational hardening and Go/No-Go

## Scope and stop boundary

H3 is approved for the existing, Access-protected, synthetic-only hosted beta.
It prepares operational controls, category-only feedback persistence, privacy and
beta-notice drafts, evidence, and a final Go/No-Go package. It does **not** invite
or contact external users, accept a real workbook, begin M3/M3.5/M5, enable public
Formula Audit, add an account system, payment, repair, AI, a general database, or
any claim that has not been verified.

H2 remains a hard dependency. The existing one-day R2 lifecycle probe must be
observed expired after its eligibility time, and the owner-session HMAC-negative
probe must be confirmed and its temporary route removed. Until then, H3 can make
progress but cannot declare the beta ready.

## H3 design additions

### Minimal feedback persistence

Use one private Cloudflare KV namespace bound only to the Access-protected Worker.
It is not an account, workbook, results, or general analytics database. Each
record has a 30-day KV expiry as a provisional, minimised operational retention
setting; this duration and the final notice require human legal/product review
before an external invitation.

The Worker—not the browser—creates the opaque feedback ID and server timestamp.
It accepts only a random per-browser-session context ID, one allowlisted Formula
Audit rule code and subtype, and one of these categories:

- `HELPFUL`
- `POSSIBLE_FALSE_POSITIVE`
- `EXPLANATION_INSUFFICIENT`

The Worker attaches the deployed scanner, formula-audit rule-set, release-candidate
and environment values itself. It rejects unknown fields, arrays, free text,
filenames, sheet names, cell locations, finding keys, formula/value content, URLs,
identity values, and client-supplied versions. A compact JSON body limit and a
separate key prefix on the existing assertion-hash rate limiter bound repeated
feedback without mixing its quota with uploads. The route is Access-authenticated,
does not reach Cloud Run or R2, and returns only a safe status code.

The existing formula-audit UI remains separately feature-gated. H3 does not turn
that switch on for public hosted beta merely to collect feedback. The persistence
path is exercised only with synthetic data until a later approved exposure step.

### Account prerequisite recorded 2026-09-09

The repository implementation and tests are ready for a private `FEEDBACK` KV
binding. The original namespace-creation attempt was rejected with Cloudflare API
authentication error `10000`; the account administrator subsequently created the
approved namespace on 2026-09-09 and supplied its ID. The Worker configuration
now names that private binding and fixed server version values. Worker version
`e5aee49a-47b2-4a8e-b265-7de17fc27ac5` deployed the binding on 2026-09-09. A
tokenless header-only request to the feedback route received the expected
Cloudflare Access 302, so it is not a public endpoint. No fallback database,
browser cache, public endpoint, or weakened route is used. An authenticated
synthetic write/read verification remains required before server feedback can be
called fully evidenced or collecting data.

### Operations and safe errors

Application telemetry is an explicit allowlist. It records only opaque IDs,
fixed scanner/rule/RC versions, fixed status/error codes, rule code/subtype, and
size/count/duration buckets. It never logs a filename, sheet, address, finding
key, formula, value, uploaded bytes, identity, organisation, URL, credential, or
free text. Safe user error codes have one stable Korean message and no exception
text.

The H3 backend was deployed and rechecked at 2026-09-09 14:09 UTC as Cloud Run
revision `workbookcare-api-beta-00003-bsp`, with immutable image digest
`sha256:5ab7065c318c2325f6124b41787e8297f4de6f428329151b6a1ca45c7cf35703`.
It retains minimum instances zero (platform default; no minimum annotation),
maximum two, CPU 1, memory 1 GiB, concurrency 1, and timeout 60 seconds. The
only Cloud Run invoker is the Gateway service account; an unauthenticated direct
`/health` request returned `403`. The current Tokyo Gateway is `ACTIVE`, and a
read-only IAM check found no `allUsers` or `allAuthenticatedUsers` binding on
Cloud Run. These are intentionally conservative synthetic-validation controls,
not a capacity claim. A Google Cloud budget already
has KRW 10,000 thresholds at 50%, 90%, and 100%; no recipient identity is
recorded here. Cloudflare billing alert availability and recipient selection remain
a human account-administrator check.

### Notice and privacy drafting

The hosted UI will link to short, truthful beta/privacy pages. They may say that
the service statically inspects supported workbooks, does not execute macros,
formulas, or external connections, and does not overwrite the source file. They
must not claim zero retention, a particular data residency, a certification,
perfect accuracy, or absolute security. The pages must label unanswered legal and
support-contact decisions as human blockers before any invitation.

## H3 acceptance gates

1. Reconfirm Hosted URL/Access, Worker, private R2, Cloud Run IAM/configuration,
   current Git baseline, immediate cleanup, and the pending lifecycle backstop.
2. Test upload and feedback rate limits; invalid/repeated requests do not reach
   R2 or persistence respectively.
3. Test the category-only feedback schema, expiry configuration, protected route,
   and absence of prohibited fields using synthetic data only.
4. Test safe telemetry and error shapes; record only allowed operational events.
5. Produce a processing inventory, privacy draft, beta notice draft, rollback
   rehearsal, synthetic E2E evidence, and a desktop/mobile human QA checklist.
6. Re-run full regression and M4 release verification. Preserve base Findings,
   risk, quote, CSV, re-validation, and M4 separation.
7. Record every human/legal/account-admin blocker explicitly. Only if every
   critical gate is evidenced may the final review use
   `HOSTED BETA READY — EXTERNAL USER INVITATION AWAITING PRODUCT OWNER APPROVAL`;
   otherwise it must use `HOSTED BETA NOT READY`.

## Human-owned items

- Confirm the one-day lifecycle probe has expired after it becomes eligible.
- Complete the owner-session HMAC-negative confirmation, then remove its
  temporary route.
- Choose a real support/deletion-request contact before an invitation.
- Review and approve final privacy/terms wording with appropriate legal advice.
- Confirm Cloudflare billing-alert options and recipients in the account UI.
- Perform the final hosted desktop/mobile browser walkthrough; automated tests
  cannot substitute for an authenticated interactive session.
