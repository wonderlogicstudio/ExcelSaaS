# 고정 합성 계약 사례

REPAIR_DELIVERY_SPEC.json은 타입 정규화 1개와 수식 복원 1개의 공개 예시다. 기대값은 산술로 별도 정의했으며 제품 실행 결과로 사후 생성하지 않았다. NEGATIVE_ACCEPTANCE_CASES.json은 실제 앱에서 추가할 32개 부정/경계 시나리오다. comparison/의 세 JSON은 V3.1 원본 그대로다.

이 파일의 존재나 contract_oracle 시험 통과는 실제 XLSX patcher/PG/Excel 계산검증 성공이 아니다. 실제 앱 검사에는 원본 fixture→API→engine→파일을 새로 생성해야 한다. 정답의 결함 발견 시 기록·독립 확인·버전 변경하고 조용히 엔진 결과에 맞추지 않는다.
