# 기술 출처와 확인 범위

확인일: 2026-09-12. 현재 실행계약에 필요한 기술 사실만 재확인했다. 신규 고객 인터뷰·가격 수용·시장 성공을 조사/검증했다고 주장하지 않는다. 기존 시장 연구는 보존한 V3 ZIP에 있다. 구현 시 PG/클라우드 계약은 다시 최신 공식 문서로 확인한다.

<a id="s1"></a>
## S1 — openpyxl

[Simple formulae](https://openpyxl.readthedocs.io/en/stable/simple_formulae.html)

반영: 수식 평가 기능을 제공하지 않으므로 값 기반 비교와 재계산을 구분한다.

<a id="s2"></a>
## S2 — OWASP

[API3:2023 Broken Object Property Level Authorization](https://owasp.org/API-Security/editions/2023/en/0xa3-broken-object-property-level-authorization/)

반영: 객체 접근과 응답 속성별 권한 검사를 적용한다.

<a id="s3"></a>
## S3 — 토스페이먼츠

[코어 API — 결제 승인·조회·취소](https://docs.tosspayments.com/reference)

반영: 서버의 orderId/amount/paymentKey를 공식 승인·조회와 연결한다.

<a id="s4"></a>
## S4 — OWASP

[CSV Injection](https://owasp.org/www-community/attacks/CSV_Injection)

반영: 비신뢰 텍스트의 CSV 수식 해석 위험을 시험한다.

<a id="s5"></a>
## S5 — Google Cloud

[Configure request timeout for services](https://docs.cloud.google.com/run/docs/configuring/request-timeout)

반영: HTTP timeout과 작업 코드 종료가 별개다.

## 저장소 확인

GitHub connector로 `docs/09_CURRENT_MILESTONE.md`의 현재 원격 발췌를 확인했다. 원격에는 2026-09-10 P1 필터 구현·시각검수 대기와 과거 H2/H3 상태가 남아 있었다. 이는 사용자의 최신 로컬 완료 상태를 부정하거나 재개발을 요구하는 근거가 아니다. 원격 snapshot에서 보았던 문제는 L01에서 현재 코드에 실제 남아 있는지 확인한 뒤 보완한다. 사용자 PC와 운영환경을 직접 실행하지 않았다.

[원격 상태 문서](https://github.com/wonderlogicstudio/ExcelSaaS/blob/main/docs/09_CURRENT_MILESTONE.md)
