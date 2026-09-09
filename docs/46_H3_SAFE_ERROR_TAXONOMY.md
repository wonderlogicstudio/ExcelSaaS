# Hosted Beta H3 — Safe error taxonomy

## Contract

The browser receives a stable error code and a short Korean explanation. It never
receives an exception message, stack trace, provider response body, object key,
URL, HMAC, Access assertion, workbook field, or feedback payload echo. Operations
may count the fixed code, but may not attach request data to it.

## Implemented scan and control-plane codes

| Code group | Codes | Meaning exposed to the user |
| --- | --- | --- |
| File admission | `UNSUPPORTED_FILE_TYPE`, `EMPTY_FILE`, `FILE_TOO_LARGE`, `INVALID_MULTIPART_REQUEST` | The supplied input is unsupported, empty, too large, or not a valid upload request. |
| OOXML safety | `ZIP_ENTRY_LIMIT`, `UNSAFE_ZIP_PATH`, `ENCRYPTED_ZIP_ENTRY`, `UNCOMPRESSED_SIZE_LIMIT`, `COMPRESSION_RATIO_LIMIT`, `INVALID_OOXML`, `MISSING_OOXML_PART`, `WORKBOOK_PARSE_FAILED` | The workbook cannot be safely inspected. |
| Formula Audit gate | `FORMULA_AUDIT_NOT_AVAILABLE` | Formula Audit is unavailable in this environment. It remains disabled for the public hosted beta. |
| Access / API route | `ACCESS_ASSERTION_REQUIRED`, `ACCESS_ASSERTION_INVALID`, `API_ROUTE_NOT_FOUND`, `METHOD_NOT_ALLOWED` | The protected request cannot be accepted on this route. |
| Upload control | `UPLOAD_RATE_LIMITED`, `CONTROL_PLANE_NOT_CONFIGURED`, `FILE_TOO_LARGE`, `TEMPORARY_UPLOAD_UNAVAILABLE`, `ANALYSIS_CONTROL_PLANE_UNAVAILABLE` | Retry later, use a supported bounded file, or contact the operator. No upstream detail is exposed. |
| Feedback control (deployed, protected synthetic verification pending) | `FEEDBACK_NOT_CONFIGURED`, `FEEDBACK_RATE_LIMITED`, `INVALID_FEEDBACK_CONTENT_TYPE`, `FEEDBACK_PAYLOAD_TOO_LARGE`, `INVALID_FEEDBACK_PAYLOAD`, `FEEDBACK_STORAGE_UNAVAILABLE` | The small category-only response could not be recorded. The caller can retry only when appropriate. |
| Unexpected application failure | `INTERNAL_ERROR` | A generic temporary failure. No exception detail is returned. |

`CONTROL_PLANE_BODY_TOO_LARGE` and the HMAC validation codes are internal
control-plane rejection codes. They are deliberately not expanded into diagnostic
details for an end user.

## Explicitly not claimed as implemented application codes

- `SCAN_TIMEOUT`: Cloud Run enforces a 60-second request timeout, but the current
  application does not translate every provider timeout into this specific code.
- `TEMPORARY_SERVICE_ERROR`: an operator-facing concept, not a separate current
  application code.
- `AUDIT_SKIPPED_LIMIT` and `AUDIT_UNSUPPORTED`: the Formula Audit result envelope
  reports its approved status/limitations rather than promising these generic
  error codes.

This distinction prevents the notice, UI, and monitoring material from claiming
behaviour that has not been implemented and tested.
