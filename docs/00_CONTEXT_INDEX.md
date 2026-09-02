# Context index

Use this file to avoid loading the full repository into Codex context.

## Always read

- `AGENTS.md` — execution rules and milestone gate.
- `docs/09_CURRENT_MILESTONE.md` — the only approved work scope.
- `docs/10_PROGRESS.md` — concise current state.
- `docs/11_DECISIONS.md` — accepted architectural/product decisions.

## Read by task

| Task | Read these documents |
|---|---|
| Product positioning or copy | `01_PRODUCT_BRIEF.md`, `02_MARKET_POSITIONING.md`, `03_UX_AND_COPY_SPEC.md`, `20_SERVICE_SCOPE.md` |
| Frontend implementation | `03_UX_AND_COPY_SPEC.md`, `12_SUCCESS_METRICS.md`, `13_TEST_PLAN.md` |
| API or scanner | `04_ARCHITECTURE.md`, `05_SECURITY_PRIVACY.md`, `06_DIAGNOSTIC_RULES.md`, `20_SERVICE_SCOPE.md` |
| Quote/pricing | `07_PRICING_AND_QUOTING.md`, `12_SUCCESS_METRICS.md`, `20_SERVICE_SCOPE.md` |
| AI use or cost | `15_AI_TOKEN_BUDGET.md`, `05_SECURITY_PRIVACY.md` |
| Deployment | `04_ARCHITECTURE.md`, `14_HOSTING_DEPLOYMENT.md`, `05_SECURITY_PRIVACY.md` |
| Risk review | `16_RISK_REGISTER.md`, `13_TEST_PLAN.md` |
| Codex operating model | `17_CODEX_OPERATING_GUIDE.md`, `.agents/skills/milestone-runner/SKILL.md` |
| User validation | `18_USER_TEST_PLAYBOOK.md`, `12_SUCCESS_METRICS.md` |
| Revenue validation | `19_REVENUE_EXPERIMENTS.md`, `07_PRICING_AND_QUOTING.md` |
| Market evidence | `research/MARKET_RESEARCH.md`, `research/SOURCES.md` |

## Repository map

- `apps/web/` — React/TypeScript conversion prototype and scan UI.
- `apps/api/` — FastAPI static workbook analyzer.
- `.agents/skills/milestone-runner/` — reusable Codex milestone workflow.
- `prompts/` — first goal, approval, review, and recovery prompts.
- `infra/` — future Cloudflare and Cloud Run deployment notes.
- `samples/` — synthetic workbooks only; no customer data.
- `preview/` — dependency-free offline product preview.
- `artifacts/` — screenshots and verification notes for the supplied baseline.
- `START_HERE_KO.md` — Korean setup, product, and Codex operating guide.

## Context-size rule

Do not read all docs in one pass. A normal milestone should require this index, the current milestone, progress, decisions, and no more than three task-specific docs.
