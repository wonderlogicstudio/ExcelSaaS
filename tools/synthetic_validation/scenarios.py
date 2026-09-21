from __future__ import annotations

from dataclasses import dataclass

INVENTORY_DETAIL_SHEET = "재고 이동"
INVENTORY_SUPPORT_SHEET = "기초 재고"
INVENTORY_TRANSACTIONS_SHEET = "재고 거래"
BOM_CATALOG_SHEET = "Part Catalog"
BUDGET_MONTH_SHEETS = tuple(f"M{month:02d}" for month in range(1, 13))


@dataclass(frozen=True, slots=True)
class Scenario:
    scenario_id: str
    family_id: str
    business_domain: str
    structural_family: str
    sheet_mode: str
    supported_scope: tuple[str, ...]
    exploratory_scope: tuple[str, ...]
    base_sheet: str
    formula_column: str
    start_row: int
    row_count: int
    formula_template: str
    semantic: str
    normal_exception_rows: tuple[int, ...] = ()
    summary_rows: tuple[int, ...] = ()
    table: bool = False
    hidden_support_sheet: bool = False


SCENARIOS: tuple[Scenario, ...] = (
    Scenario(
        scenario_id="retail_sales_vertical",
        family_id="F01-retail-vertical-detail",
        business_domain="retail sales",
        structural_family="single_sheet_vertical_revenue",
        sheet_mode="single",
        supported_scope=("vertical A1 formulas in one detail column",),
        exploratory_scope=("business correctness of discount rates",),
        base_sheet="Sales Detail",
        formula_column="G",
        start_row=12,
        row_count=9,
        formula_template="=E{row}*F{row}",
        semantic="mul_ef",
        normal_exception_rows=(16,),
        summary_rows=(21,),
    ),
    Scenario(
        scenario_id="purchase_orders_table",
        family_id="F02-purchase-table",
        business_domain="purchasing and order management",
        structural_family="excel_table_with_summary_band",
        sheet_mode="table",
        supported_scope=("base static scanner checks",),
        exploratory_scope=("Excel Table formula pattern comparison is intentionally unsupported",),
        base_sheet="PO Lines",
        formula_column="H",
        start_row=8,
        row_count=8,
        formula_template="=F{row}*G{row}",
        semantic="mul_fg",
        normal_exception_rows=(12,),
        summary_rows=(16,),
        table=True,
    ),
    Scenario(
        scenario_id="inventory_cross_sheet",
        family_id="F03-inventory-cross-sheet",
        business_domain="inventory movement",
        structural_family="detail_sheet_references_lookup_sheet",
        sheet_mode="cross_sheet",
        supported_scope=(
            "vertical formulas with quoted Korean sheet references",
            "conditional SUMIFS transaction aggregation",
        ),
        exploratory_scope=("full warehouse reconciliation beyond generated transaction rows",),
        base_sheet=INVENTORY_DETAIL_SHEET,
        formula_column="I",
        start_row=10,
        row_count=9,
        formula_template="=G{row}-H{row}",
        semantic="sub_gh",
        normal_exception_rows=(14,),
        summary_rows=(19,),
    ),
    Scenario(
        scenario_id="budget_horizontal_months",
        family_id="F04-budget-horizontal",
        business_domain="budget versus actual",
        structural_family="horizontal_monthly_matrix",
        sheet_mode="horizontal",
        supported_scope=("base static scanner checks",),
        exploratory_scope=(
            "horizontal formula repetition is outside current M4 column-local engine",
            "separate monthly actual sheets are generated for reference coverage but not M4-scored",
        ),
        base_sheet="Budget",
        formula_column="N",
        start_row=9,
        row_count=6,
        formula_template="=L{row}-M{row}",
        semantic="sub_lm",
        normal_exception_rows=(12,),
    ),
    Scenario(
        scenario_id="payroll_overtime",
        family_id="F05-payroll-overtime",
        business_domain="payroll and attendance",
        structural_family="detail_plus_hidden_rates",
        sheet_mode="hidden_rates",
        supported_scope=("vertical formulas in visible detail sheet",),
        exploratory_scope=("rate policy validation",),
        base_sheet="Payroll",
        formula_column="J",
        start_row=11,
        row_count=9,
        formula_template="=H{row}*I{row}",
        semantic="mul_hi",
        normal_exception_rows=(15,),
        summary_rows=(20,),
        hidden_support_sheet=True,
    ),
    Scenario(
        scenario_id="project_profit",
        family_id="F06-project-profit",
        business_domain="project profit",
        structural_family="multi_section_detail_summary",
        sheet_mode="sections",
        supported_scope=("vertical formulas inside one section",),
        exploratory_scope=("section allocation policy",),
        base_sheet="Project PnL",
        formula_column="K",
        start_row=13,
        row_count=8,
        formula_template="=I{row}-J{row}",
        semantic="sub_ij",
        normal_exception_rows=(17,),
        summary_rows=(21,),
    ),
    Scenario(
        scenario_id="receivables_aging",
        family_id="F07-receivables-aging",
        business_domain="accounts receivable",
        structural_family="aging_buckets_with_manual_adjustment",
        sheet_mode="aging",
        supported_scope=("vertical formulas in amount column",),
        exploratory_scope=("collectability judgment",),
        base_sheet="AR Aging",
        formula_column="H",
        start_row=10,
        row_count=9,
        formula_template="=F{row}-G{row}",
        semantic="sub_fg",
        normal_exception_rows=(13,),
        summary_rows=(19,),
    ),
    Scenario(
        scenario_id="manufacturing_bom",
        family_id="F08-manufacturing-bom",
        business_domain="manufacturing cost",
        structural_family="bom_quantity_cost_rollup",
        sheet_mode="bom",
        supported_scope=(
            "vertical formulas in cost rollup",
            "exact VLOOKUP catalog references",
        ),
        exploratory_scope=("yield-loss policy",),
        base_sheet="BOM Cost",
        formula_column="I",
        start_row=9,
        row_count=10,
        formula_template="=G{row}*H{row}",
        semantic="mul_gh",
        normal_exception_rows=(14,),
        summary_rows=(19,),
    ),
    Scenario(
        scenario_id="cashflow_calendar",
        family_id="F09-cashflow-calendar",
        business_domain="cash flow planning",
        structural_family="dated_cashflow_schedule",
        sheet_mode="dates",
        supported_scope=("vertical formulas in net cash column",),
        exploratory_scope=("cash timing assumptions",),
        base_sheet="Cash Plan",
        formula_column="J",
        start_row=12,
        row_count=12,
        formula_template="=H{row}-I{row}",
        semantic="sub_hi",
        normal_exception_rows=(16,),
        summary_rows=(24,),
    ),
    Scenario(
        scenario_id="subscriptions_kpi",
        family_id="F10-subscriptions-kpi",
        business_domain="subscription KPI",
        structural_family="cohort_kpi_detail",
        sheet_mode="kpi",
        supported_scope=("vertical formulas in KPI detail",),
        exploratory_scope=("retention policy interpretation",),
        base_sheet="KPI Detail",
        formula_column="L",
        start_row=11,
        row_count=9,
        formula_template="=J{row}*K{row}",
        semantic="mul_jk",
        normal_exception_rows=(15,),
        summary_rows=(20,),
    ),
)


FAMILY_ORDER = [scenario.family_id for scenario in SCENARIOS]


def scenario_by_family(family_id: str) -> Scenario:
    for scenario in SCENARIOS:
        if scenario.family_id == family_id:
            return scenario
    raise KeyError(family_id)


