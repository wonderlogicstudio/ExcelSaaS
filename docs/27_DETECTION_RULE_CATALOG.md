# Detection Rule Catalog — M4 Planning

## 읽는 법

이 카탈로그는 구현 백로그가 아니라 탐지 계약의 후보 목록이다. `PLANNED`는 승인된 작업이 아니며, `FREE_VISIBLE`도 이미 제공 중이라는 뜻이 아니라 실제 공개 상태 또는 그 후보 상태를 나타낸다.

- 상대 등급 `LOW` / `MEDIUM` / `HIGH`는 시장 통계가 아닌 검토 우선순위를 위한 통제값이다.
- `quality_gate_requirements`는 `docs/26_DETECTION_COVERAGE_BLUEPRINT.md`의 공통 품질 게이트를 가리킨다. 모든 게이트에는 합성 target·normal·unsupported 코퍼스, 성능 예산, 민감 정보 비노출, 사용자 설명·Excel 확인 방법, 실패 시 비공개 규칙이 포함된다.
- `repair_eligibility=FUTURE_CANDIDATE`는 향후 정밀 검증·변경 미리보기·사용자 승인·별도 수정본·재검증을 거쳐 검토할 수 있다는 뜻이다. 자동 수정 또는 수정 수식 제안이 아니다.
- `exposure_status`는 `INTERNAL_ONLY`, `M4_B_CANDIDATE`, `FREE_VISIBLE`, `WITHHELD` 중 하나이고, `quality_gate_status`는 `NOT_EVALUATED`, `PASSED_SYNTHETIC`, `CONDITIONAL`, `FAILED` 중 하나다.

## 1. 파일·구조 무결성

### `FILE_OOXML_ENVELOPE_LIMIT`

- `rule_code`: `FILE_OOXML_ENVELOPE_LIMIT`
- `rule_name`: OOXML 안전 한계 초과 또는 파싱 불가 경계
- `detection_layer`: OOXML ZIP envelope validation
- `user_problem`: 안전하지 않거나 손상된 파일을 정상 진단 파일처럼 처리하지 않음
- `detection_method`: 압축 크기·항목 수·경로·콘텐츠 유형·파싱 가능 여부를 열기 전에 검사
- `required_context`: 없음; 파일 자체의 안전 한계만 사용
- `evidence`: 차단 사유 코드와 안전한 오류 메시지. 셀 값·수식은 사용하지 않음
- `normal_exceptions`: 없음. 지원 범위를 벗어난 파일은 finding이 아니라 안전한 중단 대상
- `false_positive_risk`: LOW / `false_negative_risk`: MEDIUM
- `explainability`: HIGH / `actionability`: 다른 안전한 사본 또는 전문가 검토 / `repair_eligibility`: NONE
- `business_impact`: HIGH / `expected_frequency`: LOW / `implementation_cost`: MEDIUM
- `recommended_tier`: Free safety boundary / `recommended_milestone`: M0–M2 유지보수 / `free_or_paid_candidate`: NOT_A_SEPARATE_PRODUCT_FINDING
- `current_status`: IMPLEMENTED / `quality_gate_status`: PASSED_SYNTHETIC / `exposure_status`: WITHHELD
- `priority_rationale`: 진단 정확도보다 먼저 사용자 파일과 서비스의 안전 경계를 보장한다.
- `quality_gate_requirements`: `QG-S1`; 거부 테스트는 정상 파일과 악성/손상/비지원 파일을 모두 포함하며, 실패하면 업로드 처리를 중단한다.

### `FILE_MACRO_ENABLED`

- `rule_code`: `FILE_MACRO_ENABLED`
- `rule_name`: 매크로 포함 통합문서
- `detection_layer`: OOXML package metadata
- `user_problem`: 실행되지 않은 VBA가 포함된 파일을 자동 수정 가능 파일로 오해하지 않음
- `detection_method`: 매크로 포함 OOXML 파트 탐지
- `required_context`: 없음
- `evidence`: 매크로 포함 여부만 표시; 매크로 내용은 읽거나 실행하지 않음
- `normal_exceptions`: 승인된 매크로 통합문서는 정상일 수 있음
- `false_positive_risk`: LOW / `false_negative_risk`: LOW
- `explainability`: HIGH / `actionability`: 용도 확인 후 전문가 검토 / `repair_eligibility`: EXPERT_ONLY
- `business_impact`: HIGH / `expected_frequency`: MEDIUM / `implementation_cost`: LOW
- `recommended_tier`: Free static safety signal / `recommended_milestone`: M0–M2 유지 / `free_or_paid_candidate`: FREE_STATIC_CANDIDATE
- `current_status`: IMPLEMENTED / `quality_gate_status`: PASSED_SYNTHETIC / `exposure_status`: FREE_VISIBLE
- `priority_rationale`: 실행하지 않아도 명확한 보존·보안 경계를 설명할 수 있다.
- `quality_gate_requirements`: `QG-S1`; macro/non-macro 합성 파일에서 판별하고, 어떠한 실행·저장도 발생하지 않으면 공개 가능하다.

### `FILE_DRAWING_PARTS`

- `rule_code`: `FILE_DRAWING_PARTS`
- `rule_name`: 차트·도형·이미지 포함에 따른 보존 위험
- `detection_layer`: OOXML package metadata
- `user_problem`: 도형이 있는 파일을 향후 단순 라이브러리로 저장해도 동일하게 보존된다고 믿지 않음
- `detection_method`: drawing 관련 OOXML 파트 수 탐지
- `required_context`: 없음
- `evidence`: drawing part 존재 수만 표시
- `normal_exceptions`: 차트나 이미지 자체는 오류가 아님
- `false_positive_risk`: LOW / `false_negative_risk`: LOW
- `explainability`: HIGH / `actionability`: 정적 진단만 사용하고 향후 수정은 보존성 검토 / `repair_eligibility`: EXPERT_ONLY
- `business_impact`: MEDIUM / `expected_frequency`: MEDIUM / `implementation_cost`: LOW
- `recommended_tier`: Free static safety signal / `recommended_milestone`: M0–M2 유지 / `free_or_paid_candidate`: FREE_STATIC_CANDIDATE
- `current_status`: IMPLEMENTED / `quality_gate_status`: PASSED_SYNTHETIC / `exposure_status`: FREE_VISIBLE
- `priority_rationale`: 오류 탐지가 아니라 안전한 Repair 경계에 직접 연결된다.
- `quality_gate_requirements`: `QG-S1`; drawing 유무 코퍼스와 값 없는 근거, 수정 불가 경계 설명이 필요하다.

### `SHEET_HIDDEN` / `SHEET_VERY_HIDDEN`

- `rule_code`: `SHEET_HIDDEN`, `SHEET_VERY_HIDDEN`
- `rule_name`: 숨김·VeryHidden 시트 존재
- `detection_layer`: workbook structure metadata
- `user_problem`: 보이지 않는 시트가 의도된 보조 영역인지 검토하지 않고 공유·수정하는 위험
- `detection_method`: worksheet visibility state 읽기
- `required_context`: 없음
- `evidence`: 숨김 상태와 위치 정보; 시트 값은 노출하지 않음
- `normal_exceptions`: 보조 계산·템플릿·관리 시트를 의도적으로 숨긴 경우
- `false_positive_risk`: MEDIUM / `false_negative_risk`: LOW
- `explainability`: HIGH / `actionability`: Excel에서 숨김 해제/용도 확인 / `repair_eligibility`: FUTURE_CANDIDATE
- `business_impact`: MEDIUM / `expected_frequency`: MEDIUM / `implementation_cost`: LOW
- `recommended_tier`: Free static signal / `recommended_milestone`: M0–M2 유지 / `free_or_paid_candidate`: FREE_STATIC_CANDIDATE
- `current_status`: IMPLEMENTED / `quality_gate_status`: PASSED_SYNTHETIC / `exposure_status`: FREE_VISIBLE
- `priority_rationale`: 발견 사실은 분명하지만 의도를 알 수 없어 확인 요구로만 표현한다.
- `quality_gate_requirements`: `QG-S1`; hidden/veryHidden/visible 합성 사례와 정상 용도 설명·Excel 확인법이 필요하다.

### `SCAN_CELL_LIMIT_REACHED`

- `rule_code`: `SCAN_CELL_LIMIT_REACHED`
- `rule_name`: 검사 셀 한계 도달
- `detection_layer`: scanner execution boundary
- `user_problem`: 일부만 검사된 결과를 파일 전체 확인으로 오해하지 않음
- `detection_method`: 사전 설정된 셀 수 한계에서 스캔 중단 여부 기록
- `required_context`: 스캔 설정과 실제 처리 수
- `evidence`: `scan_truncated=true`와 한계 안내
- `normal_exceptions`: 없음; 이것은 위험 후보가 아니라 범위 제한 신호
- `false_positive_risk`: LOW / `false_negative_risk`: LOW
- `explainability`: HIGH / `actionability`: 검사 범위 확인 또는 정밀 검토 / `repair_eligibility`: NONE
- `business_impact`: HIGH / `expected_frequency`: LOW / `implementation_cost`: LOW
- `recommended_tier`: Free scope boundary / `recommended_milestone`: M0–M2 유지 / `free_or_paid_candidate`: NOT_A_SEPARATE_PRODUCT_FINDING
- `current_status`: IMPLEMENTED / `quality_gate_status`: PASSED_SYNTHETIC / `exposure_status`: FREE_VISIBLE
- `priority_rationale`: 다른 모든 finding의 해석 안전성을 지키는 선행 신호다.
- `quality_gate_requirements`: `QG-S1`; 한계 전/후와 M4 전체 생략 사례를 재현하고, 범위 축소를 숨기지 않아야 한다.

