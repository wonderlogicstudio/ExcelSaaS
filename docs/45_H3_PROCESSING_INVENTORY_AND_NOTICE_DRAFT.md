# Hosted Beta H3 — Processing inventory and notice drafts

> Status: engineering draft for the Access-protected, synthetic-only beta. It is
> not a legal notice, a promise to external users, or approval to invite anyone.

## What is actually processed today

| Data group | Purpose and path | Storage / retention currently evidenced | Logging rule |
| --- | --- | --- | --- |
| Synthetic workbook upload | Static diagnosis only. Access-protected Worker -> private R2 transient object -> API Gateway -> IAM-protected Cloud Run. | Worker tries to delete the opaque R2 object after both successful and malformed terminal paths. Those two terminal paths have been observed empty immediately afterward. The one-day R2 lifecycle rule is configured, but its separate time-based expiry probe is still pending. | No filename, sheet, cell, formula, value, URL, identity, or workbook bytes. |
| Diagnosis response | Return static, value-free result to the current browser request. | No result database or server-side scan history is implemented. Browser UI state remains in the current session. | Only fixed, content-free operation fields are permitted. |
| Operational events | Availability, limits, safe errors, and regression diagnosis. | Cloud Run / provider retention settings are not asserted by this repository and need account-owner review before invitation. | Opaque scan ID; fixed versions; fixed rule code/subtype; status/error code; and file/count/duration buckets only. |
| Formula Audit feedback | Not enabled for the public hosted beta. The H3 code is designed to receive category-only synthetic feedback through the Worker. | The private KV binding was deployed on 2026-09-09 with a 30-day record expiry. Its authenticated synthetic write/read evidence is still pending, so the storage path is not yet a completed H3 gate. | No filename, sheet, address, finding key, formula, value, free text, URL, identity, or browser-supplied version. |

## Feedback record contract after the account prerequisite is satisfied

The Worker, rather than the browser, creates the record ID and timestamp. It will
store only:

- worker-created opaque feedback ID;
- random browser-session context ID;
- deployed scanner, Formula Audit rule-set, and release-candidate versions;
- fixed rule code and allowlisted subtype;
- `HELPFUL`, `POSSIBLE_FALSE_POSITIVE`, or `EXPLANATION_INSUFFICIENT`;
- server timestamp and fixed environment value.

The request must contain exactly the four input fields needed for the user choice:
`feedback_session_id`, `feedback_category`, `rule_code`, and `subtype`. Unknown
fields, arrays, free text, client-supplied versions, and invalid rule/subtype
pairs fail closed with a safe code. The same Access check applies and a separate
assertion-hash rate-limit key is used, so feedback attempts do not consume the
upload quota. The key is not stored or logged.

## Draft privacy notice (not final legal wording)

WorkbookCare Hosted Beta statically inspects supported Excel workbook structure
and formula references to produce diagnostic information. It does not execute
macros, formulas, external connections, or queries, and it does not overwrite the
source workbook.

For a submitted workbook, the service uses an Access-protected Worker, a private
temporary object store, an authenticated analysis service, and an immediate
deletion attempt after processing. A one-day object-store lifecycle backstop is
configured. The final confirmation that a lifecycle-expiry probe has elapsed is
still pending; this draft therefore does not promise instantaneous deletion or
zero retention.

Operational records are deliberately limited to fixed status and version values
and size/count/time ranges needed to operate the beta. They are designed not to
include workbook contents, filename, sheet name, cell location, formula, cell
value, email address, company name, URL, or free-text feedback.

Before any invitation, the product owner must select a real contact for questions
and deletion requests, set any provider retention choices that are outside this
repository, and obtain appropriate legal review of the final notice.

## Draft beta terms notice (not final legal wording)

This is a limited Hosted Beta. Results are diagnostic reference information and
are not a guarantee that a workbook is correct, complete, safe, or suitable for a
particular business decision. Formula Pattern Candidates are not confirmed formula
errors and are not replacement formulas. The service does not recalculate Excel,
perform automatic repair, or modify the uploaded source workbook.

Users must independently review important workbooks and decide whether any change
is appropriate. Some Excel features are unsupported, and the service can be
unavailable or return an error. Do not use the beta as the sole control for a
high-impact decision. The scope, support contact, prohibited use, and liability
wording require product-owner and legal review before external invitation.

## H3 human decisions still required

1. Supply a support/deletion-request contact and approve its display.
2. Obtain appropriate legal review and approve final privacy/terms wording.
3. Confirm provider-managed logging retention settings.
4. Restore Cloudflare KV creation/write authority or provide an approved private
   namespace ID, then allow the protected feedback binding to be deployed and
   verified with synthetic data only.
