from __future__ import annotations

from dataclasses import dataclass

from .models import Finding, FindingGuidance, RepairReadiness, ScanResult
from .service_catalog import APPROVED_REPAIR, PRECISION_VERIFICATION


@dataclass(frozen=True, slots=True)
class GuidanceTemplate:
    detected_fact: str
    possible_impact: str
    unchecked_scope: tuple[str, ...]
    recommended_next_checks: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ExcelCheckGuide:
    """User-facing manual checks for one current, deterministic rule.

    These guides describe how to inspect a discovered signal. They do not
    generate a formula, alter a workbook, or infer the user's business rules.
    """

    how_to_check_in_excel: tuple[str, ...]
    when_it_may_be_normal: tuple[str, ...]
    when_action_is_recommended: tuple[str, ...]
    recommended_next_action: str


_CALCULATION_LIMIT = "Excel 계산 결과와 업무 규칙은 이번 검사에서 확인하지 않았습니다."
_PATTERN_LIMIT = "주변 수식의 일관성과 참조 범위의 적절성은 검사하지 않았습니다."

_TEMPLATES: dict[str, GuidanceTemplate] = {
    "FORMULA_REF_ERROR": GuidanceTemplate(
        detected_fact="수식 문자열에서 #REF! 참조 토큰을 확인했습니다.",
        possible_impact="참조가 끊긴 수식은 계산 결과에 영향을 줄 가능성이 있습니다.",
        unchecked_scope=(_CALCULATION_LIMIT, _PATTERN_LIMIT),
        recommended_next_checks=(
            "인접 수식과 참조 범위의 일관성 검사",
            "삭제되거나 이동된 참조의 업무 의도 확인",
        ),
    ),
    "FORMULA_VISIBLE_ERROR_TOKEN": GuidanceTemplate(
        detected_fact="수식 문자열에서 Excel 오류 토큰을 확인했습니다.",
        possible_impact="오류 토큰이 포함된 수식은 계산 결과에 영향을 줄 가능성이 있습니다.",
        unchecked_scope=(_CALCULATION_LIMIT, _PATTERN_LIMIT),
        recommended_next_checks=(
            "오류 토큰이 사용된 수식의 참조 범위 확인",
            "인접 수식과 참조 범위의 일관성 검사",
        ),
    ),
    "FORMULA_EXTERNAL_REFERENCE": GuidanceTemplate(
        detected_fact="수식 문자열에서 외부 통합문서 참조 표기를 확인했습니다.",
        possible_impact=(
            "외부 원본이 이동되거나 갱신되지 않으면 오래된 값이 남을 가능성이 있습니다."
        ),
        unchecked_scope=(
            "외부 파일의 접근 가능 여부와 최신성은 확인하지 않았습니다.",
            _CALCULATION_LIMIT,
        ),
        recommended_next_checks=(
            "외부 통합문서 참조 위치와 원본 파일명 확인",
            "연결 유지 또는 내부 값 전환 방식 검토",
        ),
    ),
    "FORMULA_PATTERN_OUTLIER": GuidanceTemplate(
        detected_fact="같은 열의 주변 반복 수식과 다른 패턴 후보를 확인했습니다.",
        possible_impact=(
            "업무 의도와 다르면 참조 범위나 계산 방식 확인이 필요할 가능성이 있습니다."
        ),
        unchecked_scope=(
            "수식 계산 결과와 업무상 정답 여부는 확인하지 않았습니다.",
            "현재 검사는 지원하는 A1 참조 수식의 제한된 주변 패턴만 비교했습니다.",
        ),
        recommended_next_checks=(
            "대상 셀과 주변 수식의 역할·참조 방식 비교",
            "업무상 예외 계산인지와 수식 범위 확인",
        ),
    ),
    "FORMULA_PATTERN_GAP": GuidanceTemplate(
        detected_fact="반복 수식 영역 안에서 수식이 아닌 값 또는 빈 셀 패턴 후보를 확인했습니다.",
        possible_impact=(
            "업무 의도와 다르면 반복 계산 범위에서 빠진 위치가 있는지 "
            "확인이 필요할 가능성이 있습니다."
        ),
        unchecked_scope=(
            "수식 계산 결과와 업무상 정답 여부는 확인하지 않았습니다.",
            "의도된 수동 입력·구분 행·예외 값인지는 확인하지 않았습니다.",
        ),
        recommended_next_checks=(
            "대상 셀과 위·아래 반복 수식의 역할 비교",
            "수동 값 또는 빈 셀이 의도된 예외인지 확인",
        ),
    ),
    "NUMBER_STORED_AS_TEXT": GuidanceTemplate(
        detected_fact="숫자처럼 보이는 텍스트가 같은 열의 숫자 패턴과 다르게 저장되어 있습니다.",
        possible_impact="합계 또는 조건부 집계에서 누락될 가능성이 있습니다.",
        unchecked_scope=(
            "사번·전화번호·상품코드처럼 텍스트로 유지해야 하는 값인지는 확인하지 않았습니다.",
            _CALCULATION_LIMIT,
        ),
        recommended_next_checks=(
            "숫자 변환 가능 항목과 식별자 항목 분류",
            "합계와 조건부 집계에 미치는 영향 확인",
        ),
    ),
    "FORMULA_VOLATILE": GuidanceTemplate(
        detected_fact="휘발성 함수가 포함된 수식 문자열을 확인했습니다.",
        possible_impact=(
            "수식 수가 많으면 계산 시간이나 파일 열기 속도에 영향을 줄 가능성이 있습니다."
        ),
        unchecked_scope=("실제 계산 시간과 성능 변화는 측정하지 않았습니다.",),
        recommended_next_checks=(
            "휘발성 함수의 사용 위치와 횟수 확인",
            "대체 가능한 함수와 계산 영향 검토",
        ),
    ),
    "FORMULA_DEEP_NESTING": GuidanceTemplate(
        detected_fact="중첩 IF가 깊은 수식 문자열을 확인했습니다.",
        possible_impact="업무 로직을 바꿀 때 수식 유지보수가 어려울 가능성이 있습니다.",
        unchecked_scope=(_CALCULATION_LIMIT, "업무 의도에 맞는 수식인지는 확인하지 않았습니다."),
        recommended_next_checks=(
            "중첩 조건의 업무 규칙과 예외 처리 확인",
            "수식 구조 단순화 가능성 검토",
        ),
    ),
    "FORMULA_WHOLE_COLUMN_REFERENCE": GuidanceTemplate(
        detected_fact="전체 열을 참조하는 수식 문자열을 확인했습니다.",
        possible_impact="수식 수가 많으면 계산량과 파일 성능에 영향을 줄 가능성이 있습니다.",
        unchecked_scope=("실제 계산 시간과 성능 변화는 측정하지 않았습니다.",),
        recommended_next_checks=(
            "전체 열 참조의 사용 위치와 필요 범위 확인",
            "제한된 참조 범위로 변경할 수 있는지 검토",
        ),
    ),
    "SHEET_HIDDEN": GuidanceTemplate(
        detected_fact="숨김 상태의 시트를 확인했습니다.",
        possible_impact=(
            "숨김 시트의 용도를 모르면 수식 참조나 데이터 흐름을 놓칠 가능성이 있습니다."
        ),
        unchecked_scope=("숨김 처리의 업무상 의도는 확인하지 않았습니다.",),
        recommended_next_checks=("숨김 시트의 용도와 참조 관계 확인",),
    ),
    "SHEET_VERY_HIDDEN": GuidanceTemplate(
        detected_fact="일반 메뉴에서 표시할 수 없는 VeryHidden 시트를 확인했습니다.",
        possible_impact="일반적인 시트 목록에서 보이지 않아 유지보수 시 놓칠 가능성이 있습니다.",
        unchecked_scope=("VeryHidden 처리의 업무상 의도는 확인하지 않았습니다.",),
        recommended_next_checks=("VeryHidden 시트의 용도와 참조 관계 확인",),
    ),
    "FILE_MACRO_ENABLED": GuidanceTemplate(
        detected_fact="매크로가 포함된 통합문서 구조를 확인했습니다.",
        possible_impact="매크로 동작과 파일 보존 위험은 별도 검토가 필요할 가능성이 있습니다.",
        unchecked_scope=("VBA 코드를 실행하거나 분석하지 않았습니다.",),
        recommended_next_checks=("VBA 모듈과 매크로 실행 경로의 별도 검토",),
    ),
    "FILE_DRAWING_PARTS": GuidanceTemplate(
        detected_fact="차트·도형·이미지 요소가 포함된 파일 구조를 확인했습니다.",
        possible_impact=(
            "파일을 다시 저장하는 작업은 표시 요소 보존 여부를 "
            "별도로 확인해야 할 가능성이 있습니다."
        ),
        unchecked_scope=("차트·도형·이미지의 내용과 표시 정확도는 확인하지 않았습니다.",),
        recommended_next_checks=("표시 요소의 보존 위험과 수정 범위 검토",),
    ),
}