## 2. 명시적 수식 오류

### `FORMULA_REF_ERROR`

- `rule_code`: `FORMULA_REF_ERROR`
- `rule_name`: 삭제·이동된 `#REF!` 참조
- `detection_layer`: formula token/text static inspection
- `user_problem`: 이미 깨진 참조 문자열을 놓친 채 파일을 사용하거나 전달함
- `detection_method`: 수식 텍스트의 `#REF!` 토큰 탐지
- `required_context`: 없음
- `evidence`: 오류 토큰과 위치; 계산 결과나 원문 수식 전체는 판단하지 않음
- `normal_exceptions`: 수식이 아닌 텍스트 문자열로 존재하는 경우는 스캔 대상에서 제외
- `false_positive_risk`: LOW / `false_negative_risk`: LOW
- `explainability`: HIGH / `actionability`: Excel 수식 표시줄에서 참조 복구 여부 확인 / `repair_eligibility`: EXPERT_ONLY
- `business_impact`: HIGH / `expected_frequency`: MEDIUM / `implementation_cost`: LOW
- `recommended_tier`: Free static signal / `recommended_milestone`: M0–M2 유지 / `free_or_paid_candidate`: FREE_STATIC_CANDIDATE
- `current_status`: IMPLEMENTED / `quality_gate_status`: PASSED_SYNTHETIC / `exposure_status`: FREE_VISIBLE
- `priority_rationale`: 명확한 구조 근거가 있으나 올바른 대체 참조는 업무 맥락 없이는 알 수 없다.
- `quality_gate_requirements`: `QG-S1`; target/error-token·정상 문자열·unsupported 문법 코퍼스와 Excel 확인법이 필요하다.

### `FORMULA_VISIBLE_ERROR_TOKEN`

- `rule_code`: `FORMULA_VISIBLE_ERROR_TOKEN`
- `rule_name`: 수식 안의 명시적 Excel 오류 토큰
- `detection_layer`: formula token/text static inspection
- `user_problem`: 오류 토큰이 있는 수식을 구조 검토 전에 놓침
- `detection_method`: 지원되는 Excel 오류 토큰 탐지
- `required_context`: 없음
- `evidence`: 오류 토큰과 위치만 표시
- `normal_exceptions`: 오류 텍스트가 수식이 아닌 데이터인 경우
- `false_positive_risk`: LOW / `false_negative_risk`: MEDIUM
- `explainability`: HIGH / `actionability`: 해당 수식과 선행 참조 확인 / `repair_eligibility`: EXPERT_ONLY
- `business_impact`: HIGH / `expected_frequency`: MEDIUM / `implementation_cost`: LOW
- `recommended_tier`: Free static signal / `recommended_milestone`: M0–M2 유지 / `free_or_paid_candidate`: FREE_STATIC_CANDIDATE
- `current_status`: IMPLEMENTED / `quality_gate_status`: PASSED_SYNTHETIC / `exposure_status`: FREE_VISIBLE
- `priority_rationale`: 명시적 오류는 이해는 쉽지만, silent error보다 구현 우선순위가 높다는 뜻은 아니다.
- `quality_gate_requirements`: `QG-S1`; 오류 토큰별 target과 정상 텍스트·지원하지 않는 배열/동적 문법을 분리한다.

### `DEFINED_NAME_BROKEN_REF`

- `rule_code`: `DEFINED_NAME_BROKEN_REF`
- `rule_name`: 깨진 정의 이름 참조
- `detection_layer`: workbook defined-name metadata
- `user_problem`: 수식, 이름 관리자, 차트 등의 간접 참조가 깨진 상태를 놓침
- `detection_method`: 정의 이름 목적지의 깨진 참조 토큰 탐지
- `required_context`: 없음
- `evidence`: 정의 이름의 깨진 참조 여부; 이름 내용과 셀 값은 노출하지 않음
- `normal_exceptions`: 숨은 내부 이름 또는 지원하지 않는 정의 이름 문법
- `false_positive_risk`: LOW / `false_negative_risk`: MEDIUM
- `explainability`: MEDIUM / `actionability`: Excel 이름 관리자에서 대상 확인 / `repair_eligibility`: EXPERT_ONLY
- `business_impact`: MEDIUM / `expected_frequency`: LOW / `implementation_cost`: LOW
- `recommended_tier`: Free static signal / `recommended_milestone`: M0–M2 유지 / `free_or_paid_candidate`: FREE_STATIC_CANDIDATE
- `current_status`: IMPLEMENTED / `quality_gate_status`: PASSED_SYNTHETIC / `exposure_status`: FREE_VISIBLE
- `priority_rationale`: 간접 참조의 손상을 보여 주지만 안전한 대체 대상은 자동 추정하지 않는다.
- `quality_gate_requirements`: `QG-S1`; 유효/깨진/지원하지 않는 정의 이름 코퍼스와 이름 관리자 확인법이 필요하다.

## 3. 수식 패턴 무결성

### `FORMULA_PATTERN_OUTLIER`

- `rule_code`: `FORMULA_PATTERN_OUTLIER`
- `rule_name`: 연속 수식 영역의 지배 패턴 이탈 후보
- `detection_layer`: normalized local formula pattern
- `user_problem`: 한 셀의 함수·참조 시트·상대/절대 참조·범위 패턴이 이웃과 달라져도 Excel 오류 없이 남는 위험
- `detection_method`: 같은 열의 연속 영역에서 최소 세 개의 지지 수식이 가진 지배 정규화 패턴과 한 수식을 비교
- `required_context`: 인접 수식 영역; 계산 결과·업무 규칙은 필요하지도 사용하지도 않음
- `evidence`: value-free subtype, 지배/현재 패턴 요약, 비교 위치, 정상 가능성. subtype은 rule code가 아님
- `normal_exceptions`: 소계·총계·헤더·수동 조정·Excel Table·병합 영역·구간 경계·미지원 문법
- `false_positive_risk`: MEDIUM / `false_negative_risk`: MEDIUM
- `explainability`: MEDIUM / `actionability`: Excel에서 주변 수식과 참조 차이 확인 / `repair_eligibility`: EXPERT_ONLY
- `business_impact`: HIGH / `expected_frequency`: MEDIUM / `implementation_cost`: HIGH
- `recommended_tier`: Internal precision-audit candidate / `recommended_milestone`: M4-B only after separate approval / `free_or_paid_candidate`: PAID_DEEP_VALIDATION_CANDIDATE
- `current_status`: PROTOTYPE / `quality_gate_status`: CONDITIONAL / `exposure_status`: INTERNAL_ONLY
- `priority_rationale`: 대표적인 silent formula error 후보지만, 현재 합성 품질 통과가 실제 업무 정답·일반 정확도를 뜻하지 않는다.
- `quality_gate_requirements`: `QG-P1`; 현재 target/normal/unsupported·안정성·값 없는 설명은 통과했고, 2배 성능 검토 기준 초과에 대한 인간 결정 전에는 비공개다.

### `FORMULA_PATTERN_GAP`

- `rule_code`: `FORMULA_PATTERN_GAP`
- `rule_name`: 수식 영역의 상수 덮어쓰기 또는 빈 셀 후보
- `detection_layer`: normalized local formula pattern
- `user_problem`: 반복 수식 중간에 값이나 공백이 들어가 계산이 조용히 달라질 수 있음
- `detection_method`: 같은 지배 패턴 수식 사이의 상수 또는 빈 셀을 보수적으로 탐지
- `required_context`: 양쪽 인접 수식과 충분한 지배 패턴 지지
- `evidence`: `CONSTANT_OVERRIDE_CANDIDATE` 또는 `BLANK_GAP_CANDIDATE`, 비교 위치와 한계. 이 subtype은 독립 규칙이 아님
- `normal_exceptions`: 수동 조정·소계·구분 행·의도된 공백·병합·Table·영역 경계
- `false_positive_risk`: MEDIUM / `false_negative_risk`: MEDIUM
- `explainability`: HIGH / `actionability`: Excel에서 값/빈 셀의 업무 의도와 이웃 수식 확인 / `repair_eligibility`: FUTURE_CANDIDATE
- `business_impact`: HIGH / `expected_frequency`: HIGH / `implementation_cost`: HIGH
- `recommended_tier`: Internal precision-audit candidate / `recommended_milestone`: M4-B only after separate approval / `free_or_paid_candidate`: PAID_DEEP_VALIDATION_CANDIDATE
- `current_status`: PROTOTYPE / `quality_gate_status`: CONDITIONAL / `exposure_status`: INTERNAL_ONLY
- `priority_rationale`: 사용자가 쉽게 확인할 수 있고 Repair로 이어질 여지가 크지만, 수동 입력 예외가 많아 보수적으로만 다뤄야 한다.
- `quality_gate_requirements`: `QG-P1`; 현 코퍼스는 통과했으나 성능 판단과 더 다양한 정상 수동 조정 사례가 남아 있다.

### `FORMULA_NEW_ROW_NOT_EXTENDED`

