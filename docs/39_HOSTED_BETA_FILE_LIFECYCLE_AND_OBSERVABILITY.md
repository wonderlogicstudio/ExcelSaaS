# Hosted Beta H1 — File Lifecycle, Failure, and Observability Contract

## Proposed H2 upload lifecycle

```text
authorized user -> Worker creates opaque scan ID and opaque object key
-> short-lived, single-purpose private R2 upload authorization
-> Worker verifies object metadata/size before analysis request
-> authenticated Cloud Run analysis
-> value-free result response
-> immediate deletion attempt
-> R2 lifecycle expiration backstop
```

The original filename is display-only in the browser and never forms an object key, scan ID, log field, metric, or URL. A browser cannot list a bucket, choose another object key, or call Cloud Run directly. An analysis request must be idempotent and bound to an authenticated upload session; H1 does not yet implement those endpoints or session storage.

## Deletion outcomes required in H2

| Situation | Required action | User-facing claim allowed now |
| --- | --- | --- |
| Analysis succeeds | delete input immediately after result handoff; lifecycle rule remains backstop | none until this is tested |
| Analysis fails | attempt deletion before returning a safe failure | none until this is tested |
| Upload completes but analysis never starts | lifecycle expiry and cleanup reconciliation | none until this is tested |
| Worker or Cloud Run crashes | retry/reconciliation with opaque metadata only | none until this is tested |
| Browser closes | server-side lifecycle still owns cleanup | none until this is tested |

No partial M4 result is persisted or returned after an audit failure. A failed optional formula audit preserves only the already-valid base result.

## Resource and timeout model

H2's conservative initial Cloud Run target is one request per container, 1 CPU, 1 GiB memory, 60-second request timeout, minimum instances zero, and maximum instances two. These are deployment starting values, not measured production capacity or a promise to users. The platform must enforce them; a browser timer is not a timeout and closing a tab is not cancellation.

Longer work, actual cancellation, automatic repair, or reprocessing requires a separately approved asynchronous/job design with idempotency, cleanup after kill, and explicit resource limits.

## Observability allowlist

Only these fields may be emitted: opaque scan ID; scanner, base-rule-set, formula-audit-rule-set, and RC versions; file/sheet/formula count buckets; processing duration; rule code; subtype; execution status; and safe error code. `apps/api/app/observability.py` validates the allowlist before logging.

Never emit filename, sheet name, cell address, finding key, formula, value, object URL, presigned URL, identity, company/customer identifier, credential, or free text. Generic failures return `INTERNAL_ERROR` without exception text. Expected unsafe-file errors retain their existing safe error code and message.
