from __future__ import annotations

from dataclasses import dataclass

from .models import ProductDeliverable, ProductOffering


@dataclass(frozen=True, slots=True)
class ServiceCatalogItem:
    code: str
    label: str
    status: str
    planned_deliverables: tuple[str, ...]
    offering: ProductOffering | None = None


PRECISION_VERIFICATION = ServiceCatalogItem(
    code="PRECISION_VERIFICATION",
    label="정밀 검증",
    status="PLANNED",
    planned_deliverables=(
        "수식 일관성 검사",
        "기술·업무 검증의 지원 및 제외 범위",
        "향후 판매 패키지에 포함할 검증 활동 (별도 보고서 상품 아님)",
    ),
)

APPROVED_REPAIR = ServiceCatalogItem(
    code="APPROVED_REPAIR",
    label="승인 기반 수정",
    status="PLANNED",
    planned_deliverables=(
        "변경 대상과 변경 방법의 사전 미리보기",
        "사용자 승인 후 원본과 분리된 수정본",
        "셀·수식 단위 변경 내역서",
        "수정 후 재검증 보고서",
    ),
    offering=ProductOffering(
        product_id="APPROVED_REPAIR",
        title="승인 기반 수정 패키지",
        capability_status="PLANNED",
        includes_repaired_workbook=True,
        deliverables=[
            ProductDeliverable(
                kind="REPAIRED_WORKBOOK_XLSX",
                label="수정본 XLSX",
                filename="workbookcare_repaired_<job>.xlsx",
            ),
            ProductDeliverable(
                kind="CHANGE_LOG_XLSX", label="변경내역 XLSX", filename="changes_<job>.xlsx"
            ),
            ProductDeliverable(
                kind="REVALIDATION_HTML", label="재검증 HTML", filename="verification_<job>.html"
            ),
        ],
        scope=(
            "지원되는 문제의 정확한 변경계획을 별도로 승인한 뒤 "
            "원본과 분리된 수정본을 받는 패키지입니다."
        ),
        exclusions=[
            "원본 덮어쓰기",
            "결제만으로 변경 실행",
            "승인하지 않은 셀 변경",
            "모든 Excel 오류 해결 보장",
        ],
        next_action="준비 중 · 수정 프로필과 납품 검증 전에는 구매할 수 없습니다.",
    ),
)

AUTOMATION_CONSULTATION = ServiceCatalogItem(
    code="AUTOMATION_CONSULTATION",
    label="자동화 의뢰",
    status="PLANNED",
    planned_deliverables=(
        "현재 파일 구조와 반복 작업의 검토",
        "자동화 가능 범위와 제약 조건 정리",
    ),
)

FREE_DIAGNOSIS = ServiceCatalogItem(
    code="FREE_DIAGNOSIS",
    label="무료 진단",
    status="AVAILABLE",
    planned_deliverables=(),
    offering=ProductOffering(
        product_id="FREE_DIAGNOSIS",
        title="무료 진단",
        capability_status="AVAILABLE",
        includes_repaired_workbook=False,
        deliverables=[
            ProductDeliverable(
                kind="DIAGNOSIS_CSV", label="진단 결과 CSV", filename="workbookcare-diagnosis.csv"
            )
        ],
        scope=(
            "한 파일의 구조적 위험 신호와 위치·근거를 확인하고 "
            "직접 수정한 파일을 같은 화면에서 다시 검사합니다."
        ),
        exclusions=["수정본 생성", "Excel 계산 결과·업무 정답 검증", "두 자료 비교 보고서"],
        next_action="테스트용 파일 무료 진단",
    ),
)

TWO_FILE_COMPARISON = ServiceCatalogItem(
    code="TWO_FILE_COMPARISON",
    label="두 자료 비교",
    status="PLANNED",
    planned_deliverables=("비교 보고서 XLSX", "비교 검증 HTML"),
    offering=ProductOffering(
        product_id="TWO_FILE_COMPARISON",
        title="두 자료 비교 보고서",
        capability_status="PLANNED",
        includes_repaired_workbook=False,
        deliverables=[
            ProductDeliverable(
                kind="COMPARISON_REPORT_XLSX",
                label="비교 보고서 XLSX",
                filename="comparison_report_<job>.xlsx",
            ),
            ProductDeliverable(
                kind="COMPARISON_VERIFICATION_HTML",
                label="비교 검증 HTML",
                filename="comparison_verification_<job>.html",
            ),
        ],
        scope=(
            "같은 정책으로 두 관측자료의 차이를 설명하는 독립 보고서 상품입니다. "
            "비교 자료 B는 정답이 아닙니다."
        ),
        exclusions=["수정본", "정답표", "원본 자동 덮어쓰기", "수정 패키지 실행 권한"],
        next_action="준비 중 · 두 자료 비교와 보고서 생성은 아직 시작하거나 구매할 수 없습니다.",
    ),
)

SERVICE_CATALOG = {
    FREE_DIAGNOSIS.code: FREE_DIAGNOSIS,
    TWO_FILE_COMPARISON.code: TWO_FILE_COMPARISON,
    PRECISION_VERIFICATION.code: PRECISION_VERIFICATION,
    APPROVED_REPAIR.code: APPROVED_REPAIR,
    AUTOMATION_CONSULTATION.code: AUTOMATION_CONSULTATION,
}

# These are beta hypotheses, not validated selling prices or checkout amounts.
BETA_PRICE_RANGES: dict[str, tuple[int, int] | None] = {
    "AUDIT": (9_000, 19_000),
    "BASIC": (19_000, 29_000),
    "STANDARD": (29_000, 49_000),
    "ADVANCED": (49_000, 79_000),
    "EXPERT": None,
}


def get_price_range(tier: str) -> tuple[int, int] | None:
    return BETA_PRICE_RANGES.get(tier)


def get_product_offerings() -> list[ProductOffering]:
    """Product scope is separate from the legacy quote's estimate status."""
    return [
        item.offering.model_copy(deep=True)
        for item in SERVICE_CATALOG.values()
        if item.offering is not None
    ]