_PATTERN_RULES = {
    "NUMBER_STORED_AS_TEXT",
    "FORMULA_PATTERN_OUTLIER",
    "FORMULA_PATTERN_GAP",
}
_SIGNAL_RULES = {"MERGED_CELL_HEAVY", "FORMULA_COUNT_HIGH"}

_DEFAULT_TEMPLATE = GuidanceTemplate(
    detected_fact="정적 검사 규칙에서 구조 또는 수식 관련 신호를 확인했습니다.",
    possible_impact="파일 유지보수나 계산 안정성에 영향을 줄 가능성이 있습니다.",
    unchecked_scope=(_CALCULATION_LIMIT, "업무 의도와 데이터의 정확성은 확인하지 않았습니다."),
    recommended_next_checks=("발견 위치와 관련 수식·구조의 추가 확인",),
)

_DEFAULT_CHECK_GUIDE = ExcelCheckGuide(
    how_to_check_in_excel=("표시된 시트와 셀 또는 범위를 Excel에서 확인",),
    when_it_may_be_normal=("업무상 의도된 구조 또는 수식인 경우",),
    when_action_is_recommended=("표시된 위치의 용도와 의도가 불분명한 경우",),
    recommended_next_action=(
        "표시된 위치와 관련 구조를 직접 확인한 뒤 필요하면 같은 파일을 다시 검사하세요."
    ),
)

