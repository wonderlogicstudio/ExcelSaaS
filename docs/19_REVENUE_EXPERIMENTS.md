# Revenue experiments

> M3 note: its formal user-understanding decision uses the 8-person staged protocol in `docs/m3/`, not the 10-person initial-beta hypotheses below. These experiments remain future commercial reference; M3-A adds no tracking, request form, payment, or price experiment.

## Commercial hypothesis

Users will pay for a one-time workbook repair when a free diagnosis creates three forms of certainty:

1. **Problem certainty** — exact evidence shows that a meaningful issue exists.
2. **Scope certainty** — included and excluded work is explicit.
3. **Outcome certainty** — the user receives a separate file, change log, and re-scan rather than an unverified promise.

This must be validated rather than assumed.

## Business model sequence

### Stage 1 — free diagnosis

Purpose: acquire high-intent users and identify real workbook problems.

Cost policy:

- deterministic scan;
- no LLM by default;
- no permanent file storage;
- no account required;
- strict limits against abuse.

### Stage 2 — per-file repair

Initial price hypotheses, not final prices:

| Tier | Hypothesis | Intended case |
|---|---:|---|
| Audit | ₩9,900 | report only or no repairable risk |
| Basic | ₩19,000 | small number of deterministic candidates |
| Standard | ₩39,000 | multiple patterns and confirmation items |
| Advanced | ₩79,000 | complex but bounded, preservation-safe work |
| Expert | separate quote | VBA, model logic, external systems, high fidelity risk |

Do not use discounts to compensate for unclear value. Change the evidence, scope, or target problem first.

### Stage 3 — expert lead conversion

Automation failures should not become generic error pages. High-value complex files can produce a structured expert-review request containing only the approved diagnostic summary and scope questions.

### Stage 4 — repeat/team products

Only after repeat behavior is observed:

- credit packs;
- monthly pre-send checks;
- team workspace;
- governance reports;
- local/private agent.

Do not force subscription pricing before repeat usage is proven.

## Smoke-test experiments

### Experiment A — quote willingness

After a sample or real synthetic scan, enable a non-payment intent button:

> 이 범위와 가격이면 수정 요청

Measure:

- quote viewed;
- intent clicked;
- reason for hesitation;
- selected price reaction;
- expected deliverable.

No card details are collected.

### Experiment B — price ladder

Randomize only the configured quote display for synthetic/demo sessions, never for a real binding quote. Compare clearly documented price hypotheses such as ₩29,000, ₩39,000, and ₩49,000 while keeping scope constant.

Do not optimize only for click rate. Also measure perceived credibility: a price that is too low can make sensitive-file handling look untrustworthy.

### Experiment C — trust message

Test one trust proposition at a time:

- original is never overwritten;
- browser-only quick scan;
- automatic deletion within 24 hours;
- raw workbook is not sent to an AI model;
- exact cell evidence;
- expert review for macros.

The winner is the message that increases completed scans without increasing misunderstanding.

### Experiment D — job-to-be-done landing pages

Create separate pages for high-intent problems and route all to the same scanner:

- `#REF!` repair;
- external-link audit;
- slow workbook diagnosis;
- pre-send workbook check;
- number-stored-as-text audit;
- hidden-sheet audit.

Measure scan completion and quote intent by entry problem.

### Experiment E — expert escalation

On expert-only results, ask:

> 진단 결과를 바탕으로 전문가 견적을 받아보시겠습니까?

Measure qualified requests, average quoted value, delivery effort, and gross margin. This may initially generate more revenue than automated repairs.

## Funnel definitions

```text
Qualified landing session
→ scan/sample started
→ scan completed
→ findings inspected
→ quote inspected
→ repair intent
→ paid order
→ successful delivery
→ no refund/support escalation
→ repeat/referral
```

A page view alone is not a meaningful success metric.

## Initial beta decision thresholds

These are operating hypotheses for the first small sample, not statistical proof:

- 10 user interviews completed.
- At least 8/10 understand the service.
- At least 6/10 consider paying for a real problem file.
- At least 5 users provide a synthetic or safely redacted test case.
- Static scan false positives are reviewed by an Excel expert.
- At least 3 real paid manual-assisted repairs succeed before automating payment at scale.
- No serious original-file corruption, privacy incident, or scope dispute.

## Unit-economics fields

For every paid beta order, record:

- revenue excluding tax/refunds;
- payment fee;
- storage and compute cost;
- AI cost by feature;
- human review minutes;
- support minutes;
- refund/rework cost;
- gross contribution;
- acquisition source;
- repeat or referral outcome.

The pricing engine should ultimately estimate delivery risk, but the business must be calibrated from actual work rather than a complexity formula alone.

## What not to copy from success stories

- Do not treat self-reported revenue as guaranteed outcomes.
- Do not imitate a broad product's current feature list; copy the narrow-entry strategy.
- Do not invent user counts or testimonials to look established.
- Do not spend on broad advertising before one search intent converts.
- Do not hide exclusions behind a low headline price.
- Do not let AI-generated explanations create binding scope or price decisions.