- `rule_code`: `FORMULA_NEW_ROW_NOT_EXTENDED`
- `rule_name`: 신규 행/기간에 수식이 연장되지 않은 후보
- `detection_layer`: row/column formula-region continuity
- `user_problem`: 데이터가 추가됐지만 계산 열의 수식이 마지막 행까지 내려오지 않음
- `detection_method`: 표준 수식 구간과 새 데이터 행의 경계·행 역할을 함께 비교
- `required_context`: 데이터 행과 수식 행을 구분할 수 있는 구조적 근거
- `evidence`: 예상 수식 구간, 새 행 근거, 제외한 요약/수동 행; 원문 값은 비노출
- `normal_exceptions`: 의도적으로 계산하지 않는 상태 행, 분기별 구간, 요약/소계, Excel Table 자동 확장
- `false_positive_risk`: MEDIUM / `false_negative_risk`: MEDIUM
- `explainability`: HIGH / `actionability`: 바로 위 수식과 해당 행의 업무 상태 확인 / `repair_eligibility`: FUTURE_CANDIDATE
- `business_impact`: HIGH / `expected_frequency`: HIGH / `implementation_cost`: HIGH
- `recommended_tier`: Precision-audit candidate / `recommended_milestone`: next M4 batch recommendation only / `free_or_paid_candidate`: PAID_DEEP_VALIDATION_CANDIDATE
- `current_status`: PLANNED / `quality_gate_status`: NOT_EVALUATED / `exposure_status`: WITHHELD
- `priority_rationale`: silent error 가능성과 확인 가능성이 높지만, 기존 gap 규칙의 subtype과 중복되지 않는 계약을 먼저 입증해야 한다.
- `quality_gate_requirements`: `QG-P1`; added-row target, 의도적 빈 행/수동 행/표 합계 normal, 미지원 구조를 포함하고 성능·설명 기준 미달 시 비공개다.

## 4. 참조·범위 무결성

### `FORMULA_RANGE_BOUNDARY_DRIFT`

- `rule_code`: `FORMULA_RANGE_BOUNDARY_DRIFT`
- `rule_name`: 수식 범위 시작·끝 경계 이탈 후보
- `detection_layer`: parsed A1 reference/range comparison
- `user_problem`: `SUM`, `SUMIFS`, 조회 등에서 한 행·열이 빠지거나 추가돼도 파일이 정상으로 보임
- `detection_method`: 유사 수식의 정규화 범위 끝점과 행 역할을 비교
- `required_context`: 지원되는 A1 범위, 인접 수식 패턴, 요약 행 여부
- `evidence`: `RANGE_BOUNDARY_DRIFT` subtype과 비교 위치; 현재 패턴 outlier의 subtype과 독립 rule로 중복 집계하지 않음
- `normal_exceptions`: 의도된 기간 분기, 헤더/소계 제외, 서로 다른 표 크기, 동적 범위
- `false_positive_risk`: HIGH / `false_negative_risk`: MEDIUM
- `explainability`: MEDIUM / `actionability`: Excel 수식의 시작·끝 참조와 포함 행 확인 / `repair_eligibility`: EXPERT_ONLY
- `business_impact`: HIGH / `expected_frequency`: MEDIUM / `implementation_cost`: HIGH
- `recommended_tier`: Precision-audit candidate / `recommended_milestone`: next M4 batch recommendation only / `free_or_paid_candidate`: PAID_DEEP_VALIDATION_CANDIDATE
- `current_status`: PLANNED / `quality_gate_status`: NOT_EVALUATED / `exposure_status`: WITHHELD
- `priority_rationale`: 영향은 크지만 정상 예외가 많아 aggregate 의미를 다루기 전 공개하면 오탐 위험이 높다.
- `quality_gate_requirements`: `QG-P1`; 한 행 누락/초과 target, 의도된 구간 차이 normal, dynamic/structured/3D reference unsupported를 포함한다.

### `FORMULA_NAMED_RANGE_TARGET_DRIFT`

- `rule_code`: `FORMULA_NAMED_RANGE_TARGET_DRIFT`
- `rule_name`: 이름 범위의 대상 이탈 또는 의도치 않은 확장 후보
- `detection_layer`: defined-name to reference graph
- `user_problem`: 이름을 사용하는 수식은 정상처럼 보이나 이름 대상 범위가 바뀜
- `detection_method`: 정의 이름 대상과 사용 위치의 구조적 관계 비교
- `required_context`: 지원되는 정의 이름 문법과 이름 사용 그래프
- `evidence`: 이름 대상의 구조 변화 유형과 Excel 이름 관리자 확인법
- `normal_exceptions`: 의도적 동적 이름 범위, 지역 이름, 지원하지 않는 이름 수식
- `false_positive_risk`: HIGH / `false_negative_risk`: MEDIUM
- `explainability`: MEDIUM / `actionability`: 이름 관리자와 사용 수식 검토 / `repair_eligibility`: EXPERT_ONLY
- `business_impact`: MEDIUM / `expected_frequency`: LOW / `implementation_cost`: HIGH
- `recommended_tier`: Expert precision validation / `recommended_milestone`: later M4/M6 research / `free_or_paid_candidate`: EXPERT_SERVICE_CANDIDATE
- `current_status`: PLANNED / `quality_gate_status`: NOT_EVALUATED / `exposure_status`: WITHHELD
- `priority_rationale`: 간접 참조의 영향은 크지만 동적 이름의 정상 예외를 정적으로 설명하기 어렵다.
- `quality_gate_requirements`: `QG-P1`; static/dynamic/local-name target·normal·unsupported와 이름 관리자 확인 안내가 필요하다.

## 5. 집계·소계·총계 위험

### `AGGREGATE_CRITERIA_RANGE_MISMATCH`

- `rule_code`: `AGGREGATE_CRITERIA_RANGE_MISMATCH`
- `rule_name`: 조건 범위와 집계 범위의 길이·시작점 불일치 후보
- `detection_layer`: aggregate formula argument structure
- `user_problem`: `SUMIFS`/`COUNTIFS`류 수식이 예상과 다른 행을 계산할 수 있음
- `detection_method`: 지원 함수의 조건·합계 범위 인수 길이와 시작점을 정적으로 비교
- `required_context`: 지원 함수 목록과 A1 범위 해석
- `evidence`: 불일치한 인수 역할과 범위 관계; 계산 결과나 올바른 범위는 단정하지 않음
- `normal_exceptions`: 의도된 offset, 서로 다른 표의 대응 범위, 동적/이름/구조화 참조
- `false_positive_risk`: MEDIUM / `false_negative_risk`: MEDIUM
- `explainability`: HIGH / `actionability`: Excel 함수 인수의 각 범위를 나란히 확인 / `repair_eligibility`: EXPERT_ONLY
- `business_impact`: HIGH / `expected_frequency`: MEDIUM / `implementation_cost`: MEDIUM
- `recommended_tier`: Precision-audit candidate / `recommended_milestone`: next M4 batch recommendation only / `free_or_paid_candidate`: PAID_DEEP_VALIDATION_CANDIDATE
- `current_status`: PLANNED / `quality_gate_status`: NOT_EVALUATED / `exposure_status`: WITHHELD
- `priority_rationale`: 영향과 근거 설명이 비교적 명확해 next batch 우선 후보지만 함수·참조 문법의 경계를 먼저 정해야 한다.
- `quality_gate_requirements`: `QG-P1`; offset mismatch target, 의도된 offset normal, 동적/외부/structured reference unsupported를 포함한다.

### `SUBTOTAL_TOTAL_DOUBLE_COUNT_RISK`

- `rule_code`: `SUBTOTAL_TOTAL_DOUBLE_COUNT_RISK`
- `rule_name`: 소계·총계의 중복 합산 가능성
- `detection_layer`: row role plus aggregate reference structure
- `user_problem`: 총계가 소계와 상세 행을 함께 포함해 값을 이중으로 더할 수 있음
- `detection_method`: 소계/총계로 보이는 행과 참조 범위의 포함 관계를 보수적으로 후보화
- `required_context`: 행 제목·수식 패턴·구간 경계; 업무 의미를 자동 추정하지 않음
- `evidence`: 중복 포함 가능성이 있는 구조와 제외한 정상 조건
- `normal_exceptions`: 소계가 표시용이거나 총계 계산에서 의도적으로 제외되는 경우, 다단계 보고서
- `false_positive_risk`: HIGH / `false_negative_risk`: HIGH
- `explainability`: MEDIUM / `actionability`: 총계 수식에서 소계와 상세 행 포함 여부 확인 / `repair_eligibility`: EXPERT_ONLY
- `business_impact`: HIGH / `expected_frequency`: MEDIUM / `implementation_cost`: HIGH
- `recommended_tier`: Expert precision validation / `recommended_milestone`: next M4 batch research recommendation only / `free_or_paid_candidate`: EXPERT_SERVICE_CANDIDATE
- `current_status`: PLANNED / `quality_gate_status`: NOT_EVALUATED / `exposure_status`: WITHHELD
- `priority_rationale`: 고객 가치는 높지만 행 역할의 정상 예외가 많아 false positive를 감수하고 무료 공개할 수 없다.
- `quality_gate_requirements`: `QG-P1`; 다단 소계·표시용 소계·조정 행 normal을 우선 확보하고, 명시 예외 false positive 0이 아니면 비공개다.

### `AGGREGATE_RANGE_EXCLUDES_NEW_ROWS`

