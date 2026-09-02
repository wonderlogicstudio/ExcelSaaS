# Pricing and quoting

## Pricing principle

Do not charge before diagnosis and do not offer an unlimited promise. In M2.5 the user receives a diagnostic summary, included/excluded expected scope, and a beta price hypothesis only. Exact scope, fixed price, approval, and payment are future capabilities.

## Recommended launch model

### Free quick diagnosis

- No signup.
- Risk score and issue counts.
- Top findings.
- Repairability summary.
- Quote preview.

### Planned per-file precision verification

Use exact, rule-based prices after the scan rather than a subscription. Suggested beta ranges:

| Outcome | Indicative price | Notes |
|---|---:|---|
| Audit | ₩9,000 ~ ₩19,000 | Informational or no current risk signal |
| Basic | ₩19,000 ~ ₩29,000 | Lower-complexity precision-verification hypothesis |
| Standard | ₩29,000 ~ ₩49,000 | Typical beta precision-verification hypothesis |
| Advanced | ₩49,000 ~ ₩79,000 | Higher-complexity precision-verification hypothesis |
| Expert | Range not set | Separate future consultation |

These are hypotheses, not final prices or currently chargeable amounts. The implementation stores them in `apps/api/app/service_catalog.py`; run willingness-to-pay tests before public launch.

## Quote algorithm principles

- The server is authoritative.
- The formula must be versioned and reproducible.
- Price depends on accepted repair scope and complexity, not merely file size or formula count.
- Repeated instances of the same repair pattern receive a lower marginal weight.
- Macros, external systems, unsupported OOXML parts, low-confidence logic, and encrypted files route to expert review rather than inflated automatic pricing.
- Never change the accepted price during execution without a second user approval.

## Suggested quote calculation

```text
base service fee
+ unique repair-pattern weight
+ number of affected regions weight
+ verification weight
+ fidelity-risk handling
- repeated-pattern efficiency discount
= quoted amount
```

Do not reveal a confusing internal score. Explain quote factors in ordinary language:

- `수식 패턴 2종, 18개 셀`
- `외부 링크 3개 — 삭제 여부 확인 필요`
- `숨겨진 시트 1개 — 유지`
- `매크로 포함 — 자동 수정 제외`

## Scope contract

The payment screen must store and display:

- Analysis ID.
- Quote ID and quote version.
- Included finding IDs/rule codes.
- Excluded finding IDs/rule codes.
- Price and currency.
- Expected outputs.
- Limitations.
- Expiration time.
- User approval timestamp.

## Unexpected findings after payment

Allowed behavior:

1. Finish the accepted safe scope with no additional charge.
2. Skip the newly discovered item.
3. Explain the new issue.
4. Offer a separate optional quote.

Forbidden behavior:

- Automatic additional charge.
- Holding the completed accepted work hostage.
- Quietly changing business logic outside the scope.

## Failed repair handling

Before launch, approve one clear policy. Recommended beta policy:

- If the service cannot produce a valid output for the accepted scope, automatically refund the repair amount.
- Audit/report value may be handled separately only if clearly itemized before payment.
- Preserve technical evidence for dispute handling without preserving workbook contents longer than necessary.

## Pricing experiments

Test in this order:

1. Free scan completion rate.
2. Quote-view rate.
3. Quote acceptance at ₩19k / ₩29k / ₩39k for similar basic scopes.
4. Preference for audit-only vs repaired file.
5. Expert-review lead rate.
6. Refund/support rate.

Do not optimize average order value before proving scan trust and repair success.

## Unit economics guardrail

For each quote tier, track:

- Compute cost.
- Storage/egress cost.
- Payment fee.
- AI cost.
- Expert minutes.
- Support minutes.
- Refund probability.

Automatic work should target high gross margin. Any tier requiring frequent manual intervention must be repriced or moved to expert service.
