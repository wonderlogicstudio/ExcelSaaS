from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ServiceCatalogItem:
    code: str
    label: str
    status: str
    planned_deliverables: tuple[str, ...]


PRECISION_VERIFICATION = ServiceCatalogItem(
    code="PRECISION_VERIFICATION",
    label="정밀 검증",
    status="PLANNED",
    planned_deliverables=(
        "수식 일관성 검사",
        "수정 후보 수식 또는 수정 방법",
        "변경 전 미리보기와 사용자 승인",
        "원본과 분리된 수정본 및 변경 내역서",
        "수정 전후 비교와 수정 후 재검사 보고서",
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

SERVICE_CATALOG = {
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
