# WorkbookCare repository instructions

## One-defect owner checkpoint — highest local priority

EFFICIENCY-02 in docs/54_AGENT_ORCHESTRATION.md takes priority over EFFICIENCY-01 and historical batch instructions: work on exactly one owner-approved defect, targeted tests including affected type/static checks, one focused review, then report and STOP for explicit owner confirmation before the next defect. Earlier batch approval is not permission to continue through a backlog. Defer expensive Excel/full-regression/deployment/end-to-end checks until relevant code is reviewed and frozen, as a separately confirmed final verification unit; record them as pending, never PASS. Initial attempt plus one correction maximum for the same cause. No duplicate passed tests, full-history forks, idle roles, or extra scope. Current BATCH-01 remains stopped; this settings change does not resume it.


## Cost and scope priority

Follow EFFICIENCY-01 in docs/54_AGENT_ORCHESTRATION.md before the historical broad verification/delegation rules below. Classify the task, run only impact-relevant checks, reuse unchanged evidence, and stop duplicate work. Documentation/operating settings use root only; no agents, product regression or deployment. Local UI does not require full Excel delivery replay or all-repository regression unless affected. Two failed attempts on one cause require reporting and user decision before further escalation.


## Approved PL / Builder / Reviewer operation (2026-09-15)

Follow `docs/54_AGENT_ORCHESTRATION.md` for approved development work. The main conversation is PL/orchestrator: maintain the product premise, one approved work order, exact acceptance and evidence, and hand tasks/results to the builder and independent reviewer. The user does not need to paste commands between roles. Read the corresponding `.codex/agents/*.toml` instructions when the runtime uses generic delegation instead of named agents; do not claim named-role loading or permission enforcement without evidence.

PL edits operating/progress records, not product source. One builder owns approved source edits; the reviewer does not edit product source or expected answers. Use independent agents for the approved workflow, avoid overlapping writes, and do not spawn roles for simple questions. State transitions must reflect actual activity. Preserve previous records and current user changes; this rule supersedes older replace/reset progress instructions.

The product premise and measurable UX targets in that contract are acceptance inputs. Four stages, ten required app activations through all three downloads, and zero mandatory cell-address/formula entry are initial targets, not measured achievements. Never remove exact approval, evidence, security or Excel preservation to meet a click target. Agent approval, customer change approval, owner acceptance and commercial readiness remain separate.

Current explicit user authorization can define one new bounded work unit despite a previously STOPPED milestone. Record that scope in the current milestone; do not reopen historical approvals or infer permission for another unit. Reuse standing beta authorization only within an approved product task. No remote push, live commerce, real data, new paid resources or anonymous release without their explicit authorization.

## Product contract

WorkbookCare diagnoses risky Excel workbooks, explains findings with evidence, quotes an exact repair scope before payment, and produces a separate repaired copy only after approval.

The product owner controls product direction and milestone approval. Codex controls implementation details **inside the currently approved milestone**.

## Mandatory startup sequence

Before modifying code:

1. Read `docs/00_CONTEXT_INDEX.md`.
2. Read `docs/09_CURRENT_MILESTONE.md`.
3. Read only the documents and source files referenced by the current milestone.
4. Inspect `docs/10_PROGRESS.md` and `docs/11_DECISIONS.md`.
5. Establish the current baseline by running the milestone's required checks.

Do not recursively re-read the entire repository unless the current milestone changes architecture.

## Milestone gate

- Implement only the milestone marked `APPROVED` in `docs/09_CURRENT_MILESTONE.md`.
- Do not start the next milestone automatically.
- When acceptance criteria pass, add concise current results to `docs/10_PROGRESS.md` and `docs/MILESTONE_REVIEW.md` while preserving prior records, then stop before the next unapproved unit.
- If blocked by credentials, commercial account setup, legal wording, pricing approval, destructive migration, or unresolved product direction, record the blocker and stop.
- Do not ask the user about ordinary engineering choices that can be resolved from the specifications.

## Token and context discipline

- Prefer targeted file inspection and targeted tests.
- Keep the newest progress summary short and preserve prior records; do not reset progress or rewrite history.
- Do not restate entire specifications in code comments or chat summaries.
- For approved development use the PL/builder/reviewer handoff above; parallelize only independent work and never edit overlapping files. Simple questions do not need subagents.
- Do not add AI/LLM calls when deterministic rules or templates can solve the task.
- Keep each code change focused on one acceptance criterion or one root cause.

## Engineering standards

### Frontend

- React + TypeScript with strict type checking.
- Preserve semantic HTML, keyboard access, visible focus, responsive behavior, and reduced-motion support.
- Do not use fake testimonials, fake customer logos, invented accuracy claims, or invented usage metrics.
- The primary CTA remains a free workbook check unless the product owner approves a positioning change.
- Run type check, unit tests, and production build for every frontend milestone.
- For visual milestones, inspect the running page at desktop and mobile widths. Save screenshots under `artifacts/screenshots/` when the environment supports it.

### Backend

- Python + FastAPI + Pydantic.
- Validate files before opening them as workbooks.
- Never execute VBA, embedded binaries, formulas, external connections, or user-supplied code.
- Never overwrite the uploaded workbook. All future repair output must be a new file.
- Do not claim formulas were recalculated unless an approved, isolated recalculation engine actually ran.
- Protect XML parsing and OOXML ZIP extraction from decompression bombs, path traversal, excessive entry counts, and oversized payloads.
- Run pytest and Ruff for every backend milestone.

### Excel fidelity

`openpyxl` is acceptable for read-only/static analysis and carefully scoped edits, but it must not be used to blindly load and save arbitrary customer workbooks. Unsupported drawings or other OOXML parts can be lost. Detect high-fidelity-risk workbooks and route them to audit-only or expert review until a preservation-safe patch path exists.

### Security and privacy

- Never commit secrets or real customer files.
- Logs must not include workbook cell values, formulas, filenames, email addresses, or presigned URLs unless explicitly redacted.
- AI explanations are disabled by default. Raw workbook data must not be sent to an LLM without a separately approved product and privacy milestone.
- Production uploads must use short-lived signed URLs and automatic deletion.

## Definition of done

A milestone is done only when:

1. Its acceptance criteria are implemented.
2. Relevant tests pass.
3. The changed user flow has been exercised.
4. Known limitations and risks are documented.
5. `docs/10_PROGRESS.md` is current.
6. `docs/MILESTONE_REVIEW.md` contains a concise review package.
7. Codex stops and waits for human approval.
