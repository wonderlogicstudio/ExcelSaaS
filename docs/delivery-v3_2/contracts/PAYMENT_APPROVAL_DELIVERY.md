# 결제·변경승인·실행·납품의 분리

## 결제 전

필수: 입력과 owner 확인, 수정 feasibility, 명확한 대상 범위·제외/제한, 산출물 파일 종류, 총액·세금표시·과금단위, 유효기간·보관기간, 실패·거부·취소 정책. 지원 못하는 상품에는 결제 버튼을 내지 않는다. 진단 결과가 없다고 실패 요금을 만들지 않는다.

범위와 안전성 등 구매에 중요한 정보는 무료로 공개한다. 새 유료 상세 수식/행별 기대값은 서버 projection으로 제한한다.[S5](../research/SOURCES.md#s5) API가 상세를 보낸 뒤 CSS blur로 가리는 것은 권한 통제가 아니다.

## 구매권

서버의 owner/SKU/input/spec/quote/amount/currency를 공식 PG 승인·조회 결과와 대조한다.[S3](../research/SOURCES.md#s3)[S4](../research/SOURCES.md#s4) redirect 성공·클라이언트 paid=true·임의 헤더를 근거로 사용권을 만들지 않는다. 현재 구현된 PG adapter·원장을 재사용한다. 필요한 공식 sandbox가 없으면 NOT_RUN으로 남기고 local adapter 개발은 계속한다. live key/실금액/취소 호출은 별도 승인이다.

`APPROVED_REPAIR` 권리와 `TWO_FILE_COMPARISON` 권리는 다르다. 같은 사용자의 다른 주문이라도 권리를 섞지 않는다. 아직 실행 가능한 수정 engine이 없으면 live 수정권 판매를 금지한다.

## 결제 후, 변경 전

정확한 계획의 전후 수식·타입·셀·예상 영향·남을 문제·보존 한계를 **충분히** 보여준다. 내용을 다 보여주지 않은 채 '전체 수정 동의'만 받지 않는다. 이는 유료 내역 공개와 실제 실행 동의를 분리한 것이다.

고객은 세 가지를 선택한다: 승인 / 대상 재선택 후 새 계획 보기 / 거부·취소. 체크박스 기본선택 금지. 기존 ‘확인함’ 상태로 자동 승인 금지. 선택 subset도 전체 예상 영향을 다시 계산하고 digest를 새로 만들어 승인한다.

서버 승인에는 `owner_id, input_version_hash, plan_digest, profile_version, selected_patch_set, expires_at, approval_id`를 묶는다. plan_digest는 서버 생성 canonical 데이터 기준이다. 사용자에게 보인 내용과 실제 실행 내용이 같아야 한다.[S8](../research/SOURCES.md#s8) 승인 행위는 인증 세션·CSRF·재인증 필요조건을 적용하고 거래상태 변경을 서버가 검증한다.

## 상태 축

- payment: NONE/PENDING/UNKNOWN/PAID/CANCELLED; refund: NONE/PENDING/SUCCEEDED/FAILED.
- entitlement: NONE/ACTIVE/REVOKED/EXPIRED.
- plan: DRAFT/READY/SUPERSEDED/EXPIRED/REJECTED.
- approval: NONE/APPROVED/REVOKED/EXPIRED.
- job: WAITING_APPROVAL/QUEUED/RUNNING/FAILED/TIMED_OUT/CANCELLING/CANCELLED/SUCCEEDED.
- validation: PENDING/PASS/FAIL/NOT_RUN.
- artifact: NOT_CREATED/VALIDATING/READY/QUARANTINED/EXPIRED/DELETED.

서로 자동 등치하지 않는다. PAID≠APPROVED, APPROVED≠SUCCEEDED, SUCCEEDED≠READY. 비교 상품은 변경승인 NOT_APPLICABLE이지만 상품/owner/결제/검증은 여전히 필수다.

## 재시도·수령 복구

DB/PG/object storage는 단일 transaction이 아니다. 멱등키·outbox/reconciliation·조건부 전이로 webhook 중복/역전·응답유실·이중클릭·worker crash를 복구한다. PAYMENT_UNKNOWN에 새 주문을 무한 생성하지 않는다. 기술 재실행과 재다운로드는 같은 권리이며 새로운 결제가 아니다.

결제 후 입력이 만료되면 동일 원본 hash 재업로드 또는 승인된 보상 경로다. 새로운 입력으로 기존 승인·견적을 대체하지 않는다. 이미 결제한 주문은 유효기간/데이터 수명에 맞춘 정책을 적용하고 구매 대기 때문에 원본 보관을 몰래 늘리지 않는다.

## 실패·거부·환불의 제품 제안

권장 초기 정책: 실행 전 전체 변경 거부는 취소 경로, 제공자가 검증된 수정 패키지를 못 만들면 재과금 없는 재시도 또는 환불/보상. 이는 소유자가 가격·법률 검토와 함께 확정할 정책 제안이며 법적 확정 규칙이 아니다. 실제 공개 정책을 코드와 동일하게 유지한다.

후검증 보고서만 주고 수정상품 대금을 정상 이행으로 확정하지 않는다. 일부 변경 성공을 전체 주문 성공으로 바꾸지 않는다. 첫 profile은 승인된 묶음 전체가 통과하는 경우만 납품하고, 부분납품은 새 범위·동의·보상 정책 없이는 금지한다.

환불·권리회수 후 새 다운로드 차단, 이미 발급된 signed URL의 실제 잔여 수명과 취소 방법 시험. 이미 고객 PC로 내려간 파일을 회수할 수 있다고 약속하지 않는다.