- `rule_code`: `AGGREGATE_RANGE_EXCLUDES_NEW_ROWS`
- `rule_name`: 집계 범위가 신규 데이터 행을 포함하지 않는 후보
- `detection_layer`: aggregate boundary versus data-region continuity
- `user_problem`: 새 데이터는 입력됐지만 합계/조회 범위 끝점이 늘지 않음
- `detection_method`: 인접 데이터 구간과 집계 범위의 끝점을 비교
- `required_context`: 데이터 행 식별, 합계 행, 표/필터 구조
- `evidence`: 추가 데이터 구간과 집계 범위의 경계 관계
- `normal_exceptions`: 의도적 제외, 보류 행, 다른 기간/사업부 구간, Table 자동 확장
- `false_positive_risk`: HIGH / `false_negative_risk`: MEDIUM
- `explainability`: HIGH / `actionability`: 합계 범위와 마지막 데이터 행 확인 / `repair_eligibility`: FUTURE_CANDIDATE
- `business_impact`: HIGH / `expected_frequency`: MEDIUM / `implementation_cost`: HIGH
- `recommended_tier`: Precision-audit candidate / `recommended_milestone`: later M4 batch / `free_or_paid_candidate`: PAID_DEEP_VALIDATION_CANDIDATE
- `current_status`: PLANNED / `quality_gate_status`: NOT_EVALUATED / `exposure_status`: WITHHELD
- `priority_rationale`: `FORMULA_NEW_ROW_NOT_EXTENDED`와 함께 가치가 크나 데이터 행 경계를 오판하지 않는 것이 핵심이다.
- `quality_gate_requirements`: `QG-P1`; 확장/미확장 target, 의도적 제외/기간 구분 normal, Table/동적 범위 unsupported가 필요하다.

## 6. 데이터 형식·품질

### `NUMBER_STORED_AS_TEXT`

- `rule_code`: `NUMBER_STORED_AS_TEXT`
- `rule_name`: 숫자 열 안의 숫자형 텍스트 후보
- `detection_layer`: column type profile
- `user_problem`: 집계·조건 비교에서 숫자가 누락될 수 있음
- `detection_method`: 같은 열의 숫자 비율과 문자열 숫자 패턴을 보수적으로 비교
- `required_context`: 최소 표본 수와 숫자 우세 열
- `evidence`: 위치와 열의 형식 불일치 근거; 실제 계산 결과는 검증하지 않음
- `normal_exceptions`: 선행 0이 필요한 코드, 식별자, 공백 포함 문자열
- `false_positive_risk`: MEDIUM / `false_negative_risk`: MEDIUM
- `explainability`: HIGH / `actionability`: Excel 셀 서식·선행 0 보존 필요성 확인 / `repair_eligibility`: FUTURE_CANDIDATE
- `business_impact`: MEDIUM / `expected_frequency`: HIGH / `implementation_cost`: MEDIUM
- `recommended_tier`: Free static signal / `recommended_milestone`: M0–M2 유지 / `free_or_paid_candidate`: FREE_STATIC_CANDIDATE
- `current_status`: IMPLEMENTED / `quality_gate_status`: PASSED_SYNTHETIC / `exposure_status`: FREE_VISIBLE
- `priority_rationale`: 발생 가능성이 높고 확인은 쉽지만 식별자 예외 때문에 자동 변환하면 안 된다.
- `quality_gate_requirements`: `QG-S1`; 숫자 열 target, 코드/선행 0 normal, 혼합 열 unsupported와 사용자 확인 안내가 필요하다.

### `INCONSISTENT_DATE_OR_TYPE_PATTERN`

- `rule_code`: `INCONSISTENT_DATE_OR_TYPE_PATTERN`
- `rule_name`: 날짜·숫자·텍스트 형식 혼재 후보
- `detection_layer`: column type and number-format profile
- `user_problem`: 정렬·필터·기간 계산 결과가 기대와 다를 수 있음
- `detection_method`: 열별 값 타입·표시 형식·파싱 가능한 날짜 패턴 비교
- `required_context`: 열의 의미가 아닌 구조적 형식 패턴만 사용
- `evidence`: 혼재 비율과 형식 차이; 날짜의 업무 의미는 단정하지 않음
- `normal_exceptions`: 월 제목, 공란, 코드, locale별 날짜 표현, 의도적 혼합 열
- `false_positive_risk`: HIGH / `false_negative_risk`: MEDIUM
- `explainability`: HIGH / `actionability`: Excel 형식·정렬·필터 동작 확인 / `repair_eligibility`: FUTURE_CANDIDATE
- `business_impact`: MEDIUM / `expected_frequency`: MEDIUM / `implementation_cost`: MEDIUM
- `recommended_tier`: Free/precision candidate after gate / `recommended_milestone`: later M4 / `free_or_paid_candidate`: FREE_STATIC_CANDIDATE
- `current_status`: PLANNED / `quality_gate_status`: NOT_EVALUATED / `exposure_status`: WITHHELD
- `priority_rationale`: 이해는 쉽지만 열 의미를 모르면 정상 혼합을 오탐할 위험이 높다.
- `quality_gate_requirements`: `QG-S1`; locale/코드/헤더 normal과 실제 혼재 target을 분리하고, 의미 추론이 필요한 경우 비공개다.

## 7. 외부 연결·의존성

### `FORMULA_EXTERNAL_REFERENCE`

- `rule_code`: `FORMULA_EXTERNAL_REFERENCE`
- `rule_name`: 외부 통합문서 참조
- `detection_layer`: formula reference token plus workbook relationship metadata
- `user_problem`: 원본 파일이 없거나 갱신되지 않아 오래된 값이 남을 가능성
- `detection_method`: 외부 파일 참조 형식과 external-link 관계 파트 탐지
- `required_context`: 없음; 외부 파일 접근성은 검사하지 않음
- `evidence`: 외부 참조 존재와 위치; 외부 파일명·내용을 서버 로그에 남기지 않음
- `normal_exceptions`: 의도된 월간 통합·보고용 연결
- `false_positive_risk`: LOW / `false_negative_risk`: MEDIUM
- `explainability`: HIGH / `actionability`: Excel 데이터/연결 및 수식의 외부 참조 확인 / `repair_eligibility`: EXPERT_ONLY
- `business_impact`: HIGH / `expected_frequency`: MEDIUM / `implementation_cost`: LOW
- `recommended_tier`: Free static signal / `recommended_milestone`: M0–M2 유지 / `free_or_paid_candidate`: FREE_STATIC_CANDIDATE
- `current_status`: IMPLEMENTED / `quality_gate_status`: PASSED_SYNTHETIC / `exposure_status`: FREE_VISIBLE
- `priority_rationale`: 실제 최신성은 모르지만 외부 의존성 자체는 명확한 행동 근거다.
- `quality_gate_requirements`: `QG-S1`; 내부/외부 참조 target·normal과 미지원 외부 문법을 구분하며 외부 연결을 실행하지 않는다.

### `EXTERNAL_CONNECTION_DEPENDENCY`

- `rule_code`: `EXTERNAL_CONNECTION_DEPENDENCY`
- `rule_name`: 쿼리·연결·외부 데이터 의존성 인벤토리
- `detection_layer`: OOXML relationship and connection metadata
- `user_problem`: 수식 외 연결이 파일 결과에 영향을 줄 수 있음을 모름
- `detection_method`: connection/query 관련 파트를 정적으로 목록화
- `required_context`: 지원되는 OOXML 연결 파트 정의
- `evidence`: 연결 유형·존재 여부만; 연결 문자열·자격 증명·원격 접근은 비노출·미실행
- `normal_exceptions`: 승인된 데이터 연결, Power Query, 사내 데이터 원본
- `false_positive_risk`: LOW / `false_negative_risk`: MEDIUM
- `explainability`: MEDIUM / `actionability`: Excel의 연결/쿼리 메뉴에서 갱신 정책 확인 / `repair_eligibility`: EXPERT_ONLY
- `business_impact`: HIGH / `expected_frequency`: MEDIUM / `implementation_cost`: MEDIUM
- `recommended_tier`: Expert safety audit / `recommended_milestone`: later M4/M6 research / `free_or_paid_candidate`: EXPERT_SERVICE_CANDIDATE
- `current_status`: PLANNED / `quality_gate_status`: NOT_EVALUATED / `exposure_status`: WITHHELD
- `priority_rationale`: 신뢰·보안 가치는 높지만 복잡한 연결 문법과 민감 정보 처리 정책이 선행돼야 한다.
- `quality_gate_requirements`: `QG-S1`; 합성 connection metadata만 사용하고, 비밀값 비노출·무실행을 확인하지 못하면 공개하지 않는다.

## 8. 계산·순환참조

### `FORMULA_CIRCULAR_REFERENCE`

- `rule_code`: `FORMULA_CIRCULAR_REFERENCE`
- `rule_name`: 순환참조 후보
- `detection_layer`: dependency graph with calculation configuration
- `user_problem`: 반복 계산 또는 순환참조로 결과가 예상과 다르게 유지될 수 있음
- `detection_method`: 수식 참조 그래프와 반복 계산 설정을 함께 해석
- `required_context`: 완전한 지원 문법, 이름/외부/동적 참조 처리, 계산 설정
- `evidence`: 순환 경로와 반복 계산 한계; 계산 결과는 주장하지 않음
- `normal_exceptions`: 의도된 반복 계산, 재무 목표값 찾기 모델, 미지원 동적/외부 참조
- `false_positive_risk`: MEDIUM / `false_negative_risk`: HIGH
- `explainability`: MEDIUM / `actionability`: Excel 반복 계산 설정과 참조 경로 확인 / `repair_eligibility`: EXPERT_ONLY
- `business_impact`: HIGH / `expected_frequency`: LOW / `implementation_cost`: HIGH
- `recommended_tier`: Expert deep validation / `recommended_milestone`: M6 research / `free_or_paid_candidate`: EXPERT_SERVICE_CANDIDATE
- `current_status`: REQUIRES_CALCULATION_ENGINE / `quality_gate_status`: NOT_EVALUATED / `exposure_status`: WITHHELD
- `priority_rationale`: 그래프만으로 후보를 낼 수 있어도 실제 계산 의미와 허용 반복을 구분하기 어렵다.
- `quality_gate_requirements`: `QG-C1`; 격리 계산 엔진·의도된 반복 normal·Excel 기준 비교가 없으면 구현/공개하지 않는다.

