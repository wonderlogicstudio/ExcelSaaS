# M4-D Failure and Operations Contract

## Stable user outcomes

| Situation | M4 result | Base free result | User-facing rule |
| --- | --- | --- | --- |
| Successful audit with candidates | `COMPLETED` | Retained | Candidate means a pattern difference, not an error verdict |
| Successful audit with no candidates | `COMPLETED` | Retained | State that no pattern candidate was found in this scope, not that the workbook is correct |
| Insufficient evidence | `ABSTAINED_INSUFFICIENT_EVIDENCE` | Retained | No candidate is created |
| Truncated base/audit scan | `SKIPPED_TRUNCATED` | Retained | Explain incomplete scope |
| Sheet, formula, or candidate capacity exceeded | Matching `SKIPPED_*_LIMIT` | Retained | Do not show a partial audit list |
| Unsupported formula structure | `SKIPPED_UNSUPPORTED_STRUCTURE` | Retained | Treat as outside support, not a confirmed error |
| Parse/runtime failure | `FAILED` | Retained | Offer a safe retry; no stack trace |
| Invalid/unsafe upload envelope | Safe API error code | No new audit result | Do not expose archive detail or server paths |

## Retry and cancellation

The current API is synchronous and has no server-side job cancellation. Closing a browser page or aborting a network request must not be called “cancelled analysis.” A retry is a new same-browser file upload and is safe because the audit holds no server-side audit session. Hosted beta requires a separately implemented idempotent job protocol before actual cancellation, timeout recovery, or persistent retry claims are made.

## Operations response

1. Preserve the last valid base diagnosis.
2. Record only an allowlisted, content-free error event when observability is later approved.
3. Return a stable safe code/message; never return Python exception text, formula text, values, filenames, paths, or object URLs.
4. Disable the optional audit server-side if an availability or resource issue occurs. Do not alter the base diagnosis feature flag.
5. Roll back the API/frontend deployment revision if a hosted change affects the baseline separation contract.

## Release verification

`scripts/verify.ps1` remains the ordinary development check. `scripts/verify-m4-release.ps1 -AcceptProductOwnerFixtureWaiver` is the explicit, slower RC command. It runs the web/API regression suite, the two-pack M4-C evaluator with the narrow documented waiver, and the existing M4-A.5 quality/performance evaluator. It is not part of ordinary development verification.
