# Security and privacy specification

This service will handle files that may contain payroll, customers, revenue, banking, employee, or operational information. Privacy messaging is not sufficient; the architecture must enforce it.

## Threat model

- Malicious OOXML/ZIP files.
- Decompression bombs and excessive XML expansion.
- Path traversal inside ZIP entries.
- Oversized workbooks exhausting CPU or memory.
- Embedded macros and binaries.
- External links and data connections.
- Formula injection when exporting CSV or logs.
- Unauthorized access to temporary objects.
- Guessable download URLs.
- Payment/status replay.
- Accidental workbook content in logs, analytics, error reporting, or LLM prompts.
- Cross-customer object mix-up.

## Current controls

- Extension and OOXML structure validation.
- File-size, ZIP entry, total decompressed-size, and path checks.
- `defusedxml` dependency for safer XML handling.
- No macro, formula, query, or external-link execution.
- No workbook saving in the scan path.
- No LLM call in the scan path.
- CORS allowlist through configuration.
- Synthetic tests only.

## Production upload controls

1. Create a random analysis ID and random object key; do not use the original filename as the key.
2. Generate a single-purpose, short-lived presigned `PUT` URL.
3. Restrict content length and expected content type at the application layer.
4. Configure R2 CORS for the exact production origin.
5. Keep the bucket private.
6. Confirm upload completion server-side before analysis.
7. Use a separate short-lived `GET` token for downloads.
8. Delete input and output objects automatically at expiry and allow immediate user deletion.

## Workbook execution policy

Never execute:

- VBA/macros.
- Office Scripts.
- Embedded OLE objects.
- DDE.
- Power Query.
- External database/web connections.
- Links to external workbooks.
- Formulas through Excel or LibreOffice in the general scan container.

A future calculation/recalculation feature requires a separately approved sandbox milestone with no network, low privileges, strict time/memory limits, and disposable storage.

## File-support policy

### Initial support

- `.xlsx`: static audit.
- `.xlsm`: static audit only; macros detected but never executed; no rewrite.

### Reject or manual route

- Password-encrypted workbooks.
- Legacy binary `.xls`.
- Digital-signature-sensitive workbooks.
- Files above configured limits.
- Files with unsupported or high-fidelity OOXML parts when repair is requested.

## Fidelity policy

`openpyxl` cannot preserve every possible item in an existing workbook. Therefore:

- Static analysis can use `openpyxl` without saving.
- Repair must detect drawings, charts, shapes, macros, pivots, signatures, external connections, and unsupported parts.
- High-fidelity-risk files must be audit-only until a preservation-safe method exists.
- Safe repair should prefer minimal OOXML part patching with a validated change set rather than blind load/save.
- Output must always be a new object and must pass a re-scan.

## Retention

Proposed beta policy:

- Failed uploads: remove immediately when possible.
- Free diagnosis source file: delete after result generation or within 1 hour, depending on chosen implementation.
- Paid repair input/output: delete automatically 24 hours after completion.
- Metadata: retain only what is necessary for transaction, dispute, security, and accounting obligations.

Final durations require legal/privacy review before launch.

## AI data boundary

Default: `AI_EXPLANATIONS_ENABLED=false`.

When enabled in a future milestone:

- Send rule codes and non-sensitive structural summaries, not raw workbook contents by default.
- Use deterministic templates for common explanations.
- Require explicit consent before sending cell-level context.
- Redact likely personal identifiers.
- Enforce a per-analysis token and cost budget.
- Record provider, model, prompt version, and whether content was included.
- Contractually verify provider retention/training terms before production.

## Logging

Use structured events such as:

```json
{
  "event": "scan_completed",
  "analysis_id": "random-id",
  "file_size_bucket": "1-5MB",
  "sheet_count_bucket": "6-10",
  "rule_counts": {"FORMULA_REF_ERROR": 2},
  "duration_ms": 2810
}
```

Do not log:

- Workbook contents.
- Formula text.
- Original filename.
- Object URL.
- Email.
- Payment instrument data.

## User-facing claims gate

The UI must not claim any of the following until verified and approved:

- End-to-end encryption.
- Korean-only data residency.
- SOC 2, ISO 27001, GDPR, or other certifications.
- 100% accuracy.
- Zero retention.
- Files never leave the device.

The beta may truthfully say that macros/external connections are not executed and that the original is not overwritten.