### `CALCULATED_VALUE_ERROR_OR_STALE_CACHE`

- `rule_code`: `CALCULATED_VALUE_ERROR_OR_STALE_CACHE`
- `rule_name`: 계산 결과 오류 또는 오래된 캐시 값 검증
- `detection_layer`: isolated calculation runtime and cached-value comparison
- `user_problem`: 수식 구조는 정상이어도 Excel 계산 결과가 최신이 아니거나 오류일 수 있음
- `detection_method`: 승인된 엔진에서 재계산 후 기준 결과와 캐시/구조를 비교
- `required_context`: Excel 호환 계산 엔진, 버전 정책, 재계산 설정, 격리 환경
- `evidence`: 재계산 여부·비교 결과·지원 범위. 임의의 업무 정답은 단정하지 않음
- `normal_exceptions`: 수동 계산 모드, 지원하지 않는 함수/매크로/외부 연결, 의도적 캐시
- `false_positive_risk`: HIGH / `false_negative_risk`: HIGH
- `explainability`: MEDIUM / `actionability`: Excel 계산 옵션·지원 함수·원본 데이터 확인 / `repair_eligibility`: EXPERT_ONLY
- `business_impact`: HIGH / `expected_frequency`: MEDIUM / `implementation_cost`: HIGH
- `recommended_tier`: Paid deep validation / `recommended_milestone`: M6 research / `free_or_paid_candidate`: PAID_DEEP_VALIDATION_CANDIDATE
- `current_status`: REQUIRES_CALCULATION_ENGINE / `quality_gate_status`: NOT_EVALUATED / `exposure_status`: WITHHELD
- `priority_rationale`: 결제 가치는 높지만 현재 정적 검사와 기술·보안·법적 책임 경계가 완전히 다르다.
- `quality_gate_requirements`: `QG-C1`; 네트워크 차단, disposable storage, Excel 비교 코퍼스, 성능·메모리 예산을 별도 승인해야 한다.

## 9. 파일 버전 변경

### `VERSION_FORMULA_CHANGE`

- `rule_code`: `VERSION_FORMULA_CHANGE`
- `rule_name`: 이전 파일 대비 수식 구조 변경
- `detection_layer`: paired workbook structural diff
- `user_problem`: 전월·이전 버전에서 어떤 수식이 바뀌었는지 놓침
- `detection_method`: 선택된 두 파일의 sheet/region/formula signature를 안전하게 비교
- `required_context`: 이전 파일 확보, 같은 계열 파일 판정, 비교 기준, 업로드 보관·삭제 정책
- `evidence`: 변경 유형과 비교 기준; 원문 수식·파일명을 평가 로그에 기록하지 않음
- `normal_exceptions`: 의도된 월 이월, 템플릿 업데이트, 시트 이름/행 이동, 지원하지 않는 문법
- `false_positive_risk`: HIGH / `false_negative_risk`: MEDIUM
- `explainability`: HIGH / `actionability`: 변경 목적·변경 내역과 해당 Excel 위치 확인 / `repair_eligibility`: EXPERT_ONLY
- `business_impact`: HIGH / `expected_frequency`: MEDIUM / `implementation_cost`: HIGH
- `recommended_tier`: Paid deep validation / `recommended_milestone`: M6 after privacy approval / `free_or_paid_candidate`: PAID_DEEP_VALIDATION_CANDIDATE
- `current_status`: REQUIRES_VERSION_COMPARISON / `quality_gate_status`: NOT_EVALUATED / `exposure_status`: WITHHELD
- `priority_rationale`: 실제 업무 가치는 크지만 현재 서비스는 업로드를 보관하지 않으므로 파일 쌍·보관 정책을 먼저 승인해야 한다.
- `quality_gate_requirements`: `QG-V1`; paired synthetic versions, identity/rename rules, retention/deletion policy, 값 없는 diff 출력을 갖추기 전에는 노출하지 않는다.

### `VERSION_EXTERNAL_DEPENDENCY_CHANGE`

- `rule_code`: `VERSION_EXTERNAL_DEPENDENCY_CHANGE`
- `rule_name`: 이전 파일 대비 외부 연결·정의 이름·매크로 경계 변화
- `detection_layer`: paired workbook metadata diff
- `user_problem`: 수식 외 의존성이 바뀌어도 변경 사항을 놓침
- `detection_method`: 두 파일의 OOXML metadata와 안전 경계 신호를 비교
- `required_context`: `VERSION_FORMULA_CHANGE`와 같은 파일 쌍·보관·비교 정책
- `evidence`: 추가/제거된 의존성 유형; 비밀 연결 문자열은 비노출
- `normal_exceptions`: 의도된 배포 설정 변경, 정상 템플릿 갱신
- `false_positive_risk`: MEDIUM / `false_negative_risk`: MEDIUM
- `explainability`: HIGH / `actionability`: 변경 승인 기록과 Excel 연결/이름 관리자 확인 / `repair_eligibility`: EXPERT_ONLY
- `business_impact`: HIGH / `expected_frequency`: LOW / `implementation_cost`: HIGH
- `recommended_tier`: Paid deep validation / `recommended_milestone`: M6 after privacy approval / `free_or_paid_candidate`: PAID_DEEP_VALIDATION_CANDIDATE
- `current_status`: REQUIRES_VERSION_COMPARISON / `quality_gate_status`: NOT_EVALUATED / `exposure_status`: WITHHELD
- `priority_rationale`: 보안·보존 가치는 높지만 보관 정책 없는 현 단계에서는 다룰 수 없다.
- `quality_gate_requirements`: `QG-V1`; safe metadata diff와 비밀값 비노출, 짝지은 normal 변경 사례가 필요하다.

## 10. 업무 정합성

### `DECLARED_BUSINESS_RULE_ASSERTION`

- `rule_code`: `DECLARED_BUSINESS_RULE_ASSERTION`
- `rule_name`: 사용자가 선언한 업무 규칙 위반
- `detection_layer`: declared business-rule evaluator
- `user_problem`: 예를 들어 재고 음수 금지·승인 금액 상한 같은 명시 규칙을 확인하지 못함
- `detection_method`: 사용자가 검토·승인한 범위·조건·예외를 결정적으로 평가
- `required_context`: 업무 규칙 명세, 대상 범위, 예외, 규칙 소유자
- `evidence`: 어떤 선언 규칙의 어떤 조건이 충족되지 않았는지; 규칙 밖의 업무 의도는 추정하지 않음
- `normal_exceptions`: 명시적으로 문서화된 예외만 허용
- `false_positive_risk`: MEDIUM / `false_negative_risk`: MEDIUM
- `explainability`: HIGH / `actionability`: 규칙 소유자와 해당 데이터/조건 확인 / `repair_eligibility`: EXPERT_ONLY
- `business_impact`: HIGH / `expected_frequency`: MEDIUM / `implementation_cost`: HIGH
- `recommended_tier`: Expert/premium validation / `recommended_milestone`: M5 / `free_or_paid_candidate`: PAID_DEEP_VALIDATION_CANDIDATE
- `current_status`: REQUIRES_BUSINESS_CONTEXT / `quality_gate_status`: NOT_EVALUATED / `exposure_status`: WITHHELD
- `priority_rationale`: 고객 가치는 높지만 WorkbookCare가 파일 내용만 보고 업무 규칙을 발명해서는 안 된다.
- `quality_gate_requirements`: `QG-B1`; 규칙 소유자 승인, 정상·예외·위반 합성 사례, 책임·수정 경계를 갖춰야 한다.

### `DECLARED_CROSS_SHEET_RECONCILIATION`

- `rule_code`: `DECLARED_CROSS_SHEET_RECONCILIATION`
- `rule_name`: 사용자가 선언한 시트 간 대사 규칙 불일치
- `detection_layer`: declared cross-sheet relation evaluator
- `user_problem`: 보고서·원장·요약 간 일치해야 할 값/행을 확인하지 못함
- `detection_method`: 사용자가 제공한 키·매핑·허용 오차·갱신 기준을 평가
- `required_context`: 대사 정의, 키, 기간, 허용 오차, 데이터 소유자
- `evidence`: 선언된 관계와 불일치 상태; 업무적 원인은 추정하지 않음
- `normal_exceptions`: 사용자가 지정한 시차·조정·미확정 상태
- `false_positive_risk`: MEDIUM / `false_negative_risk`: MEDIUM
- `explainability`: HIGH / `actionability`: 해당 대사 정의와 원본 데이터 확인 / `repair_eligibility`: EXPERT_ONLY
- `business_impact`: HIGH / `expected_frequency`: MEDIUM / `implementation_cost`: HIGH
- `recommended_tier`: Expert/premium validation / `recommended_milestone`: M5 / `free_or_paid_candidate`: PAID_DEEP_VALIDATION_CANDIDATE
- `current_status`: REQUIRES_BUSINESS_CONTEXT / `quality_gate_status`: NOT_EVALUATED / `exposure_status`: WITHHELD
- `priority_rationale`: 단순 구조 차이보다 강한 유료 가치를 만들 수 있지만 고객 규칙이 계약되어야 한다.
- `quality_gate_requirements`: `QG-B1`; 대사 규칙별 합성 정답·정상 시차·예외·역할 검토가 필요하다.

