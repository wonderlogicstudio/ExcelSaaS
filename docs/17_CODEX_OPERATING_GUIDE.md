# Codex operating guide

## Operating model

The product owner decides **what outcome matters and whether a milestone is approved**. Codex decides **how to implement the approved scope**. This separation prevents two common failures:

1. the AI continuously adds technically interesting features that do not improve conversion; and
2. the human micromanages files and code, wasting time and context tokens.

## The only recurring workflow

1. Product owner reviews the current demo and `docs/MILESTONE_REVIEW.md`.
2. Product owner approves one milestone in `docs/09_CURRENT_MILESTONE.md`.
3. A single Codex goal is opened using `prompts/02_APPROVE_AND_CONTINUE.md`.
4. Codex reads the context index and only the documents/files necessary for that milestone.
5. Codex implements, tests, documents trade-offs, and creates `docs/MILESTONE_REVIEW.md`.
6. Codex stops. It must not approve its own next milestone.
7. Product owner tests the output and approves, rejects, or narrows the next milestone.

## Do not paste a new implementation recipe for every task

Do not tell Codex which component, function, package, or folder to create unless a product or compliance constraint requires it. Give:

- the user outcome;
- non-negotiable constraints;
- acceptance tests;
- evidence required before stopping.

Bad goal:

> Create `TrackingContext.tsx`, use localStorage, add these exact hooks, then make five buttons.

Better goal:

> Implement the approved privacy-preserving usability instrumentation. It must capture the funnel without filenames, workbook content, formulas, email, or persistent third-party identifiers. Demonstrate the sample journey, export development events, test the schema, update the milestone review, then stop.

## Token-control rules

- One approved milestone per goal.
- Start from `docs/00_CONTEXT_INDEX.md`; do not reread every document.
- Search by symbol or rule code before opening whole source files.
- Use deterministic scripts/tests for verification instead of asking another model to review everything.
- Do not launch parallel agents unless the milestone has truly independent workstreams.
- Do not ask an LLM to inspect raw workbook data when Python rules can answer the question.
- Record durable facts in documents; do not depend on conversation history.
- Keep logs concise and quote only the failure lines needed for diagnosis.
- Stop when acceptance criteria pass; do not polish unrelated areas.

## Product-owner approval template

Use this after reviewing the current milestone:

```text
APPROVE <MILESTONE_ID>.

Outcome:
<What must become true for the user.>

Non-negotiable constraints:
- <privacy/security/business constraints>

Acceptance evidence:
- <tests, screenshots, sample flow, metrics>

Do not implement later milestones. Create docs/MILESTONE_REVIEW.md and stop when this milestone passes.
```

## Review decision template

```text
Decision: APPROVED | CHANGES_REQUIRED | REJECTED
Milestone: <ID>

What worked:
- ...

Required changes before approval:
- ...

Product decisions:
- ...

Next milestone status:
- NOT APPROVED
```

## When Codex should interrupt

Codex should continue with reasonable implementation choices and interrupt only when:

- a secret, payment account, domain, cloud login, or legal identity is required;
- two choices create materially different product behavior or recurring cost;
- an action could delete or expose user data;
- an acceptance criterion is impossible or contradicted by another approved constraint;
- the change requires expanding the approved milestone.

## When the product owner should reject work

Reject or send back the milestone when:

- the demo looks complete but the main CTA does not work;
- metrics or claims are fabricated;
- the implementation silently uploads workbook content to an AI provider;
- the original workbook is overwritten;
- a repair is offered without a reversible preview/change log;
- tests cover code paths but not the stated user outcome;
- Codex advanced into payment, authentication, or cloud storage without approval.
