# SCOPE-01


## SCOPE-01 - CHANGES_REQUIRED / STOPPED

Restore now checks nested item-criteria hashes and unused import was removed, but independent review found target-to-criteria binding remains missing. policy_base(item) excludes targets, so separate criteria-hash and candidate-set subset checks still allow target/criteria permutation. No acceptance PASS. Builder reported two scoped Ruff failures and stopped; no post-correction pytest was run.

No new pytest PASS, deployment, commit or push. Historical session 1434 is not current evidence. Existing changes preserved; initial attempt plus one correction exhausted according to builder. Next proposed unit remains the same target-to-criteria binding defect; no next work automatically authorized. Evidence: reviews/evidence/SCOPE-01.json.