# Every code in the current M2 static rule table has an explicit manual guide.
_CHECK_GUIDES: dict[str, ExcelCheckGuide] = {
    "FORMULA_REF_ERROR": ExcelCheckGuide(
        how_to_check_in_excel=(
            "표시된 셀의 수식에서 #REF! 부분 확인",
            "인접 수식과 원래 참조해야 할 행·열 범위 확인",
        ),
        when_it_may_be_normal=("현재 구현된 규칙에서는 일반적인 정상 사례로 보지 않습니다.",),
        when_action_is_recommended=("삭제되거나 이동된 참조가 의도된 범위를 가리키지 않는 경우",),
        recommended_next_action="수식의 원래 참조 범위를 확인해 직접 수정한 뒤 다시 검사하세요.",
    ),
    "FORMULA_VISIBLE_ERROR_TOKEN": ExcelCheckGuide(
        how_to_check_in_excel=(
            "표시된 셀의 수식에서 오류 토큰과 참조 위치 확인",
            "관련 원본 셀과 인접 수식의 의도 확인",
        ),
        when_it_may_be_normal=("오류 처리를 위해 수식 문자열에 토큰을 의도적으로 포함한 경우",),
        when_action_is_recommended=("토큰이 실제 참조 오류 또는 잘못된 수식을 의미하는 경우",),
        recommended_next_action=(
            "참조와 업무 의도를 확인한 뒤 직접 수정하거나 정밀 검증 범위를 검토하세요."
        ),
    ),
    "FORMULA_EXTERNAL_REFERENCE": ExcelCheckGuide(
        how_to_check_in_excel=(
            "수식의 대괄호 안 외부 파일명 확인",
            "데이터 탭의 연결 또는 쿼리에서 연결 유지 필요 여부 확인",
            "다른 PC에서도 해당 외부 파일에 접근해야 하는지 확인",
        ),
        when_it_may_be_normal=("기준 데이터나 다른 보고서를 의도적으로 연결한 경우",),
        when_action_is_recommended=(
            "외부 파일이 없거나 오래된 파일을 참조하거나 단독 배포가 필요한 경우",
        ),
        recommended_next_action=(
            "연결을 유지할지, 내부 값으로 전환할지 확인한 뒤 필요하면 수정하고 다시 검사하세요."
        ),
    ),
    "FORMULA_PATTERN_OUTLIER": ExcelCheckGuide(
        how_to_check_in_excel=(
            "표시된 셀과 비교 위치의 수식을 수식 입력줄에서 나란히 확인",
            "함수·참조 방식 차이가 업무상 의도된 예외인지 확인",
        ),
        when_it_may_be_normal=(
            "소계, 예외 계산, 의도적으로 다른 참조 범위를 쓰는 행인 경우",
        ),
        when_action_is_recommended=(
            "대상 셀의 역할을 설명하기 어렵거나 주변 행과 같은 계산이어야 하는 경우",
        ),
        recommended_next_action=(
            "수식 의도와 주변 패턴을 직접 확인한 뒤, 필요하면 정밀 검증 범위를 검토하세요."
        ),
    ),
    "FORMULA_PATTERN_GAP": ExcelCheckGuide(
        how_to_check_in_excel=(
            "표시된 셀이 수식·상수·빈 셀 중 무엇인지와 위·아래 수식을 확인",
            "반복 수식이 이 위치까지 적용되어야 하는 업무 구간인지 확인",
        ),
        when_it_may_be_normal=(
            "의도된 수동 입력, 구분 행, 보류 행 또는 예외 값인 경우",
        ),
        when_action_is_recommended=(
            "주변 반복 수식과 같은 계산이 이 위치에도 필요하다고 판단되는 경우",
        ),
        recommended_next_action=(
            "업무상 예외 여부를 먼저 확인하고, 직접 수정했다면 같은 파일을 다시 검사하세요."
        ),
    ),
    "NUMBER_STORED_AS_TEXT": ExcelCheckGuide(
        how_to_check_in_excel=(
            "표시된 셀의 숫자 서식과 왼쪽 정렬 여부 확인",
            "같은 열의 값과 함께 합계 또는 조건부 집계에 포함되는지 확인",
        ),
        when_it_may_be_normal=(
            "사번·전화번호·상품코드처럼 앞자리 0을 보존해야 하는 식별자인 경우",
        ),
        when_action_is_recommended=("산술 계산 또는 집계에 쓰이는 값인데 텍스트로 저장된 경우",),
        recommended_next_action=(
            "업무상 숫자 값인지 확인한 뒤 Excel의 숫자 변환을 사용하고 다시 검사하세요."
        ),
    ),
    "FORMULA_VOLATILE": ExcelCheckGuide(
        how_to_check_in_excel=(
            "표시된 수식에서 INDIRECT, OFFSET 등 함수 확인",
            "파일을 열거나 값을 바꿀 때 계산 지연이 있는지 관찰",
        ),
        when_it_may_be_normal=("실시간 날짜·난수·동적 참조가 업무상 필요한 경우",),
        when_action_is_recommended=("계산 지연이 반복되거나 대체 함수가 가능한 경우",),
        recommended_next_action=(
            "함수의 필요성을 확인하고, 성능 문제가 있을 때만 대체 방식을 검토하세요."
        ),
    ),
    "FORMULA_DEEP_NESTING": ExcelCheckGuide(
        how_to_check_in_excel=(
            "표시된 수식의 IF 조건과 예외 처리 순서 확인",
            "조건마다 어떤 업무 규칙을 표현하는지 확인",
        ),
        when_it_may_be_normal=("복잡한 예외 규칙을 한 셀에 명시적으로 표현한 경우",),
        when_action_is_recommended=("규칙 변경이 잦거나 수식 이해·유지가 어려운 경우",),
        recommended_next_action="조건의 업무 의미를 정리한 뒤 구조 단순화가 필요한지 검토하세요.",
    ),
    "FORMULA_WHOLE_COLUMN_REFERENCE": ExcelCheckGuide(
        how_to_check_in_excel=(
            "표시된 수식에서 전체 열 참조 범위 확인",
            "실제 데이터 범위와 계산 지연 여부 확인",
        ),
        when_it_may_be_normal=("데이터 행 수가 자주 늘어나고 성능 문제가 없는 경우",),
        when_action_is_recommended=("수식 수가 많거나 계산·열기 속도가 느린 경우",),
        recommended_next_action=(
            "성능 문제가 확인될 때 실제 데이터 범위로 제한할 수 있는지 검토하세요."
        ),
    ),
    "SHEET_HIDDEN": ExcelCheckGuide(
        how_to_check_in_excel=(
            "Excel의 시트 탭에서 숨김 해제 메뉴로 시트 이름 확인",
            "수식이 해당 시트를 참조하는지 확인",
        ),
        when_it_may_be_normal=("입력 보조 데이터나 보고서용 중간 계산을 의도적으로 숨긴 경우",),
        when_action_is_recommended=("숨김 시트의 용도나 참조 관계를 설명할 수 없는 경우",),
        recommended_next_action="시트의 용도와 참조 관계를 확인한 뒤 숨김 유지 여부를 결정하세요.",
    ),
    "SHEET_VERY_HIDDEN": ExcelCheckGuide(
        how_to_check_in_excel=(
            "VBA 편집기 또는 시트 속성에서 VeryHidden 상태와 시트 이름 확인",
            "참조 수식과 보호 목적을 확인",
        ),
        when_it_may_be_normal=("보호용 보조 시트를 의도적으로 일반 메뉴에서 숨긴 경우",),
        when_action_is_recommended=("시트의 용도·접근 권한·참조 관계가 불명확한 경우",),
        recommended_next_action=(
            "파일 관리 책임자와 용도를 확인한 뒤 표시 상태 변경 여부를 판단하세요."
        ),
    ),
    "FILE_MACRO_ENABLED": ExcelCheckGuide(
        how_to_check_in_excel=(
            "파일을 신뢰할 수 있는 환경에서 열어 매크로 사용 목적 확인",
            "개발 도구 탭에서 VBA 모듈과 실행 경로를 별도로 검토",
        ),
        when_it_may_be_normal=("신뢰할 수 있는 내부 자동화에 매크로가 필요한 경우",),
        when_action_is_recommended=("출처가 불분명하거나 다른 사용자에게 배포해야 하는 경우",),
        recommended_next_action="매크로는 실행하지 말고 별도 전문가 검토 범위를 먼저 정하세요.",
    ),
    "FILE_DRAWING_PARTS": ExcelCheckGuide(
        how_to_check_in_excel=(
            "차트·도형·이미지가 업무상 필요한지 확인",
            "수정 전 파일 사본에서 표시 요소 보존 요구를 확인",
        ),
        when_it_may_be_normal=("보고서·대시보드 표시를 위해 차트나 도형을 사용하는 경우",),
        when_action_is_recommended=("파일을 다시 저장하거나 구조를 바꾸려는 경우",),
        recommended_next_action="표시 요소 보존이 필요하면 수정 전에 전문가 검토를 받으세요.",
    ),
    "MERGED_CELL_HEAVY": ExcelCheckGuide(
        how_to_check_in_excel=(
            "병합 셀을 사용하는 보고서 영역과 입력·정렬 영역을 구분",
            "필터·복사·자동화가 필요한 범위에 병합이 있는지 확인",
        ),
        when_it_may_be_normal=("인쇄용 보고서 레이아웃에만 병합을 사용한 경우",),
        when_action_is_recommended=("데이터 정렬, 필터, 복사 또는 자동화가 자주 실패하는 경우",),
        recommended_next_action="입력·처리 영역부터 병합 해제 필요 여부를 검토하세요.",
    ),
    "FORMULA_COUNT_HIGH": ExcelCheckGuide(
        how_to_check_in_excel=(
            "통합문서의 수식 사용 영역과 계산 지연 여부 확인",
            "불필요한 중복 수식이나 전체 열 참조가 있는지 확인",
        ),
        when_it_may_be_normal=("대형 모델이나 월별·일별 계산표처럼 많은 수식이 필요한 경우",),
        when_action_is_recommended=("파일 열기·저장·계산 속도가 업무에 영향을 주는 경우",),
        recommended_next_action="성능 문제가 있을 때 수식 구조와 계산 범위를 정밀 검토하세요.",
    ),
    "SCAN_CELL_LIMIT_REACHED": ExcelCheckGuide(
        how_to_check_in_excel=("이번 결과가 일부 셀만 검사했다는 점을 먼저 확인",),
        when_it_may_be_normal=("현재 무료 검사 안전 제한을 넘는 대형 파일인 경우",),
        when_action_is_recommended=("전체 파일 범위 확인이 필요한 경우",),
        recommended_next_action=(
            "이 결과만으로 전체 파일을 판단하지 말고 더 큰 검사 범위를 별도로 검토하세요."
        ),
    ),
    "DEFINED_NAME_BROKEN_REF": ExcelCheckGuide(
        how_to_check_in_excel=(
            "수식 탭의 이름 관리자에서 표시된 이름과 참조 대상 확인",
            "삭제·이동된 시트 또는 셀을 다시 연결해야 하는지 확인",
        ),
        when_it_may_be_normal=("더 이상 사용하지 않는 이름을 정리 대상으로 남겨 둔 경우",),
        when_action_is_recommended=("해당 이름을 참조하는 수식 또는 차트가 남아 있는 경우",),
        recommended_next_action=(
            "이름의 사용처와 원래 참조 범위를 확인한 뒤 직접 정리하거나 정밀 검토하세요."
        ),
    ),
}


