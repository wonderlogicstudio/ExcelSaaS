---
name: milestone-runner
description: Execute one approved WorkbookCare product milestone autonomously, verify it, update concise project state, create a review package, and stop before the next milestone. Use for implementation, continuation, or review work in this repository. Do not use to start an unapproved milestone.
---

# WorkbookCare milestone runner

1. Read repository `AGENTS.md`.
2. Read `docs/00_CONTEXT_INDEX.md`, `docs/09_CURRENT_MILESTONE.md`, `docs/10_PROGRESS.md`, and `docs/11_DECISIONS.md`.
3. Confirm the current milestone status is `APPROVED`. If it is not, do not implement it.
4. Load only the task-specific documents listed in the context index.
5. Run the current baseline checks relevant to the milestone.
6. Create a concise execution checklist from the milestone acceptance criteria.
7. Implement the smallest coherent changes that satisfy the milestone.
8. Run targeted tests after each focused change; run the full relevant verification before completion.
9. Exercise the changed user flow. Inspect visual output when the milestone changes the UI.
10. Review the diff for security, privacy, Excel-fidelity, accessibility, and scope regressions.
11. Replace `docs/10_PROGRESS.md` with the current concise state.
12. Create or replace `docs/MILESTONE_REVIEW.md` with:
    - milestone and status;
    - user-visible result;
    - files changed;
    - verification commands and outcomes;
    - screenshots/artifacts when available;
    - limitations and risks;
    - product decisions needed;
    - recommendation for the next milestone.
13. Mark the completed milestone status in `docs/09_CURRENT_MILESTONE.md` as `COMPLETED_AWAITING_APPROVAL`, but do not approve or advance it.
14. Stop and wait for the product owner.

## Efficiency rules

- Do not scan the full repository without a concrete need.
- Do not restate specifications in source comments.
- Do not use subagents unless independent work would materially reduce risk.
- Do not add an LLM call when a deterministic rule or template is sufficient.
- Do not fix unrelated issues unless they block the milestone; record them instead.

## Blocking conditions

Stop and document the blocker when the work requires:

- credentials or billing setup;
- domain purchase;
- payment-provider contract;
- legal/privacy approval;
- destructive migration;
- real customer files;
- a change to accepted product direction;
- an unapproved relaxation of security constraints.
