# 기술·저장소 근거

공식 원문과 고정 Git snapshot을 2026-09-12 확인했다. 상품/프로필/환불/단계 수는 별도 설계 판단이며 사용자 수요·법률 적합성 검증 결과가 아니다.

<a id="s1"></a>
## S1 — openpyxl: Simple Formulae

[Simple Formulae](https://openpyxl.readthedocs.io/en/stable/simple_formulae.html)

수식을 저장/파싱하는 것과 계산하는 것은 다르다. openpyxl을 실제 계산 성공의 근거로 쓰지 않는다.

<a id="s2"></a>
## S2 — openpyxl: Tutorial

[Tutorial](https://openpyxl.readthedocs.io/en/stable/tutorial.html)

일반 load/save의 미지원 요소 보존 위험을 확인했다. 사본·지원 inventory·최소 패치·후검증을 제품 설계로 요구한다.

<a id="s3"></a>
## S3 — Toss Payments: 카드/간편결제 통합결제창 연동하기

[카드/간편결제 통합결제창 연동하기](https://docs.tosspayments.com/guides/v2/payment-window/integration)

공식 서버 승인 흐름과 주문 금액 검증을 사용한다. 수정 승인 절차는 WorkbookCare 별도 설계다.

<a id="s4"></a>
## S4 — Toss Payments: 코어 API

[코어 API](https://docs.tosspayments.com/reference)

승인/조회/취소 API와 멱등 처리 기준은 구현 시 해당 공식 문서 및 실제 계약에 맞춘다. 환불 정책을 법적으로 확정하는 근거는 아니다.

<a id="s5"></a>
## S5 — OWASP: API3:2023 Broken Object Property Level Authorization

[API3:2023 Broken Object Property Level Authorization](https://owasp.org/API-Security/editions/2023/en/0xa3-broken-object-property-level-authorization/)

상품·소유권뿐 아니라 응답 필드의 사용권을 서버에서 제한한다.

<a id="s6"></a>
## S6 — Apache POI: Formula Evaluation

[Formula Evaluation](https://poi.apache.org/components/spreadsheet/eval.html)

실제 formula evaluator 후보와 cached values 처리 API를 확인했다. 특정 Excel 파일의 결과 일치나 전체함수 지원을 입증하지 않는다.

<a id="s7"></a>
## S7 — Google Cloud: Configure request timeout for services

[Configure request timeout for services](https://docs.cloud.google.com/run/docs/configuring/request-timeout)

Cloud Run 응답 timeout은 container/code 종료와 동일하지 않다. 작업별 격리/종료 시험은 별도다.

<a id="s8"></a>
## S8 — OWASP: Transaction Authorization Cheat Sheet

[Transaction Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Transaction_Authorization_Cheat_Sheet.html)

승인 시 중요한 변경 내용을 알 수 있어야 하며 검증·실행·상태전이는 서버에서 강제해야 한다.

<a id="g1"></a>
## G1 — WorkbookCare GitHub: main reference

[main reference](https://github.com/wonderlogicstudio/ExcelSaaS/commit/47e5e54f2316e09a44e4395dd31c7afdf9803472)

2026-09-12 읽기 전용 확인한 main. 로컬 최신 상태와 같다고 가정하지 않는다.

<a id="g2"></a>
## G2 — WorkbookCare GitHub: service_catalog.py

[service_catalog.py](https://github.com/wonderlogicstudio/ExcelSaaS/blob/47e5e54f2316e09a44e4395dd31c7afdf9803472/apps/api/app/service_catalog.py)

해당 snapshot에서 PRECISION_VERIFICATION/APPROVED_REPAIR/AUTOMATION_CONSULTATION은 PLANNED다.

<a id="g3"></a>
## G3 — WorkbookCare GitHub: main.py

[main.py](https://github.com/wonderlogicstudio/ExcelSaaS/blob/47e5e54f2316e09a44e4395dd31c7afdf9803472/apps/api/app/main.py)

확인한 앱 경로는 scans/formula-audits. 이 읽기만으로 전체 저장소·운영환경을 보안 인증하지 않는다.
