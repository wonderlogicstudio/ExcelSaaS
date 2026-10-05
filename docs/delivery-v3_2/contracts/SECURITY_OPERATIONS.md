# 운영·보관·개인정보·수령 안전

기존 Cloudflare Access/Worker, private R2, Gateway/HMAC, non-anonymous Cloud Run 경계를 재사용한다. 새 수정 기능 때문에 public origin, 장기 key, 고객 임의 URL fetch를 추가하지 않는다. 기존 보호 구현은 동일 증거를 재사용하며 부족한 항목만 검증한다.

## 데이터 구역

|구역|내용|처리|
|---|---|---|
|원본|사용자 업로드 bytes|원본 보존·짧은 목적별 TTL·owner만 접근|
|private plan/diff|정확한 셀·수식·값·정책|암호화 접근·owner/필요 최소 서비스만·정해진 TTL|
|scratch 계산|임시 작업용 복제|격리·네트워크 차단·성공/실패/kill 후 삭제|
|고객 산출물|수정본·changes·verification|owner+SKU 권리·검증·만료 검사|
|운영 로그/피드백|opaque ID·상태·버전·집계 bucket|파일명·시트·셀·수식·값·URL·free text 금지|
|결제/회계 기록|결제 식별자·상태·필수 증빙|고객 파일 보관과 분리, 적용법/정책 승인|

원본·정규화표·plan·report·결제기록의 TTL은 각각 승인·설정해야 한다. 기존 H3의 자동삭제가 새로운 결제/승인 대기 수명까지 자동 보장하지 않는다. TTL이 quote/승인/실행을 충족하지 못하면 새 결제를 막고 이미 PAID인 경우 동일 hash 복구/보상으로 처리한다.

## 프로세스 경계

강제 시간/메모리 제한, ZIP/XML 한도, 외부 네트워크/매크로/연결 금지, user code eval 금지, request 종료 후 실제 worker 종료/cleanup 증거. 동시실행/lease/취소 fence와 scratch 격리를 확인한다. Cloud Run request timeout만으로 코드 종료를 주장하지 않는다.[S7](../research/SOURCES.md#s7)

## 소유권과 private 전송

업로드·plan·approve·execute·download·delete마다 서버 owner 및 product entitlement 확인. cache-control no-store, 공개 CDN 캐시 금지, 서비스워커/브라우저 저장 민감 데이터 최소화. signed URL을 쓸 경우 짧은 수명/객체 한정/로그 차단/환불 이후의 잔여 접근을 검증한다. URL에 파일명·수식·plan 원문을 넣지 않는다.

## 비용·실패 운영

대형·중복·잘못된 요청 preflight 차단, 합리적 rate limit과 원자적 사용량 원장, scan/patch 재시도 상한과 재과금 방지. 예산 알림과 인스턴스 상한은 정확한 청구 하드캡이라고 표현하지 않는다. 실제 설정과 심한 실패의 kill switch·환불·지원 절차는 live 전 확인한다.

## 공개 승인

상품별 지원환경/가격/파일 유지기간/동의/취소/지원·실제 기능을 일치시킨다. 시험하지 않은 암호화·국내보관·무보관·법적 인증을 주장하지 않는다. 실고객 파일·실결제·새 과금 자원·계정/법률 승인·공개 배포는 이 문서 생성과 별개다.