## 11. 재무 모델

### `FINANCIAL_BALANCE_AND_ROLL_FORWARD_ASSERTION`

- `rule_code`: `FINANCIAL_BALANCE_AND_ROLL_FORWARD_ASSERTION`
- `rule_name`: 재무 잔액·롤포워드·차대 불일치 검증
- `detection_layer`: financial domain model and declared accounting rules
- `user_problem`: 재무 모델의 기간 연결·합계·균형이 깨져도 구조상 보이지 않을 수 있음
- `detection_method`: 승인된 계정 구조·기간·부호·검증식을 기준으로 평가
- `required_context`: 재무 모델 정의, 회계 기간, 차트오브어카운트, 전문 검토자
- `evidence`: 선언 검증식과 불일치의 범위; 회계 판단이나 감사 의견은 제공하지 않음
- `normal_exceptions`: 조정 분개, 연결 제거, 보고 기준 차이, 미확정 기간
- `false_positive_risk`: HIGH / `false_negative_risk`: HIGH
- `explainability`: MEDIUM / `actionability`: 재무 모델 소유자·회계 전문가 검토 / `repair_eligibility`: EXPERT_ONLY
- `business_impact`: HIGH / `expected_frequency`: MEDIUM / `implementation_cost`: HIGH
- `recommended_tier`: Expert financial validation / `recommended_milestone`: post-M5 domain program / `free_or_paid_candidate`: EXPERT_SERVICE_CANDIDATE
- `current_status`: REQUIRES_DOMAIN_EXPERTISE / `quality_gate_status`: NOT_EVALUATED / `exposure_status`: WITHHELD
- `priority_rationale`: 영향은 매우 크지만 일반 규칙으로 공개하면 회계·감사 범위를 과장할 위험이 있다.
- `quality_gate_requirements`: `QG-B1`; 도메인 전문가, 모델별 규칙 계약, 합성 재무 사례, 법적/책임 경계가 필요하다.

## 12. 통계·회귀 모델

### `STATISTICAL_MODEL_RANGE_ALIGNMENT`

- `rule_code`: `STATISTICAL_MODEL_RANGE_ALIGNMENT`
- `rule_name`: 통계 모델 입력·레이블·출력 범위 정렬 검증
- `detection_layer`: statistical model structure plus calculation semantics
- `user_problem`: 데이터/레이블 길이 또는 범위 차이로 분석 결과가 신뢰하기 어려울 수 있음
- `detection_method`: 사용자 선언 모델과 지원 함수의 입력·출력 범위 관계를 평가
- `required_context`: 모델 종류, 표본 정의, 결측값 정책, 통계 해석 기준
- `evidence`: 범위 정렬 상태와 미검증 통계 가정
- `normal_exceptions`: 가중치, 결측 처리, 패널 데이터, 의도된 분할 표본
- `false_positive_risk`: HIGH / `false_negative_risk`: HIGH
- `explainability`: MEDIUM / `actionability`: 모델 작성자·통계 검토자와 입력 범위 확인 / `repair_eligibility`: EXPERT_ONLY
- `business_impact`: HIGH / `expected_frequency`: LOW / `implementation_cost`: HIGH
- `recommended_tier`: Expert statistical validation / `recommended_milestone`: post-M5/M6 domain program / `free_or_paid_candidate`: EXPERT_SERVICE_CANDIDATE
- `current_status`: REQUIRES_DOMAIN_EXPERTISE / `quality_gate_status`: NOT_EVALUATED / `exposure_status`: WITHHELD
- `priority_rationale`: 구조적 체크만으로 통계적 타당성을 주장할 수 없기 때문에 별도 도메인 제품이다.
- `quality_gate_requirements`: `QG-B1` and `QG-C1`; 통계 전문가, 계산 기준, 가정·예외가 정해지기 전에는 공개하지 않는다.

## 13. 성능·유지보수

### `FORMULA_VOLATILE`

- `rule_code`: `FORMULA_VOLATILE`
- `rule_name`: 휘발성 함수 사용
- `detection_layer`: formula token static inspection
- `user_problem`: 재계산 지연과 유지보수 부담의 원인이 될 수 있음
- `detection_method`: 지원되는 휘발성 함수 이름 탐지
- `required_context`: 없음
- `evidence`: 함수 유형과 위치; 실제 성능 저하는 측정하지 않음
- `normal_exceptions`: 의도된 현재 시각/난수/간접 참조 사용
- `false_positive_risk`: LOW / `false_negative_risk`: MEDIUM
- `explainability`: HIGH / `actionability`: 함수 필요성과 계산 옵션 확인 / `repair_eligibility`: EXPERT_ONLY
- `business_impact`: MEDIUM / `expected_frequency`: MEDIUM / `implementation_cost`: LOW
- `recommended_tier`: Free maintainability signal / `recommended_milestone`: M0–M2 유지 / `free_or_paid_candidate`: FREE_STATIC_CANDIDATE
- `current_status`: IMPLEMENTED / `quality_gate_status`: PASSED_SYNTHETIC / `exposure_status`: FREE_VISIBLE
- `priority_rationale`: 성능 위험의 근거는 명확하지만 대체 함수는 업무 의도에 따라 달라진다.
- `quality_gate_requirements`: `QG-S1`; 함수별 target·의도적 사용 normal·지원하지 않는 문법을 분리한다.

### `FORMULA_WHOLE_COLUMN_REFERENCE`

- `rule_code`: `FORMULA_WHOLE_COLUMN_REFERENCE`
- `rule_name`: 전체 열 참조 수식
- `detection_layer`: formula reference token static inspection
- `user_problem`: 큰 파일에서 계산량이 불필요하게 증가할 수 있음
- `detection_method`: 전체 열 A1 참조 패턴 탐지
- `required_context`: 없음
- `evidence`: 전체 열 참조 존재와 위치; 실제 성능 영향은 계산하지 않음
- `normal_exceptions`: 작은 파일, Table/동적 범위 대체가 부적절한 경우
- `false_positive_risk`: LOW / `false_negative_risk`: MEDIUM
- `explainability`: HIGH / `actionability`: 참조 범위 축소가 업무 의도와 맞는지 확인 / `repair_eligibility`: FUTURE_CANDIDATE
- `business_impact`: MEDIUM / `expected_frequency`: MEDIUM / `implementation_cost`: LOW
- `recommended_tier`: Free maintainability signal / `recommended_milestone`: M0–M2 유지 / `free_or_paid_candidate`: FREE_STATIC_CANDIDATE
- `current_status`: IMPLEMENTED / `quality_gate_status`: PASSED_SYNTHETIC / `exposure_status`: FREE_VISIBLE
- `priority_rationale`: 근거는 명확하지만 무조건 고쳐야 한다는 신호가 아니라 유지보수 정보다.
- `quality_gate_requirements`: `QG-S1`; 전체/부분 열·문자열·지원하지 않는 참조 사례를 분리하고 성능 단정 문구를 금지한다.

### `FORMULA_DEEP_NESTING`

- `rule_code`: `FORMULA_DEEP_NESTING`
- `rule_name`: 깊은 중첩 IF 수식
- `detection_layer`: formula token/static complexity heuristic
- `user_problem`: 수정·검토가 어려운 복잡한 수식이 업무 변경에서 위험해질 수 있음
- `detection_method`: 보수적 중첩 IF 개수 임계값
- `required_context`: 없음
- `evidence`: 중첩 정도와 유지보수 한계; 업무 정답 여부는 판단하지 않음
- `normal_exceptions`: 정당한 복잡한 의사결정 로직, 대체 함수 비지원 환경
- `false_positive_risk`: MEDIUM / `false_negative_risk`: MEDIUM
- `explainability`: HIGH / `actionability`: 수식 검토·분리·전문가 검증 고려 / `repair_eligibility`: EXPERT_ONLY
- `business_impact`: MEDIUM / `expected_frequency`: MEDIUM / `implementation_cost`: LOW
- `recommended_tier`: Free maintainability signal / `recommended_milestone`: M0–M2 유지 / `free_or_paid_candidate`: FREE_STATIC_CANDIDATE
- `current_status`: IMPLEMENTED / `quality_gate_status`: PASSED_SYNTHETIC / `exposure_status`: FREE_VISIBLE
- `priority_rationale`: 사용자 설명은 쉽지만 복잡성은 오류 증거가 아니므로 정보성으로 유지한다.
- `quality_gate_requirements`: `QG-S1`; 임계값 경계·정상 복잡 수식·지원하지 않는 문법에 대한 설명과 비단정 문구가 필요하다.

### `FORMULA_COUNT_HIGH` / `MERGED_CELL_HEAVY`

