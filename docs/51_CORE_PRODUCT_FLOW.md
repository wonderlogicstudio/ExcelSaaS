# VERIFIED — owner review pending

2026-09-13 approved IA acceptance implemented and exercised in the protected beta. See [CORE_FLOW review](delivery-v3_2/reviews/CORE_FLOW.md) and machine-readable evidence. Existing capabilities retained;95final web tests, full regression,4viewport sizes, frozen expected UI,8downloads and5native Excel opens verified. Commercial main-funnel gates remain pending; no next unit automatically approved. The original approved scope below is preserved.

---

# APPROVED — Core product flow and information architecture

Owner request 2026-09-13: preserve existing capabilities and center the product on upload → free diagnosis → review selection → support checks → scope/payment entitlement → exact approval → separate repair/revalidation → three artifacts. This is a bounded IA follow-up after D08, not D09 or commercial release.

Routes: / and /diagnosis; /precision-verification; /compare; /automation; /help; existing /privacy and /terms. /orders exposes only the existing owner-checked, temporary beta order recovery; no invented account page. /repair guides direct visitors to diagnosis. Existing anchors remain compatible. Same-tab navigation retains mounted workflow state, disclosures, filters and scroll; reload starts a fresh diagnosis and uses existing server recovery where available, never claims durable file persistence.

Reuse unified structure/M4 results, all findings/status/filter/CSV/score/manual revalidation and existing repair/comparison backends. Selecting a finding is a review request only. RP01 numeric text and RP02 true-blank candidates can seed one existing profile/sheet preflight at a time; other selections stay visible with an explicit unsupported/review disposition. No computed eligibility before server preflight/plan validation, no inferred anchor or business consent. Scope changes invalidate the old selection context; approved work is never silently replaced.

Home: concise purpose, upload, compact workflow, results and repair review. Additional services have distinct pages. Precision page distinguishes available static pattern checks from unimplemented business/expected-value verification. Automation standard products and custom consultation both show their actual unavailable state. Help retains service catalog, file principles, FAQ and operational guidance. No new prices, payment capability, scanner rules, engine or resources.

Validation: existing web baseline78 PASS; targeted route/history/state/selection tests, full scripts/verify.ps1 and existing M4 release equivalent without changing waivers/oracles. Actual protected beta desktop1440/1024 and mobile390/412, frozen synthetic expected results, repair and comparison flow. Capture commands/exits/screens and NOT_RUN separately. Deploy only validated web to existing Access Worker under standing approval; API/IAM/bindings/paymentOFF unchanged. Select local commit only, no push; stop for owner review.