def _repair_readiness(finding: Finding) -> RepairReadiness:
    """Describe a future-safe path without promising an available repair."""
    if finding.repair_class == "SAFE_CANDIDATE":
        return RepairReadiness(
            status="REPAIR_CANDIDATE_AFTER_APPROVAL",
            label="향후 승인 후 수정 검토 대상",
            explanation=(
                "현재는 정적 분류만 제공하며, 정밀 검증·변경 전 미리보기·사용자 승인이 "
                "끝나기 전에는 수정하지 않습니다."
            ),
            required_steps=[
                "정밀 검증",
                "변경 전 미리보기",
                "사용자 승인",
                "수정 후 재검증",
            ],
            planned_service_codes=[
                PRECISION_VERIFICATION.code,
                APPROVED_REPAIR.code,
            ],
        )
    if finding.repair_class == "CONFIRMATION_REQUIRED":
        return RepairReadiness(
            status="USER_DECISION_REQUIRED",
            label="사용자 결정 후 수정 검토 대상",
            explanation=(
                "업무 의도에 따라 유지 또는 변경 판단이 달라질 수 있어, "
                "사용자 확인 전에는 수정하지 않습니다."
            ),
            required_steps=[
                "업무 의도 확인",
                "정밀 검증",
                "변경 전 미리보기",
                "사용자 승인",
                "수정 후 재검증",
            ],
            planned_service_codes=[
                PRECISION_VERIFICATION.code,
                APPROVED_REPAIR.code,
            ],
        )
    if finding.repair_class == "EXPERT_REVIEW":
        return RepairReadiness(
            status="PRECISION_VERIFICATION_REQUIRED",
            label="정밀 검증 선행 대상",
            explanation=(
                "수식 의미나 파일 충실도에 영향을 줄 수 있어, 현재 자동으로 수정하거나 "
                "수정 가능하다고 판단하지 않습니다."
            ),
            required_steps=[
                "정밀 검증",
                "수정 방법 검토",
                "변경 전 미리보기",
                "사용자 승인",
                "수정 후 재검증",
            ],
            planned_service_codes=[
                PRECISION_VERIFICATION.code,
                APPROVED_REPAIR.code,
            ],
        )
    return RepairReadiness(
        status="INFORMATION_ONLY",
        label="즉시 수정 대상 아님",
        explanation=(
            "현재는 유지보수·성능·구조 판단에 참고하는 정보이며 수정 경로를 제안하지 않습니다."
        ),
        required_steps=[],
    )