- `rule_code`: `FORMULA_COUNT_HIGH`, `MERGED_CELL_HEAVY`
- `rule_name`: 많은 수식 또는 과도한 병합 영역에 따른 유지보수 신호
- `detection_layer`: workbook structural count heuristic
- `user_problem`: 파일 성능·필터·복사·자동화 작업의 복잡도가 커질 수 있음
- `detection_method`: 수식 수와 병합 범위 수의 보수적 임계값 비교
- `required_context`: 없음
- `evidence`: 개수 및 임계값 도달 여부; 실제 지연이나 손상을 측정하지 않음
- `normal_exceptions`: 대형 보고서, 인쇄용 서식, 의도된 모델 구조
- `false_positive_risk`: MEDIUM / `false_negative_risk`: MEDIUM
- `explainability`: HIGH / `actionability`: 성능·정렬·자동화 설계 검토 / `repair_eligibility`: EXPERT_ONLY
- `business_impact`: MEDIUM / `expected_frequency`: MEDIUM / `implementation_cost`: LOW
- `recommended_tier`: Free maintainability signal / `recommended_milestone`: M0–M2 유지 / `free_or_paid_candidate`: FREE_STATIC_CANDIDATE
- `current_status`: IMPLEMENTED / `quality_gate_status`: PASSED_SYNTHETIC / `exposure_status`: FREE_VISIBLE
- `priority_rationale`: 제품의 한계와 향후 자동화 상담의 맥락을 제공하지만 오류·수정 대상처럼 표시하지 않는다.
- `quality_gate_requirements`: `QG-S1`; 임계값 전후·정상 대형 파일의 코퍼스와 정보성 표현이 필요하다.

## 14. 자동화 기회

### `REPEATED_MANUAL_TRANSFORMATION_CANDIDATE`

- `rule_code`: `REPEATED_MANUAL_TRANSFORMATION_CANDIDATE`
- `rule_name`: 반복 데이터 정리·변환 흐름의 자동화 후보
- `detection_layer`: user-declared workflow context
- `user_problem`: 같은 복사·정리·형식 변경을 반복하며 시간과 오류 위험이 누적됨
- `detection_method`: 사용자 동의가 있는 업무 단계·빈도·입력/출력의 명시적 인터뷰 또는 향후 안전한 이벤트 기록을 분석
- `required_context`: 반복 주기, 담당자, 입력·출력, 예외, 보안·보관 동의
- `evidence`: 선언된 반복 단계와 확인된 수작업만 표시; 파일 구조만으로 업무를 추측하지 않음
- `normal_exceptions`: 일회성 보고서, 규정상 수동 승인, 예외가 많은 작업
- `false_positive_risk`: HIGH / `false_negative_risk`: HIGH
- `explainability`: HIGH / `actionability`: 자동화 상담 범위 정의 / `repair_eligibility`: NONE
- `business_impact`: MEDIUM / `expected_frequency`: MEDIUM / `implementation_cost`: HIGH
- `recommended_tier`: Automation consultation / `recommended_milestone`: M9 / `free_or_paid_candidate`: EXPERT_SERVICE_CANDIDATE
- `current_status`: REQUIRES_BUSINESS_CONTEXT / `quality_gate_status`: NOT_EVALUATED / `exposure_status`: WITHHELD
- `priority_rationale`: 수익성 잠재력은 있지만 자동화 기회는 진단 규칙이 아니라 합의된 업무 범위에서만 제안해야 한다.
- `quality_gate_requirements`: `QG-A1`; 관찰·동의·민감 정보 정책·실행과 제안의 분리가 없으면 어떤 finding도 만들지 않는다.

### `REPEATED_RECONCILIATION_OR_EXPORT_CANDIDATE`

- `rule_code`: `REPEATED_RECONCILIATION_OR_EXPORT_CANDIDATE`
- `rule_name`: 반복 대사·내보내기 작업의 자동화 후보
- `detection_layer`: user-declared workflow context
- `user_problem`: 여러 시트/파일 사이 대사와 CSV·보고서 내보내기를 반복하며 누락 위험이 생김
- `detection_method`: 사용자가 제공한 반복 작업 단계와 예외·승인 지점을 기록해 상담 후보화
- `required_context`: 업무 흐름, 책임자, 승인 단계, 시스템 접근 권한, 개인정보 경계
- `evidence`: 반복 빈도 자체가 아니라 확인된 과정의 단계와 수동 조치
- `normal_exceptions`: 감사·승인 때문에 의도적으로 사람이 수행하는 작업
- `false_positive_risk`: HIGH / `false_negative_risk`: HIGH
- `explainability`: HIGH / `actionability`: 자동화 의뢰 전 범위·예외·승인 방식 합의 / `repair_eligibility`: NONE
- `business_impact`: MEDIUM / `expected_frequency`: MEDIUM / `implementation_cost`: HIGH
- `recommended_tier`: Automation consultation / `recommended_milestone`: M9 / `free_or_paid_candidate`: EXPERT_SERVICE_CANDIDATE
- `current_status`: REQUIRES_BUSINESS_CONTEXT / `quality_gate_status`: NOT_EVALUATED / `exposure_status`: WITHHELD
- `priority_rationale`: 자동화 가치가 “경고 수”가 아니라 반복 과정과 안전한 전달물에서 나오도록 분리한다.
- `quality_gate_requirements`: `QG-A1`; 고객 파일 내용·자격 증명·업무 규칙을 수집하지 않은 상태에서는 자동화 후보를 추정하지 않는다.

## M4-A.6 보류 후보

### `FORMULA_STORED_AS_TEXT_CANDIDATE`

- `rule_code`: `FORMULA_STORED_AS_TEXT_CANDIDATE`
- `rule_name`: 수식처럼 보이는 텍스트 셀 후보
- `detection_layer`: cell type and formula-like text static inspection
- `user_problem`: 계산 열에 수식 대신 텍스트가 들어가도 Excel이 즉시 오류를 내지 않을 수 있음
- `detection_method`: 셀 타입, 선행 등호 문자열, 주변 수식 영역을 함께 비교하는 보수적 형식 후보화
- `required_context`: 주변 수식 영역과 셀 타입. 현재 M4-A 정규화만으로는 충분하지 않음
- `evidence`: 값 없는 셀 타입/주변 수식 근거와 Excel 수식 표시줄 확인 안내
- `normal_exceptions`: 수식을 설명하기 위한 텍스트, 의도적으로 보관한 템플릿 문자열, 데이터 입력 열
- `false_positive_risk`: HIGH / `false_negative_risk`: MEDIUM
- `explainability`: HIGH / `actionability`: 셀 앞의 등호와 실제 셀 타입을 Excel에서 확인 / `repair_eligibility`: FUTURE_CANDIDATE
- `business_impact`: HIGH / `expected_frequency`: LOW / `implementation_cost`: MEDIUM
- `recommended_tier`: Precision-audit candidate / `recommended_milestone`: later M4 batch recommendation only / `free_or_paid_candidate`: PAID_DEEP_VALIDATION_CANDIDATE
- `current_status`: PLANNED / `quality_gate_status`: NOT_EVALUATED / `exposure_status`: WITHHELD
- `priority_rationale`: silent error 가능성은 있으나 텍스트 수식의 정상 용도가 많아 현재 두 M4 규칙과 함께 공개할 수 없다.
- `quality_gate_requirements`: `QG-P1`; formula-like text target, 문서/템플릿 text normal, 미지원 수식 구조를 분리하고 근거 부족 시 유보한다.

### `FORMULA_PARTIAL_EXTERNAL_REFERENCE_PATTERN`

- `rule_code`: `FORMULA_PARTIAL_EXTERNAL_REFERENCE_PATTERN`
- `rule_name`: 일부 수식에만 존재하는 외부 통합문서 참조 패턴 후보
- `detection_layer`: formula pattern plus external-reference syntax
- `user_problem`: 같은 계산 열에서 일부 셀만 외부 파일을 참조해 결과 출처가 달라질 수 있음
- `detection_method`: 지원되는 외부 참조 문법을 가진 수식과 주변 패턴을 비교
- `required_context`: 외부 참조 문법 지원, 외부 연결을 실행하지 않는 정규화, 정상 예외 구조
- `evidence`: 외부 참조 존재의 구조 차이와 Excel 연결/수식 확인법; 외부 파일명·내용은 비노출
- `normal_exceptions`: 의도된 예외 기간, 수동 조정, 다른 원본을 참조하는 보고 행
- `false_positive_risk`: HIGH / `false_negative_risk`: HIGH
- `explainability`: MEDIUM / `actionability`: Excel 연결과 해당 수식의 참조 원본 확인 / `repair_eligibility`: EXPERT_ONLY
- `business_impact`: HIGH / `expected_frequency`: LOW / `implementation_cost`: HIGH
- `recommended_tier`: Expert precision validation / `recommended_milestone`: later M4/M6 research / `free_or_paid_candidate`: EXPERT_SERVICE_CANDIDATE
- `current_status`: UNSUPPORTED / `quality_gate_status`: NOT_EVALUATED / `exposure_status`: WITHHELD
- `priority_rationale`: 외부 참조 존재 자체는 현재 규칙으로 알 수 있지만, 일부 셀만 참조하는 패턴은 현 M4-A가 안전하게 정규화하지 않는다.
- `quality_gate_requirements`: `QG-P1`; 외부 참조를 실행하지 않는 합성 target·normal·unsupported corpus와 비밀값 비노출을 먼저 입증해야 한다.

### `IFERROR_MASKED_ERROR_REVIEW_SIGNAL`

