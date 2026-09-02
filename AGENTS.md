# WorkbookCare repository instructions

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
- When acceptance criteria pass, update `docs/10_PROGRESS.md`, create or replace `docs/MILESTONE_REVIEW.md`, and stop for human approval.
- If blocked by credentials, commercial account setup, legal wording, pricing approval, destructive migration, or unresolved product direction, record the blocker and stop.
- Do not ask the user about ordinary engineering choices that can be resolved from the specifications.

## Token and context discipline

- Prefer targeted file inspection and targeted tests.
- Keep progress notes short and replace stale status instead of appending a diary.
- Do not restate entire specifications in code comments or chat summaries.
- Do not invoke subagents by default. Use them only for genuinely independent research or review, never to edit overlapping files.
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
