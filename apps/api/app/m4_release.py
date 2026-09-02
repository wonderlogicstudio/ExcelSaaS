"""Fixed M4 release-candidate identifiers and approved evaluation waiver.

The waiver is deliberately narrow: it preserves the immutable source labels
and accepts only the two contradictory labels reviewed by the product owner
on 2026-09-02. Any other evaluation failure still fails closed.
"""

M4_FORMULA_AUDIT_RELEASE_CANDIDATE_VERSION = "m4-formula-audit-rc1"
M4_C_PRODUCT_OWNER_WAIVER_ID = "M4C-2026-09-02-source-label-conflict"

M4_C_WAIVED_SOURCE_CONFLICTS = frozenset(
    {
        (
            "WorkbookCare_M4C_Additional_Pack",
            "18_공통비_원가배부.xlsx",
            "배부계산",
            "E13",
            "D6:I13",
        ),
        (
            "WorkbookCare_M4C_Additional_Pack",
            "18_공통비_원가배부.xlsx",
            "배부계산",
            "F22",
            "D22:I29",
        ),
    }
)
