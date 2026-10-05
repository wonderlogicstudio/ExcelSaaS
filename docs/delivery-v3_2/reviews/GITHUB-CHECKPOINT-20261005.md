# WorkbookCare GitHub checkpoint - 2026-10-05

Owner explicitly requested committing and pushing the original ExcelSaaS checkout to origin/main. This snapshot archives existing operating documents, the delivery instruction package, and synthetic validation/review evidence. No product feature, repair rule, model generation or deployment is part of this unit.

Base commit: da9041f6460bb88350ed2423969f561683d0428e. Historical PASS, FAILED, PARTIAL and NOT_RUN evidence is preserved without promoting readiness. Product implementation source is unchanged.

Local-LLM work remains in the separate ExcelSaaS-local-llm-20260929 worktree and is not merged into this product checkpoint. Its latest CLAIM-RUN-01 screen failed; no model connection to customer files was performed.

Manifest: artifacts/github-checkpoint-20261005/publication-manifest.json. Generated container images, Vite caches, private runtime state and pytest temporary folders stay local and are excluded through .gitignore. Existing dependency, secret, log and generated-workbook exclusions remain. Three public synthetic delivery examples are explicitly included with their existing DEMO hashes; they are not product-delivery proof.

Exact-byte attributes preserve newly archived evidence where line-ending conversion would invalidate pinned hashes. Existing operating text follows the repository line-ending policy. JSON files parse with encoding-aware loading. One existing PowerShell UTF16-BOM JSON capture is preserved verbatim, not recoded. Credential-signature scanning found no actual credential signatures in the publication set; the embedded verifier's detection regex is a reviewed false positive.

No unchanged product test suites were rerun for this publication-only checkpoint. Final publication is verified by comparing actual remote main to local HEAD after push; the commit hash is determined when this record is committed.
