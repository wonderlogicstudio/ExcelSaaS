# Architecture

## Architecture goals

- Near-zero idle cost during validation.
- Deterministic workbook scanning before any LLM usage.
- Direct-to-object-storage uploads in production.
- Explicit states for diagnosis, quote, approval, payment, repair, and download.
- Safe failure: unsupported files are diagnosed or escalated, never silently rewritten.
- Easy local development in VS Code/Codex.

## Current vertical slice

```text
React + Vite browser
      │ multipart/form-data in local development
      ▼
FastAPI service
      │
      ├─ OOXML ZIP validation
      ├─ openpyxl read-only/static inspection
      ├─ deterministic issue rules
      ├─ risk/complexity calculation
      └─ quote preview
```

The sample-demo path works without the API.

## Target production architecture

```text
Browser
  │
  ├─ Static/React app: Cloudflare Workers Assets
  │
  ├─ Control API: Cloudflare Worker or small API layer
  │      ├─ rate limits
  │      ├─ upload session
  │      ├─ short-lived R2 presigned URL
  │      └─ public status/download tokens
  │
  ├─ Direct upload → Cloudflare R2 private bucket
  │
  └─ Analysis request → Google Cloud Run
          ├─ FastAPI orchestration for small scans
          ├─ Cloud Run Job for long scans/repairs
          ├─ deterministic scanner and quote engine
          ├─ optional bounded AI explanation adapter
          └─ result metadata → database
```

## Why split Cloudflare and Cloud Run

Cloudflare is suitable for the web edge, signed upload control, static assets, and private object storage. Cloud Run provides a conventional container environment for Python, `openpyxl`, heavier packages, and future isolated workers while scaling to zero.

## Application boundaries

### `apps/web`

Responsibilities:

- Landing and SEO-oriented content.
- Upload consent and validation.
- Sample demonstration.
- Scan status polling/display.
- Findings and quote UI.
- Approval UX.
- Download UX.
- Privacy and limitations.

Must not:

- Contain secret storage credentials.
- Calculate authoritative prices independently.
- Treat client-side validation as security.

### `apps/api`

Responsibilities:

- File-envelope validation.
- Static workbook inspection.
- Rule execution.
- Risk and complexity scoring.
- Quote calculation from versioned rules.
- Result schema.
- Later: repair planning and job orchestration.

Must not:

- Execute macros, queries, formulas, embedded files, or external links.
- Overwrite input files.
- Trust extension or MIME type alone.

### Future control plane

Responsibilities:

- Identity and anonymous sessions.
- Object keys and signed URLs.
- Rate limits and abuse controls.
- Payment webhook state machine.
- Retention/deletion scheduling.
- Audit events with no workbook content.

## Core domain states

```text
CREATED
→ UPLOAD_AUTHORIZED
→ UPLOADED
→ VALIDATING
→ SCANNING
→ DIAGNOSED
→ QUOTED
→ SCOPE_APPROVED
→ PAYMENT_PENDING
→ PAID
→ REPAIRING
→ VERIFYING
→ READY
→ DOWNLOADED
→ EXPIRED / DELETED
```

Failure states must preserve the last valid state and a user-safe error code.

## API sketch

### Current

- `GET /health`
- `POST /v1/scans`

### Production roadmap

- `POST /v1/upload-sessions`
- `POST /v1/analyses`
- `GET /v1/analyses/{analysis_id}`
- `GET /v1/analyses/{analysis_id}/findings`
- `POST /v1/quotes/{quote_id}/approve`
- `POST /v1/payments/checkout`
- `POST /v1/payments/webhook`
- `POST /v1/repairs`
- `GET /v1/repairs/{repair_id}`
- `POST /v1/download-tokens`
- `DELETE /v1/files/{file_id}`

All mutation endpoints require idempotency keys in production.

## Data model outline

### Analysis

- `id`
- `anonymous_session_id` or `user_id`
- `object_key`
- `original_filename_display` (encrypted or minimized)
- `sha256` (optional; assess privacy before enabling)
- `status`
- `scanner_version`
- `rule_set_version`
- `risk_score`
- `complexity_score`
- `created_at`
- `expires_at`

### Finding

- `analysis_id`
- `rule_code`
- `severity`
- `sheet_ref`
- `cell_ref`
- `confidence`
- `repair_class`
- `metadata_json` without raw sensitive values

### Quote

- `analysis_id`
- `quote_version`
- `currency`
- `amount`
- `included_rule_codes`
- `excluded_rule_codes`
- `expires_at`
- `status`

### Repair

- `quote_id`
- `repair_plan_version`
- `status`
- `output_object_key`
- `verification_analysis_id`
- `change_log_object_key`

## Synchronous vs asynchronous

- Small scan target: synchronous response under 15 seconds.
- Larger scan: return `202 Accepted`, poll status.
- Repairs and high-fidelity verification: asynchronous job.
- Do not hold a browser request open for long jobs merely because Cloud Run permits long timeouts.

## Versioning

Persist these versions with every result:

- Scanner version.
- Diagnostic rule-set version.
- Quote rule-set version.
- Repair engine version.
- AI prompt/template version when enabled.

This is required for dispute handling and reproducibility.

## Observability

Allowed metrics:

- File size bucket.
- Processing time.
- Sheet/formula count buckets.
- Rule-code counts.
- Status transitions.
- Error codes.
- Conversion events.

Prohibited by default:

- Cell contents.
- Formula text.
- Raw filenames.
- Email addresses in logs.
- Uploaded file URLs.
