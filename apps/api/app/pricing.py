from __future__ import annotations

from .models import DiagnosisSummary, Finding, QuotePreview, WorkbookSummary
from .service_catalog import PRECISION_VERIFICATION, get_price_range


def build_quote(
    summary: DiagnosisSummary,
    workbook: WorkbookSummary,
    findings: list[Finding],
) -> QuotePreview:
    factors: list[str] = []
    excluded: list[str] = []

    band_label = {
        "basic": "기본 난이도",
        "standard": "표준 난이도",
        "advanced": "고급 난이도",
        "expert": "전문가 난이도",
    }[summary.complexity_band]
    factors.append(band_label)

    if workbook.formula_count:
        factors.append(f"수식 {workbook.formula_count:,}개")
    if summary.safe_candidate_count:
        factors.append(f"자동 수정 후보 {summary.safe_candidate_count}건")
    if summary.confirmation_required_count:
        factors.append(f"확인 필요 {summary.confirmation_required_count}건")

    if workbook.has_macros:
        excluded.append("VBA 매크로 분석·실행·수정")
    if workbook.external_link_count:
        excluded.append("외부 파일이나 시스템의 실제 데이터 검증")
    if workbook.drawing_part_count:
        excluded.append("차트·도형·이미지의 디자인 재구성")
    if summary.expert_review_count:
        excluded.append("업무 의미가 필요한 수식 로직 재설계")

    expert_required = (
        summary.complexity_band == "expert"
        or workbook.has_macros
        or summary.expert_review_count >= 5
    )

    if expert_required:
        return QuotePreview(
            status="EXPERT_REVIEW",
            tier="EXPERT",
            amount=None,
            headline="현재 정적 검사만으로는 정밀검증의 예상 범위와 가격 가설을 정할 수 없습니다.",
            included=[
                "현재 탐지된 구조 위험 신호 검토",
                "정밀검증 예상 범위와 수정 가능성 분류",
                "변경 계획에 필요한 추가 확인 항목",
            ],
            excluded=excluded or ["승인되지 않은 자동 변경"],
            factors=factors,
            pricing_note="베타 가격 가설은 아직 설정되지 않았으며 현재 결제는 진행되지 않습니다.",
            service_code=PRECISION_VERIFICATION.code,
            service_status=PRECISION_VERIFICATION.status,
            planned_deliverables=list(PRECISION_VERIFICATION.planned_deliverables),
        )

    if summary.issue_count == 0 or (
        summary.critical_count == 0
        and summary.warning_count == 0
        and summary.info_count > 0
    ):
        tier = "AUDIT"
        amount = 9_900
    elif summary.complexity_band == "basic":
        tier = "BASIC"
        amount = 19_000
    elif summary.complexity_band == "standard":
        tier = "STANDARD"
        amount = 39_000
    else:
        tier = "ADVANCED"
        amount = 79_000

    included = [
        "현재 탐지된 구조 위험 신호 검토",
        "정밀검증 예상 범위와 수정 가능성 분류",
        "변경 계획에 필요한 추가 확인 항목",
    ]
    if summary.safe_candidate_count == 0:
        included[1] = "규칙상 자동 수정 후보가 없는 항목의 상세 검토"

    price_range = get_price_range(tier)
    amount_min, amount_max = price_range if price_range else (None, None)

    return QuotePreview(
        status="AVAILABLE",
        tier=tier,
        amount=amount,
        headline=(
            "현재 탐지된 구조 문제와 정밀검증 예상 범위를 기준으로 한 참고용 예상 금액입니다."
        ),
        included=included,
        excluded=excluded or ["신규 대시보드·VBA·업무 프로세스 개발"],
        factors=factors,
        amount_min=amount_min,
        amount_max=amount_max,
        pricing_note=(
            "베타 가격 가설이며 현재 결제는 진행되지 않습니다. "
            "최종 작업 범위와 가격은 향후 사용자 확인 후 확정됩니다."
        ),
        service_code=PRECISION_VERIFICATION.code,
        service_status=PRECISION_VERIFICATION.status,
        planned_deliverables=list(PRECISION_VERIFICATION.planned_deliverables),
    )
