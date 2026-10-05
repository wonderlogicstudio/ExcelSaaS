# 계산·기대값·불변 수정계획

## 분석·설명·계산·수정을 분리

지원 Registry는 `(function, syntax, operand types, reference kind, combination, engine version, profile version)`으로 판정한다. 함수 이름이 들어 있다는 것만으로 지원을 표시하지 않는다. 정적 AST 그림과 실제 실행 trace는 다른 산출물이다. 실행 순서를 기록하지 않은 엔진에 가상의 trace를 붙이지 않는다.

openpyxl은 수식을 평가하지 않으므로 별도 실제 계산 adapter가 필요하다.[S1](../research/SOURCES.md#s1) 기존 검증된 adapter가 있으면 재사용한다. 없다면 Apache POI 등 실제 evaluator를 좁은 프로필로 검증하고 버전을 고정한다.[S6](../research/SOURCES.md#s6) 모든 Excel 함수 지원을 기다리지도, 임의 Python eval/LLM 응답으로 대체하지도 않는다.

## 계산 경계

네트워크/외부파일/매크로/UDF를 허용하지 않는 isolated process에서 사본을 평가한다. 요청 timeout과 계산 프로세스 종료는 별개로 확인한다.[S7](../research/SOURCES.md#s7) hard deadline·memory·process lifetime·결과 크기를 제한하고 종료 뒤 scratch cleanup을 시험한다. 엔진의 디버그 로그에는 원문을 남기지 않는다.

처음 허용할 산술·내부 A1·SUM/ROUND 및 IF/IFERROR/AND/OR/ISNUMBER 등의 정확한 조합은 `capability_registry`에 시험 근거와 함께 등록한다. 이름은 후보 범위이며 무시험 허용표가 아니다. 미지원 함수가 사용되지 않은 분기에 있어도 첫 엄격 프로필은 거부할 수 있으며 이를 성공 계산으로 표시하지 않는다.

`ENGINE_UNSUPPORTED`, `ENGINE_TIMEOUT`, `ENGINE_RESOURCE_FAILURE`는 `#N/A/#VALUE!` 같은 Excel 의미 오류가 아니다. IFERROR가 엔진 실패를 정상 대체값으로 바꾸면 안 된다. 숫자/텍스트/빈칸/오류 타입, 날짜 체계, 정밀도·반올림을 구분한다.

## 고정 기대값과 독립 시험

주요 조합은 사람이 검토한 수학/정책 기대값과 타깃 Excel에서 생성한 고정 reference 결과를 비교한다. actual engine을 실행해 나온 결과를 그대로 정답으로 저장하지 않는다. fixture 결함은 독립 검토/버전 변경으로 처리한다. 보정된 숫자만 비교하지 말고 타입·오류·분기경계·참조를 검사한다. 패키지 예시는 실제 Excel reference가 아니다.

상품에서 보여줄 값의 출처 enum:
`SOURCE_VALUE`, `SOURCE_CACHED_VALUE`, `ENGINE_CALCULATED`, `POLICY_EXPECTED`, `SYNTHETIC_EXAMPLE`, `NOT_COMPUTED`.
B자료 관측값은 `POLICY_EXPECTED`가 아니다. 계산 before/after delta가 승인된 영향과 다른 경우 납품을 차단한다. 예상 영향이 소수 patch의 합이라고 가정하지 않고 선택한 전체 patch set을 함께 평가한다.

## RepairPlan 필수 스냅샷

- owner/job/product/SKU와 immutable 원본 hash·inventory hash
- profile·engine·rule·policy·template 버전
- candidate IDs와 승인할 exact target set
- 각 patch: sheet/cell locator, before typed value/formula/hash, after typed value/formula, 변환 이유, 기준 앵커/정책
- 예상 영향·비교 대상·계산 전후 typed 값·검증 coverage·제외 항목
- 기술적 보조 변경: 계산 캐시/계산 설정/필요한 OOXML part 목록과 사유
- plan 생성/만료, canonical plan digest, quote/order 연결, 필수 산출물

실제 민감값은 private plan에 저장하고 public log/metric에는 opaque ID와 상태만 남긴다. 해시라도 고객 간 연계 가능한 원본 지문은 공개 telemetry에 내지 않는다.

결제 전 서버에서 feasibility와 계획 후보를 만들 수 있으나 고객에게 유료 상세를 노출하지 않는다. 결제 후 상세 plan 전체를 보여주고 **그때도 실행하지 않는다**. 고객 선택이 달라지면 plan·예상 영향·digest를 다시 계산한다. 가격이 바뀌지 않아도 승인은 갱신한다.

입력·선택·정책·앵커·engine/profile·기술 부수 변경이 바뀌면 기존 승인 무효. 고객이 전부 거부하면 빈 plan을 실행하지 않는다. 동일 snapshot 기술 재시도는 기존 승인+유효 권리를 재검사하되 새로운 변경을 섞지 않는다.
