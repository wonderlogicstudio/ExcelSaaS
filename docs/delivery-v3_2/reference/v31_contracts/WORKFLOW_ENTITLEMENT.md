# 작업·견적·결제·결과 수령 계약

## 최소 구조

기존 React/TS, Worker, private R2, Gateway, FastAPI/Cloud Run 보호 경로를 재사용한다. 신규 업무는 전용 service/endpoint를 추가하고 기존 `/v1/scans`와 `/v1/formula-audits`의 의미를 바꾸지 않는다. 이미 있는 DB/작업 저장소·PG adapter를 우선 사용한다. 없어도 서버less 인스턴스 메모리나 임시 파일을 영구 주문 원장으로 쓰지 않는다.

구현 언어/세부 endpoint는 Codex가 정하되 다음 논리 계약을 만족한다. DB/인증 공급자를 새로 쓰는 비용/계약은 소유자 승인 대상이다. 로컬 durable adapter로 개발하더라도 다중 인스턴스 운영이 확인되지 않았으면 live ready가 아니다.

## 논리 API와 projection

|행동|전제|허용 응답|
|---|---|---|
|create/update input, mapping|인증된 owner; 아직 구매 spec 미확정|본인 원본 preview, 검증 사유, 원천 row count|
|preflight|두 입력과 의미 확인; 서버 검증|적합성·범위·자료오류·제외/모호 제한. paid 결과 없음|
|quote|적합성 통과; spec/기간 고정|총액·통화·포함/제외·제공기간·실패처리·만료|
|confirm payment|서버 quote와 PG 승인/조회 일치|주문 상태/사용권. raw provider 응답 미노출|
|execute/retry|유효 권리 또는 server-side 비공개 test grant; 같은 spec|job 상태·안전 오류·완료 artifact ID|
|get result|owner + 유효 사용권 + 검증된 result + 미만료|허용된 paid 결과 필드|
|download|동일 권한 재검사 + 파일 검증 + 미만료|인증된 전달 또는 짧은 object 한정 URL|
|resume status|owner|같은 주문 상태; 권한 없으면 결과 원문 없음|
|cancel/delete|owner·현재 상태·별도 권리검사|취소/삭제 접수·완료 상태, 필요한 보상 경로|

paid=true/owner_id/result_ready/amount 같은 클라이언트 필드는 신뢰하지 않는다. 브라우저 숨김 대신 서버 allowlist projection을 사용한다. [S2](../research/TECHNICAL_SOURCES.md#s2)

## 상태를 독립 관리

- input: `UPLOADING → AVAILABLE → EXPIRED/DELETED/REJECTED`.
- preflight: `DRAFT → CHECKING → ELIGIBLE / ELIGIBLE_WITH_LIMITATIONS / NOT_ELIGIBLE`.
- payment: `NOT_STARTED → PENDING → PAID / FAILED / CANCELLED` (응답 유실 시 `PAYMENT_UNKNOWN`에서 공식 조회로 복구), 취소·환불은 별도 `REFUND_PENDING → REFUNDED/REFUND_FAILED`.
- job: `NOT_STARTED → QUEUED/RUNNING → SUCCEEDED / FAILED / TIMED_OUT / CANCELLED`.
- artifact: `NOT_CREATED → VALIDATING → READY / QUARANTINED → EXPIRED/DELETED`.
- entitlement: `NONE → ACTIVE → REVOKED/EXPIRED`, 보상·재시도 자격과 구분.

`job=SUCCEEDED`가 자동으로 `artifact=READY`나 `payment=PAID`를 의미하지 않는다. 실제 단계 이벤트가 없으면 진행 퍼센트를 만들어내지 않는다. DB state transition은 조건부 update/transaction을 써서 마지막 도착 이벤트가 무조건 덮어쓰지 않게 한다.

## 결합·멱등성

`owner + operation + idempotency_key`를 원장에 저장하고 spec_hash가 같으면 기존 응답, 다르면 conflict를 반환한다. canonical input 버전이 바뀌면 새 spec/견적이 필요하다. 결제 완료 원장의 spec을 수정하지 않는다. 키·금액·기간이 같아 보여도 원천 바뀜을 묵시 허용하지 않는다.

PG 인증 redirect만으로 PAID를 설정하지 않는다. 서버에 저장한 금액·orderId·대상 spec과 공식 PG 승인/조회 결과를 일치시킨다. webhook의 공식 인증·재전송·조회 방식은 구현 시 최신 문서를 확인하고 임의 헤더 서명 표준을 만들지 않는다. [S3](../research/TECHNICAL_SOURCES.md#s3)

중복 결제 승인·이벤트 순서 역전·응답 유실·타임아웃에는 PG 상태 조회로 복구한다. DB와 PG 사이에는 원자적 transaction이 없으므로 reconciliation/outbox 또는 동등한 복구 원장을 사용한다. 미확정 승인에 새 주문을 자동 생성하지 않는다. 중복 결제가 실제 확인되면 취소/보상 기록을 남긴다.

동일 작업 기술 재시도·재다운로드는 새 요금 없음. 다음 기간 새 입력은 새 작업/견적이다. 입력·정책·engine version이 바뀌면 기존 구매권을 몰래 전용하지 않는다. 기술 장애로 artifact를 다시 만들 때 같은 spec/version을 재현하지 못하면 변경 동의 또는 보상 경로로 간다.

## 새로고침·종료·재방문

개인별 최소 작업 목록/주문 상태는 필요하다. 범용 대시보드를 만들라는 뜻은 아니다. 인증 복구 후 opaque job/order ID로 서버 상태를 조회하며, 값·시트·파일명·signed URL을 브라우저 URL에 넣지 않는다. 브라우저 local state만 남아 있어 결과가 사라지는 상용 흐름 금지.

이미 결제했지만 입력이 만료되면 같은 원천 hash의 재업로드 허용 또는 승인된 보상 정책을 제공한다. 새로운 입력으로 치환하지 않는다. raw 입력/정규화 자료/결과의 보관 기간은 서로 다르고 약관·가격표에 실제 적용 값을 명시해야 한다.

## 견적과 파일 만료의 경계

견적 만료는 필요한 입력/정규화 자료의 실제 잔여 수명과 처리 여유보다 짧아야 한다. 자료가 이미 만료됐거나 처리할 수명 여유가 없으면 결제를 시작하지 않는다. 결제 대기 중 자료 삭제/만료가 발생하면 결제상태 조회와 재업로드/보상 경로로 분기하며, 보관 동의 없이 자료 수명을 무기한 늘리지 않는다. 외부 PG와 저장소/DB의 상태를 하나의 원자적 거래라고 가정하지 않는다.

## 테스트 결제와 실사용권

L04까지는 production에서 비활성인 서버 내부 test grant로 종단시험할 수 있다. UI toggle이나 public endpoint로 grant 발급 금지. L05는 공식 PG sandbox의 실제 승인·조회·취소 adapter까지 구현하고 mock-only 상태는 분리한다. live 계약/key/가격 승인 전에는 실결제를 열지 않는다.

환불/권리회수 후 결과 링크가 남지 않게 프록시/짧은 서명URL/객체정리 정책을 시험한다. 이미 내려받은 파일을 회수할 수 있다고 약속하지 않는다. 자료의 즉시 삭제를 요청하면 재생성/다운로드 가능 여부도 명확히 안내한다.