- `rule_code`: `IFERROR_MASKED_ERROR_REVIEW_SIGNAL`
- `rule_name`: 오류 처리 함수로 가려질 수 있는 오류 검토 신호
- `detection_layer`: formula token plus calculation/domain semantics
- `user_problem`: 오류 처리 함수가 기대한 예외를 처리하는지, 실제 오류를 가리는지 구분하기 어려움
- `detection_method`: 함수 사용 존재는 정적으로 확인할 수 있으나 실제로 가려진 오류 판단에는 계산 결과와 업무 맥락이 필요
- `required_context`: 계산 엔진, 오류 값, 업무 규칙, 오류 처리 의도
- `evidence`: 현재는 함수 사용 존재만 가능한 신호이며 숨겨진 오류·잘못된 결과는 주장하지 않음
- `normal_exceptions`: 의도된 빈값 처리, 선택적 조회, 데이터 미입력, 업무상 허용된 오류 처리
- `false_positive_risk`: HIGH / `false_negative_risk`: HIGH
- `explainability`: LOW / `actionability`: 수식 작성자와 오류 처리 의도를 확인 / `repair_eligibility`: EXPERT_ONLY
- `business_impact`: HIGH / `expected_frequency`: MEDIUM / `implementation_cost`: HIGH
- `recommended_tier`: Expert deep validation / `recommended_milestone`: M5/M6 research / `free_or_paid_candidate`: EXPERT_SERVICE_CANDIDATE
- `current_status`: REQUIRES_CALCULATION_ENGINE / `quality_gate_status`: NOT_EVALUATED / `exposure_status`: WITHHELD
- `priority_rationale`: 오류를 숨긴다는 단정은 정적 검사로 할 수 없으므로 상위 구현 배치나 M4-B 공개 대상이 아니다.
- `quality_gate_requirements`: `QG-C1` and `QG-B1`; 계산 기준과 업무상 정상 오류 처리 예외가 없으면 후보 자체를 만들지 않는다.

## M4-A.6 보충 메타데이터 — 모든 후보 레코드의 일부

아래 표는 본문 후보 레코드의 `evidence_required`, `abstain_conditions`, `precision_potential`을 명시한다. `precision_potential`은 실제 정확도 수치가 아니라 필요한 전제조건이 충족될 때의 상대적 검증 가능성이다.

| rule code | evidence_required | abstain_conditions | precision_potential |
| --- | --- | --- | --- |
| `FILE_OOXML_ENVELOPE_LIMIT` | ZIP/OOXML 안전 메타데이터 | 파싱 불가·경계 초과 시 안전 중단 | HIGH |
| `FILE_MACRO_ENABLED` | 매크로 파트 존재 | 지원하지 않는 파일 형식 | HIGH |
| `FILE_DRAWING_PARTS` | drawing 파트 존재 | 손상된 package | HIGH |
| `SHEET_HIDDEN`, `SHEET_VERY_HIDDEN` | visibility 상태 | workbook 구조를 읽지 못함 | HIGH |
| `SCAN_CELL_LIMIT_REACHED` | 실제 처리 셀 수와 한계 | 없음; 범위 제한을 항상 표시 | HIGH |
| `FORMULA_REF_ERROR` | 수식의 깨진 참조 토큰 | 수식이 아닌 텍스트·미지원 구문 | HIGH |
| `FORMULA_VISIBLE_ERROR_TOKEN` | 지원 오류 토큰 | 수식이 아닌 텍스트·미지원 구문 | HIGH |
| `DEFINED_NAME_BROKEN_REF` | 정의 이름 대상 구조 | 동적/미지원 이름 문법 | HIGH |
| `FORMULA_PATTERN_OUTLIER` | 3개 이상 지지하는 정규화 주변 패턴 | generic subtype·경계·제외 행·미지원 문법 | MEDIUM |
| `FORMULA_PATTERN_GAP` | 양쪽 지배 패턴과 상수/빈 셀 관계 | 수동 조정·구분/요약 행·미지원 구조 | MEDIUM |
| `FORMULA_NEW_ROW_NOT_EXTENDED` | 데이터 행과 수식 구간 연속성 | 행 역할·추가 맥락 불충분 | MEDIUM |
| `FORMULA_RANGE_BOUNDARY_DRIFT` | 지원 A1 범위와 인접 패턴 | 동적/3D/구조화 참조·의도된 구간 차이 | MEDIUM |
| `FORMULA_NAMED_RANGE_TARGET_DRIFT` | 이름 대상과 사용 구조 | 동적·지역·미지원 이름 문법 | LOW |
| `AGGREGATE_CRITERIA_RANGE_MISMATCH` | 지원 함수 인수의 시작점/길이 | offset·동적·구조화 참조의 의도 불명 | MEDIUM |
| `SUBTOTAL_TOTAL_DOUBLE_COUNT_RISK` | 행 역할과 참조 포함 관계 | 소계 역할·표시 목적이 불명 | LOW |
| `AGGREGATE_RANGE_EXCLUDES_NEW_ROWS` | 데이터 구간과 집계 끝점 | 기간/사업부 제외 또는 Table 동작 불명 | MEDIUM |
| `NUMBER_STORED_AS_TEXT` | 숫자 우세 열과 셀 형식 | 코드·선행 0·혼합 열 | MEDIUM |
| `INCONSISTENT_DATE_OR_TYPE_PATTERN` | 열 타입/표시 형식 프로필 | locale·코드·의도된 혼합 | LOW |
| `FORMULA_EXTERNAL_REFERENCE` | 외부 참조 token/관계 파트 | 지원하지 않는 외부 문법 | HIGH |
| `EXTERNAL_CONNECTION_DEPENDENCY` | connection/query 메타데이터 | 비밀값/미지원 연결 구조 | MEDIUM |
| `FORMULA_CIRCULAR_REFERENCE` | 완전한 참조 그래프와 계산 설정 | 동적/외부/이름 참조 또는 반복 계산 의도 | LOW |
| `CALCULATED_VALUE_ERROR_OR_STALE_CACHE` | 격리 엔진의 재계산 비교 | 엔진 불일치·미지원 함수·외부 연결 | LOW |
| `VERSION_FORMULA_CHANGE` | 안전한 두 파일 구조 비교 | 파일 동일성·보관 정책·매핑 기준 부족 | MEDIUM |
| `VERSION_EXTERNAL_DEPENDENCY_CHANGE` | 안전한 두 파일 메타데이터 비교 | 파일 쌍/보관/비밀 연결 정책 부족 | MEDIUM |
| `DECLARED_BUSINESS_RULE_ASSERTION` | 승인된 규칙·범위·예외 | 규칙 소유자·예외 정의 부족 | MEDIUM |
| `DECLARED_CROSS_SHEET_RECONCILIATION` | 승인된 대사 키·오차·기간 | 대사 계약·시차·예외 부족 | MEDIUM |
| `FINANCIAL_BALANCE_AND_ROLL_FORWARD_ASSERTION` | 재무 모델/계정/기간 계약 | 도메인 검토·조정 정의 부족 | LOW |
| `STATISTICAL_MODEL_RANGE_ALIGNMENT` | 모델·표본·결측 정책 | 통계 가정·계산 기준 부족 | LOW |
| `FORMULA_VOLATILE` | 지원 함수 token | 미지원/문자열 문맥 | HIGH |
| `FORMULA_WHOLE_COLUMN_REFERENCE` | 전체 열 A1 참조 | 미지원 참조 문법 | HIGH |
| `FORMULA_DEEP_NESTING` | 중첩 함수 구조 | 미지원/문자열 문맥 | HIGH |
| `FORMULA_COUNT_HIGH`, `MERGED_CELL_HEAVY` | workbook 구조 count | 부분 스캔 또는 파싱 실패 | HIGH |
| `REPEATED_MANUAL_TRANSFORMATION_CANDIDATE` | 사용자 동의된 반복 업무 단계 | 관찰·동의·보관 정책 부족 | LOW |
| `REPEATED_RECONCILIATION_OR_EXPORT_CANDIDATE` | 사용자 동의된 대사/내보내기 흐름 | 책임·접근·예외 정의 부족 | LOW |
| `FORMULA_STORED_AS_TEXT_CANDIDATE` | 셀 타입·formula-like text·주변 수식 | 의도된 설명 텍스트·템플릿 | LOW |
| `FORMULA_PARTIAL_EXTERNAL_REFERENCE_PATTERN` | 지원 외부 참조 패턴 비교 | 현 미지원 문법·외부 의도 불명 | LOW |
| `IFERROR_MASKED_ERROR_REVIEW_SIGNAL` | 계산 결과와 승인된 오류 처리 의도 | 계산/업무 맥락 부족 | LOW |

## 공개 전 상태 요약

| rule code | current status | quality gate | exposure | 비고 |
| --- | --- | --- | --- | --- |
| `FORMULA_PATTERN_OUTLIER` | PROTOTYPE | CONDITIONAL | INTERNAL_ONLY | 성능 인간 결정 전 비공개 |
| `FORMULA_PATTERN_GAP` | PROTOTYPE | CONDITIONAL | INTERNAL_ONLY | 성능 인간 결정 전 비공개 |
| `GENERIC_PATTERN_DRIFT` | UNSUPPORTED evidence subtype | NOT_EVALUATED | WITHHELD | 독립 규칙이 아니며 공개 금지 |
| 지원하지 않는 수식 문법 | UNSUPPORTED | NOT_EVALUATED | WITHHELD | 추측·대체 분류 금지 |
| 다음 구현 배치 후보 | PLANNED | NOT_EVALUATED | WITHHELD | 추천일 뿐 구현 승인 아님 |

이 카탈로그는 M4-B 화면, 새 진단 규칙, 계산 엔진, 버전 비교, 업무·재무·통계 검증, 자동 수정, 수정본 XLSX, 결제·계정·AI·클라우드 기능을 승인하거나 구현하지 않는다.
