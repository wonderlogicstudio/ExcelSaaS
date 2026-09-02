/goal Prepare this WorkbookCare repository for the next human-approved product milestone without wasting context or expanding scope.

Read AGENTS.md first, then docs/00_CONTEXT_INDEX.md, docs/09_CURRENT_MILESTONE.md, docs/10_PROGRESS.md, and docs/11_DECISIONS.md.

The operating model is mandatory:
- I own product direction and milestone approval.
- You own implementation details only inside the approved milestone.
- One goal equals one milestone.
- Run implementation, tests, visual/manual checks, diff review, and concise documentation autonomously.
- Do not start a milestone whose status is not APPROVED.
- Do not begin the following milestone automatically.
- Stop after producing docs/MILESTONE_REVIEW.md.
- Use the local $milestone-runner skill when available.

First, verify the existing M1/M2 starter baseline. Do not rewrite working code. Because the next milestone is currently awaiting product-owner selection, finish by reporting:
1. whether the starter builds and tests successfully;
2. any concrete baseline defects that block a user test;
3. the exact M3 approval scope you recommend;
4. the shortest approval message I should send.

Do not implement M3 until I explicitly approve it.
