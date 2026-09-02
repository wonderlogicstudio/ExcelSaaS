# Success metrics and experiment plan

## Principle

The first goal is not traffic or account growth. It is evidence that a person with a real workbook problem understands the diagnosis, trusts the scope, and is willing to pay for a specific outcome.

## Funnel

```text
Landing view
→ scan/demo start
→ scan completion
→ diagnosis engagement
→ quote view
→ willingness-to-pay signal
→ payment attempt
→ successful repair
→ valid download
→ repeat/referral
```

## Pre-payment prototype metrics

| Metric | Definition | Initial learning target |
|---|---|---:|
| Hero comprehension | User can explain service after 5 seconds | 8/10 test users |
| CTA discovery | User starts upload/demo without help | 8/10 |
| Demo completion | Sample starters reaching result | >70% |
| Findings engagement | Result users opening at least one finding | >50% |
| Quote view | Completed scans that view quote scope | >40% |
| Price acceptance intent | Quote viewers choosing “would pay” | >10% initially |
| Expert interest | Advanced-result users requesting expert contact | Track, no target yet |

These are learning thresholds, not industry benchmarks.

## Paid beta metrics

- Scan-to-paid conversion by problem type.
- Gross margin per quote band.
- Repair success rate.
- Re-scan pass rate.
- Refund rate.
- Support minutes per order.
- Time to first useful result.
- Download completion.
- User-reported trust and clarity.
- Repeat/referral rate.

## Quality gates

Do not expand acquisition if:

- More than 2% of paid outputs cannot be opened.
- More than 5% require an unplanned refund.
- Automatic repair frequently changes unsupported workbook objects.
- Support time makes a tier unprofitable.
- Users misunderstand the limits of static analysis.

Exact thresholds must be recalibrated with beta volume.

## Experiment sequence

### E1 — Message

Compare:

- `보내기 전에, 엑셀부터 검사하세요.`
- `엑셀 오류와 숨은 위험을 1분 안에 확인하세요.`

Measure sample/upload starts and comprehension.

### E2 — Trust

Compare trust emphasis:

- Original untouched.
- No signup.
- Local/private quick scan once implemented.

Measure scan starts, not vanity clicks.

### E3 — Result framing

Compare:

- Risk score first.
- Repairable issue count first.
- Money/time impact first, without unsupported claims.

### E4 — Price

For equivalent synthetic scopes, test exact quote levels and ask willingness to pay. Do not charge until the repair path is reliable.

### E5 — Output choice

Test demand for:

- Audit report only.
- Annotated workbook.
- Repaired workbook.
- Expert review.

## Test-user recruitment

Start with 10–20 users from existing Excel inquiry channels and acquaintances who actually use complex workbooks. Do not recruit only developers or Excel experts.

Use synthetic or deliberately sanitized files during early sessions.

## Interview questions

1. What did you think this service would do before clicking?
2. Which result made you trust or distrust it?
3. Which issue would you pay to have fixed?
4. Was the quote scope clear?
5. What did you expect that was not included?
6. Would you upload a real work workbook? Why or why not?
7. Which deletion/privacy promise matters most?
8. Would you prefer a one-time fee or subscription?

## Decision rule

Do not build payment merely because users like the design. Proceed when multiple users with real problems express willingness to pay for the same repair class and understand the limitations.