def _evidence_grade(rule_code: str) -> str:
    if rule_code in _PATTERN_RULES:
        return "PATTERN_INFERENCE"
    if rule_code in _SIGNAL_RULES:
        return "REFERENCE_SIGNAL"
    return "DIRECT_CONFIRMATION"


def _action_guidance(finding: Finding) -> tuple[str, str, bool]:
    """Map an existing repair class to the user's next-action category."""
    if finding.formula_pattern is not None:
        return "DEEP_VALIDATION_REQUIRED", "CURRENTLY_NOT_SUPPORTED", True
    if finding.repair_class == "SAFE_CANDIDATE":
        return "FIX_RECOMMENDED", "MANUAL_GUIDANCE_AVAILABLE", False
    if finding.repair_class == "CONFIRMATION_REQUIRED":
        return "USER_CONFIRMATION", "USER_CONFIRMATION_REQUIRED", True
    if finding.repair_class == "EXPERT_REVIEW":
        return "DEEP_VALIDATION_REQUIRED", "EXPERT_REVIEW_REQUIRED", True
    return "INFO_ONLY", "NOT_APPLICABLE", False


def build_finding_guidance(finding: Finding) -> FindingGuidance:
    template = _TEMPLATES.get(finding.rule_code, _DEFAULT_TEMPLATE)
    check_guide = _CHECK_GUIDES.get(finding.rule_code, _DEFAULT_CHECK_GUIDE)
    action_category, repair_eligibility, user_confirmation_required = _action_guidance(finding)
    return FindingGuidance(
        evidence_grade=_evidence_grade(finding.rule_code),  # type: ignore[arg-type]
        action_category=action_category,  # type: ignore[arg-type]
        repair_eligibility=repair_eligibility,  # type: ignore[arg-type]
        user_confirmation_required=user_confirmation_required,
        detected_fact=template.detected_fact,
        possible_impact=template.possible_impact,
        how_to_check_in_excel=list(check_guide.how_to_check_in_excel),
        when_it_may_be_normal=list(check_guide.when_it_may_be_normal),
        when_action_is_recommended=list(check_guide.when_action_is_recommended),
        recommended_next_action=check_guide.recommended_next_action,
        unchecked_scope=list(template.unchecked_scope),
        recommended_next_checks=list(template.recommended_next_checks),
        recommended_service_code=(
            PRECISION_VERIFICATION.code
            if action_category == "DEEP_VALIDATION_REQUIRED"
            else None
        ),
        repair_readiness=_repair_readiness(finding),
    )


def add_finding_guidance(findings: list[Finding]) -> list[Finding]:
    return [
        finding.model_copy(update={"guidance": build_finding_guidance(finding)})
        for finding in findings
    ]


def enrich_scan_result(result: ScanResult) -> ScanResult:
    """Add deterministic result guidance without changing scanner findings or summary."""
    return result.model_copy(update={"findings": add_finding_guidance(result.findings)})
