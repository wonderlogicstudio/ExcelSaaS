# 수정 적합성과 프로필

## 판매 전 필수 확인

고객이 업로드 권한이 있음을 확인한 `.xlsx` 한 파일을 대상으로 한다. 원본 전체 hash·package inventory·파일/시트/셀 상한·제한된 formula IR를 snapshot으로 고정한다. 고객 소유권과 검사 동의가 없는 파일을 분석하지 않는다. 결제 전에는 적합성·대상 범위·수정 종류·제외 이유를 무료로 알 수 있다. 새로운 전체 수정 수식/상세 계산표는 유료 projection으로 분리한다.

프로필은 후보 탐지와 다르다. `NUMBER_STORED_AS_TEXT`가 나왔다고 자동으로 RP01을 허용하지 않고, M4 GAP이 나왔다고 자동으로 RP02를 허용하지 않는다.

## 공통 첫 지원 경계

- plain OOXML `.xlsx`, 비암호화, 무매크로, 비서명, 지원하는 내부 셀·서식 구조.
- XLSM/VBA, 외부 통합문서/연결, Power Query, embedded object, 디지털서명, unsupported package part, shared/array/data-table/spill formula, 임의 add-in/UDF, `INDIRECT/OFFSET` 동적 참조, volatile/time/random/웹 함수, 반복 계산 순환참조는 첫 수정 프로필에서 제외.
- 시트 보호/숨김·병합·Table·subtotal 등은 함부로 해제하거나 건너뛰지 않는다. 첫 profile은 대상 셀 또는 평가에 필요한 구조가 해당하면 거부하고 설명한다. 특수 drawing/차트/확장 part가 있으면 보존 검증이 없는 한 수정 거부.
- 파일별 max 10 MiB, 기존 OOXML 해제/entry/압축비 제한보다 완화하지 않는다. 추가 formula/cell/patch/time/memory 상한은 서버 설정·시험으로 고정한다. UI 임의 수치로 판단하지 않는다.
- formula가 하나라도 있으면 첫 수정 프로필은 **워크북의 수식/참조 전체가 검증된 계산 profile 안에 있음**을 요구한다. 부분 검사로 누락 의존성이 있을 가능성을 덮지 않는다. 이후 impact closure만 검증하는 profile은 별도 확장이다.
- 값만 있는 workbook은 계산 항목 `NOT_APPLICABLE`이 가능하지만 패치·보존·자료 정책 검증은 생략하지 않는다.

## RP01_NUMERIC_TEXT_FIELD_V1

입력: 사용자가 ‘거래 ID가 아닌 금액 또는 수량’으로 선언한 필드와 선택 셀, ko-KR 정수 숫자 해석 정책. 숫자문자열 그대로와 바뀔 숫자 타입을 보여준다. 쉼표는 명확한 3자리 그룹만 허용하고, 부호·범위·정밀도 조건을 독립 검사한다. 첫 profile의 유효 정수 유효숫자는 최대 15자리로 제한한다. 금액/수량 역할 확인 없으면 거부한다.

거부: `00123` 등 선행0, ID/계좌/전화/우편번호, 공백으로 둘러싼 불명확 값, 날짜/%, 소수점·지수 표기, 단위문자, 빈칸/null, 식, 이미 숫자인 셀, 초과 정밀도. 빈칸은 0으로 만들지 않는다. ‘−0’처럼 표기가 의미를 가질 수 있는 특수형도 첫 profile은 거부한다.

변경 종류는 `TYPE_NORMALIZATION`이다. 값이 같더라도 SUM/lookup/text comparison에서 의미가 달라질 수 있으므로 전후 계산 및 예상 delta를 검사한다. 계산 결과가 반드시 동일해야 한다고 가정하지 않는다. 변경 후 결과의 차이는 승인 전 보이고 정책과 일치해야 한다. 고객 표시 형식과 스타일은 계획 밖으로 바꾸지 않는다.

## RP02_APPROVED_FORMULA_RESTORE_V1

입력: 기준 셀과 기준 수식, 대상 **진짜 빈 셀** 목록, 대상 행에도 같은 업무 규칙을 적용한다는 확인. 기준은 사용자가 지정한 앵커 또는 등록된 승인 템플릿이다. 주변 패턴은 추천 근거일 뿐 정답 결정권이 아니다.

AST/참조 번역으로 각 대상의 정확한 수식을 만들고 사용자에게 셀별 미리보기를 제공한다. 절대/상대/혼합 참조를 보존한다. 불연속 셀을 연속 범위로 확대하지 않는다. 공백 문자열, `=""` 수식, 이미 값/수식이 있는 셀은 ‘빈칸’으로 덮어쓰지 않는다.

처음부터 복합 수식을 포함하되 검증된 grammar/조합만 허용한다. `ROUND(B6*C6*(1-D6),0)` 같은 앵커를 E8로 옮기는 경우 B8/C8/D8 참조 및 expected value를 독립 확인한다. AND/ISNUMBER/IF/ROUND 조합 등은 계산 profile fixture가 있을 때만 제공한다.

고정 단가/세율 셀의 `$`를 바꾸거나 원자료를 새 값으로 만드는 것은 이 profile에 포함하지 않는다. 외부 기준 없는 누락금액 채우기, 다른 자료 B값으로 덮어쓰기, IF→IFS/IFERROR 추가, SUMIF→SUMIFS 정답 추천은 제외한다.

## 불충족 상태

`UNSUPPORTED_FILE`, `UNSUPPORTED_FORMULA`, `UNCONFIRMED_BUSINESS_INTENT`, `INSUFFICIENT_EVIDENCE`, `NO_ELIGIBLE_CHANGES`, `PREVIEW_VALIDATION_FAILED`, `LIMIT_EXCEEDED`는 ‘수정 가능’이 아니다. quote/결제 차단, 구체적인 다음 준비 행동 제공. 고객이 돈을 내겠다고 해도 안전 gate를 해제하지 않는다.
