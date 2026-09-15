# SCROLL-02 — 스크롤 개선 검증 완료

2·3단계의 사용자 작업 후 새 계산 결과·검증한 예시·정확한 변경 제목으로 스크롤과 포커스를 이동하도록 수정했습니다. 승인 후 결과와 사본 준비 완료도 한 번만 안내합니다. 이전 단계·작업으로 이동한 뒤 늦게 도착하는 결과, 중복 polling/execute 응답은 화면을 빼앗지 않도록 검사했습니다. 정확한 변경 승인·별도 실행·검사/수정 범위는 유지했습니다.

표적24/전체web157/type/build, 전체 회귀web157/Worker16/API240/Ruff/M4exact36 exit0. 기존 보호 베타 웹 배포와 실제 데스크톱/모바일 화면·예상값·다운로드 검증 완료. API48파일·보호152파일은 그대로이며 API00017-xid와 기존 보안/결제 경계를 유지했습니다. 상세한 실제 이동 위치와 산출물은 증거에 기록했습니다. 원격push 없음, 다음 단위 자동 실행 없음. 이번 작업은 스크롤 개선이며 전체10조작 목표나 초보자 이해도 합격을 의미하지 않습니다.

[검증 기록](delivery-v3_2/reviews/SCROLL-02.md)

---

# FLOW-01 최신 결과 — 보호 베타 검증 완료

기존 두 수정 기능의 실제 보호 베타 흐름과 다운로드 검증을 마쳤습니다. 숫자 정리8개/합계2,159,436, 빈 수식3개/5,232·3,551·7,800/합계937,923이 화면과 고정 예상값에 일치했습니다. 실제 다운로드6개, 수정본별725개 예상값 및 원본·비대상 보존 검증 PASS. 같은 베타 재업로드에서 RP01 구조8→0/수식3유지, RP02 수식3→0/구조8유지를 확인했습니다. 지원 검사 후 자동 계산, 정확한 변경의 직접 표시, 별도 승인 후 결과 단계 이동을 적용했고 별도 실행·승인 경계는 유지했습니다.

전체 회귀 exit0(web141/Worker16/API240/Ruff/M4exact36), 복잡도 통합5사례 exit0, 승인받은 실제 Excel4파일 읽기 전용 검증 PASS. 이 Excel4개는 호환성 증거용 출력이며 최종 복잡도 다운로드와 구분합니다. API00017-xid와 Workerc6e1ed05를 기존 보호 베타에 배포했습니다. 원격 Git push 없음.

UX는 부분 충족입니다: 두 경로 모두4단계·필수 앱 조작16회·필수 셀/수식 입력0회. 10회 목표는 미달이며, 긴 전체 변경/영향 목록과 초보자의 실제 이해도는 남은 과제입니다. 제품 엔진·화면의 기술 검증과 고객 사용성 승인, D08 상용화 판단은 별개입니다. FLOW-01의 검증된 수정과 기록을 선별 local commit한 뒤 멈추며 다음 단위는 승인하지 않았습니다.

[검증 기록](delivery-v3_2/reviews/FLOW-01.md) · [증거](delivery-v3_2/reviews/evidence/FLOW-01.json)

---

# FLOW-01 latest verified checkpoint

FLOW-01 remains approved but incomplete. Existing protected-beta RP01/RP02 actual screen flows, six downloads and same-beta rescan passed on the pre-change deployment. Each repaired workbook matches725 frozen cached values; RP01 static8→0/M4remaining3, RP02 M4 3→0/staticremaining8. This is not evidence for the new local report/UI deployment. Scoped source corrections and independent code review PASS; final full regression exit1: web141/build and Worker16 PASS, API228passed/12failed at stale-compatibility gates (8 REFERENCE_NOT_VERIFIED,4 PRODUCT_NOT_READY). Separately API Ruff and M4 frozen36-candidate checks exit0. Full regression is not PASS. New source binds same-detector resolution/completeness, truthful abstention, direct exact-change display, automatic calculation, and one-shot approved navigation with safe return/cancel. Existing explicit approval, separate execution and private beta boundaries remain. Fresh actual synthetic compatibility artifacts were generated but not published READY. Actual Excel reopening NOT_RUN; compatibility remains STALE until new measured evidence is registered. Updated-beta screen/release/runtime verification NOT_RUN. Local HTML opening was blocked by browser URL policy; no workaround or visual PASS claimed. No deployment, local commit or remote push this unit. Initial usability target10 activations NOT_MET (baseline RP02=19); updated count and human comprehension NOT_RUN. Awaiting explicit Excel COM method approval only; no next unit approval inferred. [Work order and evidence](delivery-v3_2/reviews/FLOW-01.md).

---

## 2026-09-15 — ORCH-02 모델 분리 설정 검증

PL AstraMedium·빌더5.5Medium·리뷰어AstraHigh, 단순Low/복잡High 배정 규칙을 반영했다. 실제5.5Medium 빌더/AstraHigh 리뷰어 위임, TOML/격리native config-read/독립리뷰 PASS. 기존 제품·샘플·사용자460파일hash와 과거 기록 보존. 현재 루트 모델 자동 전환·Desktop 개별역할 자동등록·절감률은 미검증/미측정. 제품변경·배포·push 없음. [리뷰](delivery-v3_2/reviews/MODEL_ROUTING.md). 다음 FLOW-01 미승인, D08 PARTIAL 유지.

---

## 2026-09-15 — ORCH-01 세 역할 운영 구성 검증 / 다음 단위 전 정지

PL·빌더·리뷰어 설정, 하위 동시성2, 서비스 대전제/승인/증거/편의성 기준과 기존 지침 연결을 구성했다. 실제 설치 Codex의 격리 홈 strict config/read exit0, 독립 내용 리뷰에서 합성 증거 금지 충돌을 수정 후 PASS. 자동 승인 검토 capacity로3회 미실행됐던 운영 문서 적용은4회차 정상 승인 경로로 성공했다. 제품·기존샘플·사용자파일460개 hash 보존. 4단계/세다운로드까지10activation/주소·수식입력0/재입력0/주CTA1은 미측정 목표다. 실제 Desktop 역할 자동로드/권한강제/사용성/제품회귀/배포/push는 미실행. [리뷰](delivery-v3_2/reviews/ORCHESTRATION.md). 현재 CONFIGURED_VERIFIED_AWAITING_OWNER, D08 PARTIAL 유지, 다음 FLOW-01 미승인.

---

## 2026-09-13 — 수정 제안·희망 결과 대조 UX 검증 완료

시트·발견 위치 기반 제안, 금액/개수/구분 번호 질문, 실제 원본 기준 선택, 대표 계산 예시→전체 변경→별도 승인을 구현했다. 의견 없음/숫자 희망값/같은 계산 방식 요청을 구별하고 불일치·대조 불가 시 승인 경로를 차단한다. 베타 RP01 일부 합2,029,526·RP02 5,232/3,551/7,800·합937,923, 실제6다운로드·설치Excel4개 PASS. 전체 웹139/Worker16/API231/Ruff/M4exact36 exit0, 최종 웹139·타입·빌드 exit0.

Worker `1fa2992b-c75d-400b-8acc-14dd484c7a40`100%, private API00014-nah·보안·결제OFF 유지. 의견은 현재 브라우저 세션만이며 서버 승인기록/납품 보고서에 영속 연결하지 않는다. 이번 UX ENGINEERING_VERIFIED_AWAITING_OWNER / D08전체 PARTIAL. 다음 한 단위는 요청 조건의 서버 승인계획·재검증 보고서 연결 제안만, 자동 실행하지 않고 정지한다. 아래 기록은 이전 이력이다.

[리뷰](delivery-v3_2/reviews/PROPOSAL_FLOW.md)

---

## 2026-09-13 — 단계별 탭·원본 비교 UX 구현 및 보호 베타 검증 완료

무료 진단 → 수정 범위·검증 → 변경 승인 → 결과 받기를 완료 조건으로 열리는4개 탭으로 정리했다. 원본 수식/상수/빈 셀과 비교 근거, 선택과 개인 메모 분리, 공통 한계 한 곳, 무료 견적 제거, 중복 수정 진입 통합을 구현했다. 실제 베타16건/3유형·정상0·지원 제외, RP01일부 합2,029,526·RP02합937,923 및 실제6다운로드·설치Excel4개를 확인했다. full118웹/16Worker/231API/36M4 exit0 뒤 프런트 최종121·타입·빌드와 실제 모바일 재시험PASS.

Worker `4f756e00-dc3d-4c2c-ae5c-862e79b6422c`100%, private API00014-nah·기존 보안·결제OFF 그대로다. [GUIDED_FLOW review](delivery-v3_2/reviews/GUIDED_FLOW.md), [확인 행동](delivery-v3_2/owner_action.md). 이번 UX ENGINEERING_VERIFIED_AWAITING_OWNER, D08전체 PARTIAL. 다음 한 단위는 무료 진단 요약 보고서 제안만이며 자동 실행하지 않고 정지한다. 아래 기록은 당시 이력이다.

---

## 2026-09-13 — Main Flow / IA 구현·보호 베타 검증 완료

무료 진단 → 유형/셀 근거 → 수정 검토 선택 → 기존 사전 검사·별도 승인·세 파일 납품으로 연결하고 정밀 검증·비교·자동화를 독립 페이지로 분리했다. 기존 기능·진행·예상 값은 보존했다. 실제 복합16건/3유형·정상0건·RP01 일부 합2,029,526·RP02 합937,923·비교464그룹/큰 정수 차액1원을 대조했다. 실제 다운로드8개·설치 Excel XLSX5개 PASS. full 회귀 웹91/Worker16/API231/M4exact36 exit0, 이후 프런트 최종95·타입·빌드와 모바일 Esc 재시험 PASS.

Worker `5a857656-3807-4fb5-84a5-70b6b49517ee`만 배포; private API00014-nah·모든 기존 바인딩·Access·결제OFF 유지. 이번 IA 단위 ENGINEERING_VERIFIED_AWAITING_OWNER, D08 전체 PARTIAL. 일반 고객 범위·견적/공식 PG/영속 상용 운영은 미완료. 상세17항목·실패수정·명령·미실행은 [CORE_FLOW review](delivery-v3_2/reviews/CORE_FLOW.md). 검증 파일만 로컬 커밋하고 정지. 다음 제안 한 단위는 일반 사용자용 지원 범위 → 의뢰 범위·견적 연결이며 자동 실행하지 않는다.

---

## 2026-09-13 — D08 복합 합성 수용시험 완료 / 정지

입력XLSX7·CSV2·독립 예상XLSX/JSON을 추가했다. 베타에서 혼합16건/정상0건, 수정3경로의725셀씩, 비교464그룹·888행, 경계1000그룹·2000행 및 미지원 차단을 실제 확인했다. 다운로드13개·설치Excel8개·출력시각 검토 PASS. 전체회귀78웹/16Worker/231API/36M4 exit0. 고정 합성 등록만 private API00014-nah에 배포; Worker/Access/IAM/결제OFF 보존. 기존83문서/68샘플 hash 보존. 상세 변경·명령·실패·exit·미실행은 [D08 복합 증거](delivery-v3_2/reviews/evidence/D08-complex.json). 이번 단위 ENGINEERING_VERIFIED_AWAITING_OWNER, D08전체 PARTIAL. 다음 부하·중단·재시도 시험은 제안만 하며 자동 실행하지 않는다.

---

## D08 보호 베타 구현·실제 화면 검증 완료 — 2026-09-13

기존 Access 베타에 D02–D08 납품 경로를 반영했다. 이번 후속은 **ENGINEERING_VERIFIED_AWAITING_OWNER**, D08 전체는 **PARTIAL**이다. 공식 PG 계정·키가 준비되지 않았다는 사용자 답변에 따라 실제 결제·일반 구매는 OFF다. 다음 묶음은 실행하지 않고 D08에서 정지한다.

등록된 합성 원본·소유자·정확한 계획/비교 기준·만료에 결합한 시험권만 추가했다. 시험권은 결제·주문·변경 승인을 만들지 않는다. RP01/RP02는 별도의 정확한 변경 승인 뒤 수정본 XLSX·변경내역 XLSX·재검증 HTML을 생성한다. 비교는 수정권 없는 별도 XLSX·HTML이며 B를 정답으로 취급하지 않는다. 기존 계산·보존 패치·승인 기록·무료 위치/근거/CSV/점수·M4 분리와 계층형 결과 UI를 재사용했다.

**실제 베타 예상 값 확인:** M4C03 구조49+수식4=53, M4C01 구조0+수식4 및 G23/G52/H37/I48, 정상 M4C10은 두 검사 완료/0건. RP01 B2=-1,250/B3=7,200/H2=5,950, RP02 F3=2,800/F12=16,890. 비교7그룹·A7/B5행·250/190원·차액20원·중복3행·오류 양쪽2행·전체12행. 선행0 ID/이미 있는 수식/비교기간 불일치도 화면에서 차단 확인했다. 모바일390 RP02·비교와 데스크톱을 실제 확인했다. 최종 문구 재배포에서는 M4C01/정상10과 상품 안내를 다시 확인했다.

실제 다운로드8개와 RP02 동일hash 재수령1개, 설치 Excel16.0/build20326에서 XLSX5개 재개봉·전체 재계산·값/수식/ID/대상 서식/원본hash 확인 PASS. 비대상 ZIP member도 동일하다. 실제 Excel 출력3페이지까지 시각 검토했다. 패키지 계약 모형을 Excel/PG 검증으로 보고하지 않았다.

전체 회귀 웹75·Worker16·API219·M4 exact36 exit0, 이후 화면/네트워크 안내 변경에 대한 최종 웹78·타입·빌드 exit0. 실제 Linux 이미지 기준20개·수정2프로필·산출물6개 PASS. 이미지 확인만으로 트래픽을 넘기지 않았고, 최초9초 시작 실패 후 staging120초에서 전체 검증한 같은 이미지를 일반 시작 모드·원래9초 probe로 다시 확인했다. Docker/WSL 재시작 없이 기존 private Registry에 OCI를 구성했다.

최종 Worker `521ad0aa-55f9-4606-b481-fc4861d8a60f`, Cloud Run `workbookcare-api-beta-00011-bav`, Gateway `workbookcare-beta-d08-e6132fcdf496`. Access 네 경로302·private IAM·R2/KV·HMAC·기존 바인딩 유지. API 임시 저장의 다중 인스턴스 분리를 피하려고 최대1개로 제한했다. 영속 상용 저장이나 동시 처리 성능 보장은 아니다. 보관 만료는 즉시 접근 차단하지만 서버 유휴 시 물리 삭제 지연 가능성을 화면에 명시했다.

한 차례 모바일 업로드 연결 오류는 재시도로 성공했다. 원인은 확정하지 않았고 읽기 쉬운 재시도 안내만 보완했다. 공식 PG/SDK/webhook, 영속 상용 원장, 최대 조합/동시 부하, 원본 patch·정적검사의 별도 hard OS deadline, 가격·세무·법률·지원·M3/M3.5 증거는 여전히 미완료다. 일반 판매·익명 공개·실고객 파일·실결제/환불·새 유료 자원·원격 Git push는 수행하지 않았다. owner 원본83개·샘플68개 hash를 보존했다.

상세 명령·exit·실패/수정·화면·산출물·미실행: `docs/delivery-v3_2/reviews/evidence/D08-hosted.json`. 배포/롤백: `docs/50_BETA_RELEASE_WORKFLOW.md`. 다음 한 단위 제안은 PG 테스트 계정 준비 후 공식 sandbox 결제·조회·취소 검증이며 자동 실행하지 않는다.

---

이하 이전 기록은 당시 상태로 보존합니다. 최신 판정은 위 기록입니다.

# Current progress

## D08 최종 수용시험과 제품별 판정 — 2026-09-13

판정 **PARTIAL · 로컬 구현 검증 완료 / 사용자 확인 대기**. D01–D08 개발 범위의 실제 UI·API·계산·사본 납품을 구현하고 검증했다. 공식 PG, D02 이후 hosted/Linux, 상용 운영 승인은 미완료다. 이 기록 아래의 이전 단계 기록은 당시 이력이며, 현재 판정은 [release_manifest](delivery-v3_2/release_manifest.json)가 기준이다. D08에서 정지하며 다음 묶음은 실행하지 않는다.

승인 기록에 원본·정확한 계획·소유자·상품·권리·만료를 결합한 서버 HMAC 검증을 추가했다. 결제/기준 확인과 변경 승인, 수정 상품과 비교 상품을 분리한다. HMAC는 내부 서버 인증 기록이며 외부 PKI/결제사 증명이 아니다.

새 독립 예상 값은 RP01 B2=-1,250/B3=7,200/H2=5,950, RP02 F3=2,800/F12=16,890이다. 비교는7그룹·A7/B5행·알려진 합250/190원·DIF20원·중복3행·ERR양쪽2행이다. 화면10경로와 최종 안내/레이아웃 재시험6경로에서 대조했다. 실제 다운로드20개·같은hash 재수령4개, 다운로드 XLSX12개와 호환성 XLSX4개를 설치 Excel16.0에서 재개봉했다. 원본/ID·비대상 값·수식·스타일과 비대상ZIP member를 확인했다. 스크린샷51개 저장, 대표24개(실제 Excel 출력3개 포함)를 시각 검토했다.

실제 Excel은 최초 새 샘플의 F3→E3 비정상 순서를 거부했다. 앱이 이를 통과시키던 결함을 수정하여 `UNSUPPORTED_CELL_ORDER`를 사전 차단한다. 실패 V1와 예상 값은 보존하고 셀 순서만 수정한 V2로 재시험했다. 숫자 예상 값을 실행 결과에 맞춰 바꾸지 않았다. 비교5000행 보고서 시간초과/20000행 프로세스 실패를 성공 처리하지 않고, 실제 납품을 확인한1000행으로 서버·표시를 맞췄다. 모든 최대 크기 조합·hosted 동시 부하는 미검증이다.

전체 회귀 **웹75 / Worker16 / API216 / M4 exact36, exit0**. 마지막 화면 문구·여백 변경 후 웹75·타입·build, 새 receipt 접근/변조9개·Ruff, 해당 실제 화면/Excel을 다시 통과했다. 상세 명령·exit·실패/원인수정/재시험·재사용·산출물은 [D08 증거](delivery-v3_2/reviews/evidence/D08-local.json), [negative matrix](delivery-v3_2/reviews/evidence/D08-negative-matrix.json), [Excel](delivery-v3_2/reviews/evidence/D08-excel-reopen.json)에 기록했다. 기존 owner 패키지83개·샘플68개 hash와 진행 기록을 보존했다.

베타는 **D01 Worker91c06632 / API00004-hhk 그대로**다. Docker 읽기 전용12초 확인도 timeout이며, 다른 컨테이너 영향이 있는 재시작 질문에는 응답이 없어 실행하지 않았다. 기존 API 컨테이너의 JDK/POI 포장·Linux 한도와 원본 patch/정적 검사 별도 OS deadline도 후속 배포 단위에 남긴다. “작업당 총3회 시도”는 동시 처리3개 보장이 아니다.

공식 PG sandbox/SDK/외부 webhook, 영속 상용 원장, 가격·세무·법률·지원 결정은 NOT_RUN/PENDING. LOCAL_CONTRACT 계약 모형을 PG 시험으로 보고하지 않았다. M3 관찰/M3.5 구매 증거도 PENDING/DEFERRED다. 원격 push·공개 배포·실고객·실결제·새유료자원은 수행하지 않았다.


## D07 화면·만료·복구·운영 경계 — 2026-09-13

완료 화면에서 파일 수령을 먼저 보여주고 기존 기준·계산 근거는 접었다. 모바일 중첩 여백과 주문 상태를 정리했으며, 비교 0건은 일치한 결과를 설명한다. 주문 목록에서 비교를 이어가고 돌아올 때 키보드 focus를 복구한다. 만료된 계획·입력은 화면에서도 제거하고 새 승인 없이 실행하지 않는다.

보고서 생성·의미 검증을 30초/Windows512MiB 제한 프로세스로 이동했다. 원본·결과15분, 승인 대기 계획10분, 합성 주문24시간을 분리하고 실제30초 백그라운드 삭제를 관측했다. 동시3회 실행 상한, 만료 직전 주문 차단, owner/CSRF/no-store, 파일 하나라도 누락·손상이면 전체 세트 차단과 같은 주문 복구를 검증했다.

전체 웹75/Worker16/API206/M4 exact36, 추가 실제 자동삭제1개, build/Ruff exit0. 실제 화면12경로의 기대값을 대조했고 스크린샷35개를 저장·대표14개를 시각 검토했다. 실제 다운로드 XLSX15개를 Excel에서 재개봉했다. 마지막 무결성 보강 뒤 만료/복구 화면2경로와 해당 Excel을 재시험했다. 상세 명령·재사용·변경·미실행은 [D07 증거](delivery-v3_2/reviews/evidence/D07-local.json).

판정 PARTIAL: 로컬 경계는 검증했으나 Hosted/Linux, 공식 PG, 영속 회계 저장과 법률·가격·지원 결정은 남아 있다. 원본 OOXML patch/정적 검사 자체의 별도 OS deadline과 최대 동시 처리 용량은 미검증이며, 검증한 계산·보고서 프로세스 한도와 구분한다. 보안 경계 및 기존 원본 패키지83·샘플68개 보존. 승인된 D08을 진행한 뒤 멈춘다.


## D06 주문·별도 변경 승인·납품 복구 — 2026-09-13

합성 시험 주문 원장을 입력 보관과 논리적으로 분리하고, 결제·변경 승인·파일 준비·취소 상태를 각각 표시했다. PAID만으로 수정하거나 다운로드하지 않는다. 정확한 일부 대상 재선택은 실제 계산과 새 승인을 요구한다. 같은 주문 재시도/재수령, 동일 원본 복구, 중복·역순 응답, 취소 전 권리 회수와 늦은 게시 차단을 구현했다. OFF 기본값과 TEST 전용 PG 어댑터를 추가했으며 실제 가격은 정하지 않았다.

화면 4경로/11스크린샷에서 RP02 6,000·18,200, RP01 B2 단독 승인 합계12,000 및 B3 보존, 전체거부의 미실행, 비교14행·47,900/51,000원을 확인했다. 실제 8산출물과 동일hash 재수령2건, 설치 Excel 재개봉5건을 검증했다. 표적15개와 전체 웹75/Worker16/API 196/M4 exact36 및 build/Ruff exit0. 명령·재사용·변경·증거는 [D06 증거](delivery-v3_2/reviews/evidence/D06-local.json).

판정 PARTIAL: 로컬 제품 경로는 검증했으나 공식 PG 계정/credentials 및 SDK 인증 연결·외부 webhook 실검증은 NOT_RUN/미연결이다. 계약 모형을 PG 증거로 세지 않았다. Hosted/Linux는 Docker 응답 장애로 미배포다. 재시작은 다른 컨테이너에 영향을 줄 수 있어 별도 질문의 답을 기다리며 수행하지 않았다. 가격/법률/상용 준비와 owner acceptance는 PENDING. 기존 원본 패키지83·샘플68개 보존. 승인된 D07을 계속 진행한다.


## D05 두 자료 비교 실제 구현·화면·Excel 검증 — 2026-09-13

값 기반 두 자료 비교를 별도 상품 경로로 연결했다. CSV/XLSX의 문자 키와 정수 KRW를 정확히 비교하며 중복·자료오류를 보류하고 모든 원천 행을 보존한다. B를 정답으로 취급하거나 원본을 수정하지 않는다. 보고서 XLSX·재검증 HTML 두 파일만 같은 납품으로 게시하며 비교 권리로 수정 API를 실행/다운로드할 수 없다.

기존 baseline과 edge16을 실제 parser/engine에 연결했다. 화면은 전체 요약 → 문제 유형 → 해당 거래 → 원천 위치·값이며 공통 설명은 한 번만 표시한다. 모바일의 가로 표를 세로 근거 카드로 보완했다. CSV/XLSX × 1440/390과 zero/큰 정수 총6경로에서 기대한 8그룹·14행·47,900/51,000원·−2,000원 및 큰 정수 차액1원을 직접 대조했다. 실제 다운로드12개, XLSX6개를 설치된 Excel에서 재개봉해 기대값과 원본 미변경을 확인했다. 재접속도 같은 결과를 표시한다.

전체 회귀 웹75·Worker16·API178·M4 exact36, build/Ruff exit0. 마지막 보고서 내용 검증 강화 뒤 관련9개 시험, 실제6화면/12다운로드/Excel6개를 재검증했다. 보고서 행·요약을 변조하고 hash를 다시 만들어도 차단한다. 실제 변경·재사용·명령·실패/수정·산출물은 [D05 증거](delivery-v3_2/reviews/evidence/D05-local.json).

판정: 로컬 ENGINEERING_VERIFIED_AWAITING_OWNER. Hosted 배포는 Docker 복구 대기이며 PG 검증·상용 판매 준비를 뜻하지 않는다. 사용자 원본 패키지83개와 기존 샘플68개 hash를 보존했다. 최신 D08까지 승인에 따라 다음 D06을 진행한다.


## D04 승인한 사본·세 파일 납품 검증 — 2026-09-13

원본 bytes를 그대로 두고 승인한 셀과 계획된 계산 캐시·설정만 별도 OOXML 사본에 적용한다. 비대상 member hash, 셀·서식·XML 의미, 정확한 patch set, 실제 후계산과 계획 결과를 대조한다. 실제 변경내역 XLSX·재검증 HTML과 수정본을 원본/plan/output hash로 결합한다.

현재 계획·소유자·수정 SKU·내부 합성 권리를 별도로 확인한 뒤 명시 승인을 받는다. 확인함/결제만으로 실행하지 않는다. 세 파일과 READY는 SQLite에서 원자적으로 게시하며, 누락·검증 실패는 격리한다. 중복 실행은 같은 논리 납품을 재사용하고 취소는 publication fence와 실제 child kill/cleanup 후 완료된다.

전체 웹75·Worker15·API151·M4 exact36, Ruff/build exit0. 마지막 보고서 표시/열 폭 보완 뒤 관련22개 시험과 실제 UI4개를 다시 통과했다. RP01 H2=15,500, RP02 F3=6,000/F12=18,200을 데스크톱1440·모바일390 화면에서 확인하고 세 파일씩12개를 실제 다운로드했다. 그중 XLSX8개를 설치된 Excel에서 읽기 전용 재개봉해 값/수식·식별자 보존을 확인했다. 화면12장과 Excel-rendered 보고서1장 검토.

판정: 로컬 `ENGINEERING_VERIFIED_AWAITING_OWNER`. **D02–D04 hosted 배포/화면과 Linux 컨테이너 검증은 Docker 복구 대기**. 실제 PG·고객 권리·상용 납품 가능 판정이 아니다. 내부 합성 검증권은 hosted/production에서 인정하지 않는다.
실제 변경·재사용·실패 수정·명령/exit·산출물·미실행은 [D04 증거](delivery-v3_2/reviews/evidence/D04-local.json), [Excel 대조](delivery-v3_2/reviews/evidence/D04-excel-reopen.json).
최신 D08까지 승인에 따라 다음 D05로 진행한다.


## D03 실제 계산·불변 계획·화면 검증 — 2026-09-13

Apache POI 5.5.1 계산 adapter를 제한된 JDK17 프로세스에서 실행한다. 원본 XLSX 대신 검증한 typed snapshot을 전달하며 원본 저장/캐시 사용은 하지 않는다.
지원 수식 조합/참조/깊이/전체 coverage, RP01 타입변환, RP02 절대·상대·혼합/불연속 정확 번역을 구현했다.
원본·소유자·정책·엔진/템플릿·exact patch·계산 영향·캐시/계산 설정 보조 변경·만료를 plan digest로 고정한다.
무료 projection은 범위 요약이다. 정확 상세는 권리 검사를 요구하며 내부 합성 fixture 권리는 local CLI만 발급하고 hosted/production에서는 인정하지 않는다.

고정 수학/정책 oracle 20개 사례 25개 typed 결과를 설치된 Excel과 실제 POI 실행으로 대조: 일치.
표적31개, 전체 웹75·Worker15·API129·M4 exact36, Ruff/build exit0. 강제 timeout 뒤 프로세스 종료/임시 경로 삭제, Windows 512MiB 메모리 제한, 네트워크/외부파일/실행/쓰기 거부를 실제 확인했다.
실제 local desktop/mobile 7개 UI 시나리오: RP01 0→15,500, subset 0→12,000, RP02 F3=6,000/F12 12,200→18,200, 미검증 조합은 성공 0으로 표시하지 않는다.
직접 변경값은 한 번, 복원 수식과 계산 결과는 같은 셀에, downstream 영향은 별도 표시한다. 스크린샷5장 검토.

로컬 개발 판정 `ENGINEERING_VERIFIED_AWAITING_OWNER`. **hosted D02/D03 배포, Linux 컨테이너 실행은 Docker 엔진 무응답으로 미실행**.
계산 프로필 검증은 상용 판매·납품·PG 검증이 아니다. 현재 구매/실행 false, D04 산출물은 아직 만들지 않았다.
실패 수정·명령·exit·화면·미실행은 [D03 증거](delivery-v3_2/reviews/evidence/D03-local.json), 실제 Excel 결과는 [reference](delivery-v3_2/reviews/evidence/D03-excel-reference.json).
최신 D08까지 승인에 따라 다음 D04로 진행하고 배포 대기는 계속 보존한다.


## D02 구현·로컬 화면 검증 — 2026-09-13

실제 원본 고정/소유자/버전 API와 사전 검사 UI를 구현했다. 기존 OOXML 보호·Access/HMAC·R2·무료/M4를 재사용한다.
RP01 금액·수량만 허용하고 ID/선행 0/단위/소수/초과 정밀도를 거부한다. RP02는 정확한 기준 수식과 실제 빈 target을 요구한다.
원본 hash/inventory를 고정하고 교체/타소유자/동시 이전 버전/만료를 거부한다. 원본 overwrite API는 없다.
실제 desktop/mobile 10개 화면 시나리오에서 RP01 2건, RP02 1건과 제외 0건을 확인했고 캡처4장을 검토했다.
전체 회귀 웹75·Worker15·API98·M4 exact36 및 Ruff/build exit0. 최종 공통 설명 정리 후 실제 화면10개 재시험 exit0.

`ENGINEERING_VERIFIED_AWAITING_OWNER`는 D02 로컬 개발 판정이다. 계산이 없으므로 PRELIMINARY_ONLY, 견적/구매/실행 false.
SQLite는 beta local adapter이며 15분 만료/서버 재시작 시 소실 가능; 상용 durable 저장소 증거가 아니다.
**D02 베타 배포와 실제 hosted 화면은 Docker 엔진 무응답으로 아직 미실행**이다. 재시작 승인을 요청했으며 기존 베타는 D01 그대로다.
자세한 실제 명령·실패 수정·검증·미실행: [D02 로컬 증거](delivery-v3_2/reviews/evidence/D02-local.json).
최신 D08까지 개발 승인에 따라 로컬 화면 검증을 통과한 D02 다음으로 D03을 진행하되, 배포 미실행을 완료로 바꾸지 않는다.


## D01 hierarchy verified — 2026-09-13

최신 승인에 따라 전체 요약 → 유형별 공통 설명 → 필요한 셀의 위치·차이로 화면을 정리했다.
같은 제목/설명을 반복하지 않으며 실제 동일한 설명만 유형에 한 번 올린다. 서로 다른 근거는 셀에 남긴다.
추가 기준·검사 한계, 점수 상세, 직접 재검사·참고 견적은 펼쳐 확인한다. 기존 무료 CSV/점수/견적/상태 키·M4 의미는 유지된다.
표적12개, 전체 회귀 웹75·Worker14·API77, TypeScript/build/Ruff exit0. 실제 로컬 desktop20/mobile4에서72 exact,
그룹/셀/표/필터/확인함/CSV 불변과 캡처6장 직접 검토. 실제 로그인 베타03·01·20도 53/4/0건 및8개 exact 위치 일치.
소스 `2c0b4d1a6b1f`, Worker `91c06632-1302-4877-ae49-d4e44af3f3a2`100%; 기존13바인딩/Access 유지, API·Gateway 변경 없음.
명령·실패원인수정·재시험·화면·미실행은 [D01 계층 증거](delivery-v3_2/reviews/evidence/D01-hierarchy.json)에 기록했다.
소유자 패키지83개 보존. 고객 원본 수정·Excel/PG 검증은 이 UI 보완의 증거가 아니다.
이전 D01-only/정지 기록은 이력이다. **최신 사용자가 D08까지 개발과 단계별 실제 화면 검증을 승인했으므로 D02로 진행한다.**
사용자 최종 검토는 요청대로 D08 뒤에 받으며 상용 공개/실결제 승인을 추정하지 않는다.


## Unified diagnosis UX completed — 2026-09-13 (KST)

Owner-approved D01 single upload/progress/list implemented and deployed to protected beta.
Combined UI: case03=53 (49 structure+4 formula),11=63,01=4,controls10/20=0.
Source categories, groups/full table/filters/keyboard/mobile/handling preserved; base score/quote/CSV/revalidation unchanged.
Final verify.ps1 exit0: web73/Worker14/API77, TypeScript/build/Ruff/main pack36.
Actual local desktop20/mobile4:72 exact,6 screenshots visually reviewed; actual authenticated hosted representative5:12 exact.
Prior all20 hosted/container72 evidence reused, not claimed rerun. Existing strict2 label conflicts/waiver unchanged.
Source `d64c45178cf1`; Worker `f9be71f3-d035-48cb-b9a9-7fcaa1e7469a`100%; all13 bindings/Access unchanged; no API/Gateway rollout.
Owner83/sample68 hashes unchanged. No Excel/PG/repair delivery,paid resource,remote push,H2/H3 completion or D02 execution.
D01 ENGINEERING_VERIFIED_AWAITING_OWNER: engineering acceptance done, final owner acceptance pending. Stop after D01.
See `delivery-v3_2/reviews/D01.md` and `delivery-v3_2/reviews/evidence/D01-unified-diagnosis.json`. Prior records preserved below.

## Protected beta M4 follow-up completed — 2026-09-12

The approved expected-results connection is deployed and agent-verified on the actual authenticated beta:
20 unique synthetic uploads,72/72 exact sheet/cell/rule/subtype,no extras; controls10/20 zero.
Free counts03=49/11=59/others0, grouped locations,score/CSV and approval separation are preserved.
Existing engine reused; automatic separate M4, gated API/Worker/Gateway connection and mobile layout repaired.
Final full regression exit0:web69/Worker14/API77,TypeScript/build/Ruff; actual container72 and local UI72 pass.
Strict evaluator remains BLOCKED solely by existing case18 E13/F22 target/normal label conflicts; existing waiver accepted,
no fixture/threshold/waiver edits. Source `0ae6c63c06a7`. Worker `c222ac45-36ab-48c0-a0b1-e0d66f4755d8`,
Cloud Run `workbookcare-api-beta-00004-hhk`, Gateway `workbookcare-beta-m4-0ae6c63c06a7`; Access/IAM/private storage preserved.
Evidence: `delivery-v3_2/reviews/evidence/D01-m4-hosted.json` and `D01-m4-hosted-browser.json`.
Owner83/sample68 hashes unchanged. No Excel/PG/repair delivery,paid resource,remote push,H2/H3 completion or D02 execution.
D01 engineering verified,owner acceptance pending; stop here. Earlier M4-disabled/pending notes are historical.

## D01 authenticated hosted sample verification — 2026-09-12

The connected, logged-in Chrome beta was exercised by the agent using actual
synthetic uploads: all 20 unique Workbook samples plus demo, 21/21 free results
matching local counts and scanned-cell/formula metadata. Case03: 49 deep-nesting
findings, one collapsed group; case11: 59 volatile-function findings, one collapsed
group. All 49/59 locations are retained; case11 full table retains 59 rows. The other
18 samples return free0; demo returns12. Zero screens clearly show M4 not performed.
The supplied M4 expected72 are NOT verified on the hosted site: hosted M4 remains
unavailable/disabled. This is a product-scope/connection gap, not evidence that the
M4 expected findings passed. Browser setup does not approve M4 activation.
No source/deployment/gate changes; prior full regression web63/Worker13/API75 is
reused, not rerun. Owner83 hashes and tracked samples preserved. Actual browser
actions, results, recovered chooser failure and limits are recorded in
`delivery-v3_2/reviews/evidence/D01-hosted-browser.json`. Earlier pending-browser
notes below are historical. D01 owner acceptance, H2/H3 readiness and D02 gate stay unchanged.

## D01 owner-feedback grouping fix — 2026-09-12

Owner confirmed beta case03 free count 49, matching local API. Same-rule grouping
was incomplete: all leaf cards were always shown and titles repeated. Now each
rule has one summary and a collapsed location disclosure; individual evidence,
handling, filters, full table/CSV and risk remain intact. Source `5828aca`.
RED2 -> corrected implementation/legacy expectations -> targeted19 -> full
web63/Worker13/API75, build/Ruff/M4 sample36 (exit0). Actual local API/Chrome
1440/390: case03 49/one group, case11 59/one group, controls12/0, all locations,
CSV invariance, keyboard/focus and no overflow verified; four captures reviewed.
All Workbook packs also rerun: 20 unique files, M4 72/72 exact, same accepted
two-label-conflict waiver; 61 local API requests passed. Source fixtures intact.
Beta version `673f2895-2142-4215-8024-9acb14fa53ae` at 100%; rollback
`dc94d91a-e969-479e-9087-f1f9758ec2ef`. All12 bindings/Access preserved.
No Cloud Run/Gateway change, M4 activation, remote push or next bundle. Post-fix
authenticated hosted UI remains owner review, distinct from local/browser and
deployed-version evidence. Original owner package83 files and prior records
preserved. Evidence: `delivery-v3_2/reviews/evidence/D01-grouped-findings.json` and
`D01-workbook-packs.json`. D01 acceptance pending; stop, D02 recommendation only.

## D01 feedback follow-up — 2026-09-12

The owner used existing M4 formula-pattern test files. Current beta free scanning
does not execute the separate M4 audit. Actual local controls: 9/10 M4 files had
zero free findings, one had 49, internal M4 had 36 candidates; free positive control
had 12. The authenticated hosted all-files-zero report remains unverified.
Clarified zero/partial/empty states, scanned cell/formula counts and excluded M4
checks without changing scanner/CSV/risk/API/gates. Source `207e09c`.
Full regression: web 61 / Worker 13 / API 75, build/Ruff/M4-C 36 exact. Actual local
browser/API controls and reviewed desktop/mobile captures passed. Final targeted
17 tests and hosted build passed after correcting legacy negative assertions.
Beta version `dc94d91a-e969-479e-9087-f1f9758ec2ef` deployed 100%; bindings/Access preserved.
Evidence: `delivery-v3_2/reviews/evidence/D01-zero-findings.json`.
No hosted M4 exposure, Cloud Run change, authenticated beta scan, Git push or D02.

## D01 protected beta deployment — 2026-09-12

The owner subsequently approved this deployment and continued deployment of
verified, separately approved work to the existing beta. D01 web assets from
source `40e2e89` are now deployed at
https://workbookcare-beta.wonderlogic-studio.workers.dev/ .
Active Worker version: `9748b413-0acd-4a57-a0fd-9a5e3324f3db` (100%).
Prior rollback version: `762582e4-2d79-4e8b-be38-b5add1add5c2`.
Web 59 / Worker 13 and hosted-beta TypeScript/build passed (exit 0); the unchanged
API's prior D01 local 75 tests/M4-C evidence is reused, not claimed rerun here.
Version upload dry-run, upload, deployment and provider recheck exited 0.
All 12 binding descriptors/values fingerprints remained identical. Root, scan
and Formula Audit paths returned the existing Access 302 before and after.
No Access/route/IAM/R2/KV policy, Cloud Run/Gateway revision, feature gate, or
remote Git change. D01's additive API product/count projection remains local;
the deployed frontend uses its generated catalog and existing summary fields
with older API responses. No cloud scan upload or authenticated UI result is claimed.
The URL-scoped browser tool reported no browser available. Owner checks now use
the beta URL; local D01 product/browser evidence remains separately recorded.
Actual commands/exit codes and asset hashes: `delivery-v3_2/reviews/evidence/D01-beta-release.json`.
D01 owner acceptance and H2/H3 readiness remain unchanged. Stop; do not start D02.

## V3.2 D01 — 2026-09-12

**ENGINEERING_VERIFIED_AWAITING_OWNER.** Product/deliverable boundaries are connected
to the existing catalog/API/UI; absent comparison/repair engines stay PLANNED and
non-purchasable. Reused free diagnosis, P1 filters and P2 comparisons now have
group/table views, complete count distinctions, CSV formula interpretation defense,
and incomplete-comparison wording. Group review remains personal handling only.
M4/H3 guards, old records and source workbook bytes are preserved; no live ops.

Final verification: web 59 / Worker 13 / API 75, TypeScript/build, Ruff, M4-C supplied
pack 36 exact/no extras. Actual local Chrome + API, synthetic 150/120/30 result,
1440/390 keyboard/mobile and final screenshots passed. A mobile caption layout
defect was found in visual review and fixed. Existing M3 fixture planned activity
wording was synchronized without changing detection/IDs/time/risk/prices.

Local source commit: `40e2e8998beef87cb844c1fc400f1e75eced2fa1`. Full delta and owner actions:
`delivery-v3_2/reviews/D01.md`, `delivery-v3_2/owner_action.md`, `delivery-v3_2/delivery-progress.json`.
No actual repair/delivery, Excel reference/calculation, PG/payment/refund, real
customers, pricing approval, cloud changes, push or deployment was performed.
D01 only; D02 recommendation does not authorize execution. Prior records follow.

## Current product work — 2026-09-12

**Product P2 — Re-validation location details: IMPLEMENTED / VISUAL REVIEW PENDING.**
The owner's renewed product-only instruction selected the existing comparison
workflow. Startup confirmed local/remote `main` at `47e5e54` (after the supplied
`4faae1b`). Untracked `docs/delivery-v3_2/` was left untouched and excluded.

Each comparison group now offers an expandable complete title/rule/location
list. Removed entries use previous locations; continuing/new entries use current
locations. Missing location scope, empty groups, version/truncation warnings and
rename/move/calculation limits are explicit. P1 filters and full CSV remain
independent; no comparison algorithm, scanner/API/Worker/infra/feature gate,
storage, feedback, dependency or cloud change. Scope: `docs/49`.

Baseline `scripts/verify.ps1`: web 36, Worker 13, API 72. After implementation:
web 43, Worker 13, API 72, TypeScript/production build, Ruff and 36 exact M4-C
supplied-pack candidates with no extras. Seven additional behavior tests include
the same-session sample loop, all groups/location scope, warnings, P1 filter/CSV
independence and disclosure reset. The existing Starlette/httpx warning remains.

Real desktop/mobile verification is pending: the browser connector was
unavailable; Windows computer-use then stopped because it could not determine
the current browser URL with enough confidence to enforce policy. No fallback
UI automation, screenshot, or visual acceptance is claimed. P1's visual review
also remains pending. See `MILESTONE_REVIEW.md` for the local synthetic checklist.
H2/H3 operations and Hosted Beta NOT READY remain unchanged. No cloud resources
were inspected and no deployment, real workbook or external session was run.

## Previous product work — 2026-09-10

**Product P1 — Free-result navigation: IMPLEMENTED / VISUAL REVIEW PENDING.** The owner requested product
development only, followed by full regression verification, commit, and GitHub
synchronization. The selected scope adds browser-memory filters for severity,
sheet, and local handling status to the existing free findings. See `docs/48`.
Read-only startup confirmed a clean `main` and local/remote commit `4faae1b`.
Baseline `scripts/verify.ps1` passed: web 30, Worker 13, API 72, TypeScript and
production build, Ruff, and 36 exact M4-C supplied-pack candidates with no extras.
One pre-existing Starlette/httpx deprecation warning remains.

Implemented severity/sheet/status filters, visible match counts, reset, and a
priority shortcut. Workbook-level findings remain selectable. Empty filters do
not imply a clean scan. Status edits update the filtered list and preserve focus;
new scans reset filters. Summary, quote, CSV, and local statuses remain intact.
Post-change `scripts/verify.ps1` passed: web 36 (six new behavior regressions),
Worker 13, API 72, TypeScript/build, Ruff, and 36 exact supplied-pack candidates
with no extras. All test inputs are synthetic. No browser is connected to the
computer-use runtime (`apps: []`, `browsers: []`), so desktop/mobile visual review
and screenshots remain pending. See `MILESTONE_REVIEW.md` for the review package.

No H2/H3 verification or deployment is resumed in this product task. Operational
evidence and open gates below are retained; P1 does not authorize Hosted Beta
Ready, external participants, or real workbook processing.

## Separate operational status — 2026-09-09

**Hosted Beta H3 is approved and in progress.** H3 prepares the already deployed,
synthetic-only beta for a later product-owner decision about invitations. It does
not invite participants or permit real workbooks. H2 remains a dependency: the
one-day R2 lifecycle probe still needs an observed expiration. The owner-session
HMAC-negative check passed and its temporary route has been removed. H3 cannot
be marked Hosted Beta Ready while the lifecycle gate remains open.
The scoped plan and engineering additions are in
`docs/44_HOSTED_BETA_H3_OPERATIONAL_HARDENING.md`.

H3 implementation now has content-free telemetry buckets, a strict
category-only feedback Worker contract, a hosted browser client that sends only
four allowlisted fields, and draft privacy/terms UI pages. The account owner has
now created the required private Cloudflare KV namespace after the original
Wrangler API authentication error `10000`; Worker version
`e5aee49a-47b2-4a8e-b265-7de17fc27ac5` deployed its protected binding. A
tokenless read-only header check was redirected to Cloudflare Access. An
authenticated synthetic persistence verification remains open, and Formula Audit
is still not publicly exposed. The inventory, safe-error taxonomy, and
synthetic/rollback checklist are `docs/45` through `47`; the current Go/No-Go is
`HOSTED BETA NOT READY`.

Read-only provider recheck at 2026-09-09 14:05 UTC reconfirmed Cloud Run max two,
concurrency one, CPU one, 1 GiB, timeout 60 seconds, an ACTIVE Gateway, and no
public Cloud Run IAM member. Full local regression passed again: web 30, Worker
13, API 72, production build, Ruff, and the supplied M4-C package. The R2
lifecycle probe is not eligible for observation until 2026-09-10 12:37:58 UTC
(2026-09-10 21:37:58 KST), so it remains correctly open rather than inferred.
The H2 temporary no-HMAC route initially rendered the SPA because static assets
were served first. Selective Worker-first `/api/*` routing enabled an
owner-session result of `HMAC_NEGATIVE_CONFIRMED`; the route and its dedicated
test were removed in Worker version `762582e4-2d79-4e8b-be38-b5add1add5c2`.
The H3 safe-telemetry/error backend is now live in Cloud Run revision
`workbookcare-api-beta-00003-bsp` from immutable image
`sha256:5ab7065c318c2325f6124b41787e8297f4de6f428329151b6a1ca45c7cf35703`.
Its existing guardrails were preserved, and a direct unauthenticated health
request returned `403`.

## Historical current override — 2026-09-09

**Hosted Beta H2 is approved and in progress.** This section supersedes the
earlier H1-only stop record below. The product owner created the private
`workbookcare-beta-uploads` R2 bucket with a one-day deletion lifecycle, the
Access-protected `workbookcare-beta` Worker with its `UPLOADS` R2 binding, enabled
Google API Gateway, and granted only
`workbookcare-gateway-invoker@workbookcare-beta.iam.gserviceaccount.com` the Cloud
Run Invoker role on the existing IAM-required `workbookcare-api-beta` service.

Tokyo API Gateway (`asia-northeast1`) is explicitly approved to reach the existing
Seoul Cloud Run service (`asia-northeast3`). The cross-region bridge is
synthetic-only until H2 completes. Provider secrets, the same Cloud Run service's
H2 revision, Gateway, and Worker assets/control route are now deployed. A browser
upload returned 404 because Gateway discarded `/v1/scans`; the routing correction
is now deployed on the ACTIVE Gateway. An authenticated browser synthetic upload
then completed with a 200 scan result and the R2 bucket returned to zero objects.
A deliberately malformed synthetic `.xlsx` then reached the same Cloud Run route,
returned 415, and R2 again returned to zero objects. This proves normal and
malformed terminal-path cleanup, but not every H2 live gate. The deployed Worker
now limits each authenticated Access assertion to five upload attempts per minute;
tests prove both over-limit files and rate-limited attempts stop before R2.
The product owner reports browser CSV download success and completed synthetic
browser re-validation; the comparison summary changed from `3/3` to `2/1`.
The active project budget is KRW 10,000 with 50%, 90%, and 100% alerts. The
direct-Gateway HMAC-negative gate is evidenced and its temporary route is
removed; only observed lifecycle-expiry evidence remains open.
A private synthetic lifecycle probe was remotely written and read back at
2026-09-09 12:37 UTC without emitting its key or contents; it is awaiting the
configured one-day expiration. No invitations, real workbook use, repair, payment,
hosted Formula Audit, AI, M5, or H3 work has started.

Current local H2 evidence: standard verification passed with web 26 tests and
production build, Worker 7 tests, API 70 tests, Ruff, and the M4-C supplied pack.
M4 release verification passed under its existing narrow fixture waiver (72/72
locations and top-level rules); M4-A.5 remains `CONDITIONAL_GO`. A freshly built
local H2 container passed synthetic signed-upload, error, health, non-root, and
temporary-file cleanup rehearsals. New regression tests reproduce the original
Gateway 404 and pass with path preservation, including unsigned-call denial and
Worker cleanup on backend 404/network failure. Local tests do not prove the live
end-to-end flow or R2 lifecycle. Deployment evidence is recorded in
`42_HOSTED_BETA_H2_PREFLIGHT.md`.

## Current step — 2026-09-09

**Cloud Run preparation completed; deployment stopped.** The owner's 2026-09-08
instruction supersedes the broader H2 execution scope for this step. Container
runtime logging is content-free, build context is restricted, and multipart spool
cleanup is verified. Docker rehearsals passed on 8080/9091 and forced 500; web 23,
API 65, build/Ruff, supplied M4-C pack and complete M4 RC verification passed with
the existing fixture waiver. M4-A.5 remains CONDITIONAL_GO. No cloud resources,
image push, frontend deployment, Cloudflare/R2, signup/payment/repair, or scanner
behavior changes. Details: `43_CLOUD_RUN_PREPARATION.md` and `MILESTONE_REVIEW.md`.
Earlier H2 status below is historical; do not resume deployment automatically.


## Completed

- [x] Market and competitor research.
- [x] Product positioning and value proposition.
- [x] Milestone-controlled Codex operating model.
- [x] Responsive React conversion prototype.
- [x] Sample diagnosis and quote-preview flow.
- [x] FastAPI static workbook scan endpoint.
- [x] OOXML ZIP safety checks.
- [x] Deterministic initial diagnostic rules.
- [x] Risk score, complexity band, and quote preview.
- [x] Backend automated test suite (12 passing tests in supplied environment).
- [x] Frontend test specifications, TS/TSX syntax verification, and offline visual QA.
- [x] Cloudflare/Cloud Run target design.
- [x] Korean start guide, revenue experiments, and user-test playbook.
- [x] M2.5 service-scope result UX, evidence grades, and four repairability summaries.
- [x] Scanner-generated frontend sample fixture with scanner/fixture consistency test.
- [x] Separate recommendation engine and planned-service catalog with beta price ranges.
- [x] Repair-readiness path derived from existing finding classifications, with planned approval-based repair and re-validation stages.
- [x] M2.5 Extension: rule-based Action Category and direct Excel-check guidance for every current static rule.
- [x] M2.5 Extension: value-free finding keys, same-session manual re-validation comparison, and local handling status.
- [x] M2.5 Extension: browser-generated UTF-8 BOM CSV result download.
- [x] M2.5 UI navigation correction: sticky-header-safe anchor and CTA scrolling on desktop and mobile.
- [x] M2.5 navigation and full-screen section alignment: five exact menu destinations, distinct planned-service pages, and desktop section boundaries.
- [x] M2.5 progressive Finding disclosure: one compact complete list with per-Finding expandable evidence and controls.
- [x] M3-A preparation baseline: verified M2.5, staged 8-person qualitative protocol, de-identified observation forms, and scanner-backed synthetic scenarios.
- [x] M4-A Formula Pattern Audit Prototype + Feedback Capture Readiness (internal, default-off prototype only).
- [x] M4-A.5 Formula Audit Quality Gate (synthetic-only; CONDITIONAL GO operating limit recorded).
- [x] M4 Planning Detection Coverage Blueprint (documentation-only; 14 coverage layers, candidate catalog, release gates, and recommended—not approved—next batch).
- [x] M4-A.6 Detection Coverage Blueprint & M4-B Contract (documentation and readiness review).
- [x] M4-B Formula Pattern Audit Internal Beta code and automated verification (separate optional audit API/UI; default-off and server-gated).
- [x] M4-C Formula Pattern Coverage Extension (value-free literal-category normalization, reference subtype correction, and exact 36-target/36-normal synthetic practical corpus gate).
- [x] M4-C quality remediation (summary-marker handling for formulas that reference a `총계` worksheet, synthetic Holdout recovery, and source-fixture ambiguity recorded).
- [x] M4-C final baseline closure: 72/72 engine contract accepted with the explicit, narrow product-owner fixture waiver `M4C-2026-09-02-source-label-conflict`; source labels remain unchanged.
- [x] M4-D Formula Audit Release Candidate & Hosted Beta Readiness: `m4-formula-audit-rc1`, configurable audit limits, safe no-partial-result states, memo-free category feedback, release verification command, support/failure/hosted-beta/manual-review documents.
- [x] Hosted Beta H1 Deployment Foundation & Security Boundary: strict hosted environment/CORS contract, non-root API container, safe liveness/readiness/error/logging contracts, same-origin hosted-beta configuration, deployment/lifecycle/runbook documents, local container rehearsal, and regression verification. No cloud deployment or user upload.
- [ ] Hosted Beta H2 Cloud Deployment, Private Upload Pipeline & Analysis Execution (deployed, synthetic-only; upload routing corrected, final live verification remains open; no external invitation).

## Current product state

A local user can open the website, run a sample diagnosis, or upload a supported workbook to the local API and receive a static diagnostic result. The result clearly distinguishes confirmed facts, possible impacts, Excel manual checks, normal conditions, action recommendations, unchecked scope, and recommended precision checks. A user can mark local handling status, directly edit a test workbook, re-scan it with the same rules in the current browser session, compare the two results, and download the current result as CSV. It shows only rules-based risk labels and beta price hypotheses; no customer data should be used during development.

M4-B/M4-C keep the two formula-pattern candidate classes default-off and internal-only. When both server gates and the separate browser visibility flag are enabled in a development/internal-beta environment, a user can explicitly re-send the same in-browser file to `POST /v1/formula-audits`. The response is a separate `FormulaAuditResult`; its candidates never enter the basic finding list, risk score, quote, repairability totals, or CSV. M4-C compares supported numeric/text/logical/error literal categories without exposing their values and adds a value-free fixed-reference subtype; unsupported structures remain fail-closed. In internal-beta mode only, the separate audit panel appears before the potentially long free Finding list so a user cannot mistake free-scan counts for formula-audit candidates. `scripts/dev.ps1 -InternalFormulaAudit` enables the required API/browser gates together on an automatically selected isolated port pair from `8010–8090` and `5174–5190`, so an old default stack on `8000` / `5173` cannot intercept the test.

## Not implemented

- Browser-only scan.
- Production R2 upload.
- Database/state machine.
- Real pricing validation.
- Repair engine.
- Payment.
- Authentication.
- Expert workflow.
- Production legal/privacy pages.
- Production deployment.
- Actual user-understanding / conversion-intent sessions and their results (M3 Round 1/2, deferred until hosted beta).
- Hosted paid-value validation (M3.5, deferred until hosted beta).

## Current blocker

M4 is complete as a local Release Candidate, not a hosted release. The combined evaluator confirms 72/72 locations, rules, and subtypes with no unexpected candidates, no non-target normal-range candidates, no clean-control findings, no scan failures, no base-result regressions, and no raw formula/value output fields. The additional pack still contains two target/normal overlaps, accepted only by the documented product-owner fixture waiver; a corrected upstream pack remains recommended. The existing M4-B desktop/mobile capture is a hosted-beta manual gate because this environment has no controllable browser runtime. M3 remains internal-review complete with external validation deferred until hosted beta. No external response, PASS decision, market validation, or paid-value result has been collected or inferred. Actual hosting, automatic repair, payment, calculation, new rule codes, and M5 require separate approval.

## Verification status

Completed locally for the M2.5 Extension on 2026-08-31:

- `scripts/verify.ps1`: frontend Vitest 13 passed and Vite production build passed; API pytest 18 passed and Ruff passed.
- `samples/demo-risky-workbook.xlsx` scanner output regenerated into the frontend JSON fixture and checked by API regression test.
- Component tests cover 0, 1, 2, and 3+ findings, `scan_truncated`, information-only-only, all findings display, local user status, and mixed repairability classes.
- Re-validation tests cover no-longer-detected, continuing, newly-detected, duplicate finding keys, scanner/rule-set mismatch, and truncated comparison warnings. CSV tests check UTF-8 BOM and requested fields.
- Navigation and viewport alignment: the header has five named destinations that each contain a matching title; `진단 시작` and page CTAs move to the upload card. Frontend Vitest 15 passed and the Vite production build passed.
- Progressive Finding disclosure: frontend Vitest 16 passed and Vite production build passed. Tests cover one complete, initially closed Finding list and user expansion.

Manual visual screenshots could not be captured in this environment because no controllable browser runtime was available. Required manual review after starting `scripts/dev.ps1`:

- Visit `http://localhost:5173`, run the sample result at desktop and mobile widths, and verify scope → summary → next actions → findings → re-validation → CSV order.
- Upload only `samples/demo-risky-workbook.xlsx` to the local API and compare it with the generated fixture when intentionally refreshing it.

M3-A preparation on 2026-09-01:

- `scripts/verify.ps1` passed before and after preparation. Final result: frontend Vitest 16, Vite production build, API pytest 20 (including 2 M3 fixture checks), and Ruff. The test runner emitted pre-existing `act(...)` and ZipFile resource warnings but no failed checks.
- `samples/m3/low-or-zero-findings.xlsx` is a reproducible 0-Finding, low-risk synthetic scenario.
- `samples/m3/revalidation-before.xlsx` and `revalidation-after.xlsx` create actual removed, continuing, and new rule signals; their JSON fixtures are regenerated by `scripts/generate_m3_test_scenarios.py` and asserted against a fresh scanner run.
- No participant session, UI change, tracking, payment, repair, or new scanner rule was performed.

M4-A verification on 2026-09-01:

- `scripts/verify.ps1`: frontend Vitest 19 passed, Vite production build passed, API pytest 25 passed, Ruff passed.
- Pattern tests cover function/reference/relative/range pattern outliers; constant and blank gaps; boundaries, summary rows, blank dividers, merged cells, Excel Tables, default-off behavior, truncated scans, stable keys, and value-free evidence.
- Feedback tests cover local-only allowlisted fields, memo limit, clear action, and the disabled-by-default Results UI.
- Existing `act(...)`, Starlette `TestClient`, and ZipFile cleanup warnings remain non-failing known test-environment warnings.

M4-A.5 verification on 2026-09-01:

- `samples/m4-evaluation/` contains reproducible synthetic target, normal-exception, unsupported, truncated, and 1k/10k/30k formula performance assets; `manifest.json` has 40 fixed expectation labels.
- `scripts/evaluate_formula_patterns.py --performance-runs 3`: 24 TP, 0 FP, 0 FN; precision/recall/F1 1.00; normal exceptions, unsupported syntax, truncated scans, key stability, and value-free evidence all passed on this synthetic corpus.
- The same timing run measured M4-to-baseline ratios of 2.545×, 2.510×, and 2.198×. This exceeds the 2× relative-review threshold, so the M4-A.5 recommendation is `CONDITIONAL GO`, not automatic M4-B approval.
- `scripts/verify.ps1` after the changes: frontend Vitest 19 and Vite production build passed; API pytest 27 and Ruff passed. React act and ZipFile cleanup warnings were corrected; Starlette TestClient deprecation remains documented for dependency follow-up.

M4 Planning verification on 2026-09-01:

- `scripts/verify.ps1` baseline passed before documentation work: frontend Vitest 19, Vite production build, API pytest 27, and Ruff. The only warning remains the documented Starlette TestClient deprecation.
- `scripts/evaluate_formula_patterns.py --performance-runs 3` was re-run against the actual scanner: precision 1.00, recall 1.00, decision `CONDITIONAL_GO`. This confirms the existing M4-A.5 result; it does not approve M4-B because the documented relative performance review remains unresolved.
- `docs/26_DETECTION_COVERAGE_BLUEPRINT.md` and `docs/27_DETECTION_RULE_CATALOG.md` add documentation only. No scanner, API, frontend, fixture, configuration, or sample workbook changed; M4 remains default-off and internal-only.

M4-A.6 verification on 2026-09-01:

- `scripts/evaluate_formula_patterns.py --performance-runs 3` passed after the documentation work: precision 1.00, recall 1.00, decision `CONDITIONAL_GO`. It reconfirms the existing synthetic-only M4-A.5 result.
- `scripts/verify.ps1` passed after the documentation work: frontend Vitest 19, Vite production build, API pytest 27, and Ruff. The only warning remains the documented Starlette TestClient deprecation.
- The final M4-A.6 documents only amend product/readiness contracts; no scanner, API, frontend, fixture, configuration, sample workbook, or feature flag changed.
- `docs/28_M4B_PRODUCT_CONTRACT.md` records the required future separation of M4 candidates from baseline findings, risk, quote, repair counts, and default results. `docs/29_M4B_MANUAL_REVIEW_CHECKLIST.md` is intentionally blank and synthetic-only.

M4-B verification on 2026-09-01:

- `scripts/verify.ps1`: frontend Vitest 22 passed, Vite production build passed; API pytest 30 passed and Ruff passed. The only warning is the existing Starlette `TestClient` deprecation.
- API regression tests prove that enabling the internal gate leaves the base finding list, workbook summary, risk score, quote, and limitations unchanged before and after `POST /v1/formula-audits`; M4 candidates are absent from the base list. Failure, unsupported-structure, formula-limit, and truncated-audit outcomes emit no candidates and preserve the base result.
- `scripts/evaluate_formula_patterns.py --performance-runs 3`: synthetic 24 TP / 0 FP / 0 FN, precision/recall/F1 1.00, `CONDITIONAL_GO`. The separate audit path measured average M4/base ratios of 1.771× (1k), 2.158× (10k), and 2.062× (30k), so the relative-cost limit remains documented.
- Local API smoke test on isolated `internal_beta` port 8001: base scan returned no M4 candidates; the optional audit returned `COMPLETED` with only `FORMULA_PATTERN_OUTLIER` and `FORMULA_PATTERN_GAP` on `samples/m4-evaluation/detected-patterns.xlsx`.
- Desktop/mobile browser capture was attempted through the approved browser runtime, but it reported no available browser. No unrelated browser automation was used; responsive component tests and production build passed, while a manual visual capture remains required when a controllable browser is available.

M4-C verification on 2026-09-01:

- `samples/m4c-evaluation/` contains the supplied synthetic 10-workbook practical corpus. The new exact-match regression verifies all 36 labelled target candidates, all 36 normal exceptions, and the clean-control workbook with no unexpected candidate; it also proves M4 remains absent from base findings and that base summary/risk/quote/CSV inputs are unchanged.
- `scripts/evaluate_formula_patterns.py --performance-runs 3`: existing M4-A.5 corpus remains 24 TP / 0 FP / 0 FN with precision/recall/F1 1.00; unsupported and hard-exclusion failures are zero; audit rule-set version is `2026.09.5` while the base rule-set remains `2026.09.4`.

M4-C execution-path recovery on 2026-09-01:

- Reproduced the reported behaviour against the supplied source folder: free scan counts are `0, 0, 49, 0, 0, 0, 0, 0, 0, 0`, while the separate M4 audit returns `4, 4, 4, 4, 4, 4, 4, 4, 4, 0`. The 49 free findings in scenario 03 are existing M0–M2 rules, not M4 candidates.
- The supplied source pack's expected manifest and workbooks are exercised both by the direct corpus gate and `POST /v1/formula-audits` integration test. `scripts/verify-m4c-sample-pack.ps1` prints both count classes separately and requires 36 exact M4 candidates with no extras.
- The internal-beta panel is rendered before the free Finding list, and a frontend test asserts that order after an uploaded file scan. Public/default mode remains unchanged.
- `scripts/dev.ps1 -InternalFormulaAudit` now sets both child-process gates on an actually bindable port pair selected from `8010–8090` / `5174–5190`, including matching CORS/API-base settings. It checks actual socket binding, so a stale/broken default `8000` / `5173` stack cannot be misrepresented as an enabled internal beta.
- The timing run remains `CONDITIONAL_GO` only because the predeclared relative-cost review limit is exceeded: 1k / 10k / 30k added 0.0400s / 0.4848s / 1.3296s, with 2.038x / 2.244x / 2.102x ratios. These are synthetic local measurements, not production performance claims.
- Final `scripts/verify.ps1`: frontend Vitest 22 and Vite production build passed; API pytest 32 and Ruff passed. The only warning remains the documented Starlette `TestClient` deprecation.

M4-C supplemental synthetic-pack remediation on 2026-09-01:

- A second user-supplied, checksum-verified synthetic pack (22 files) exposed a summary-row exclusion defect: matching `총계` inside formula source text caused every formula row that referenced `총계정원장` to be skipped. The exclusion now inspects only static row-label text, never a formula string. A focused regression test covers this exact condition while preserving labelled subtotal/total row exclusion.
- The additional pack now returns its exact 36 target candidates with 0 extras; its Holdout files return 4/4 and 0/0 candidates. Combined with the original pack, the engine returns 72/72 exact labelled candidates and 0 unexpected candidates.
- All non-conflicting labelled normal-exception ranges produce 0 candidate. The additional source manifest itself has two overlapping labels: expected targets `배부계산!E13` and `배부계산!F22` lie inside its own normal ranges `D6:I13` and `D22:I29`. This is a fixture-contract ambiguity, not an engine false positive; do not claim a strict 72-normal-exception gate until the fixture owner corrects those ranges.
- Final `scripts/verify.ps1`: frontend Vitest 23 and Vite production build passed; API pytest 34 and Ruff passed. The only warning remains the documented Starlette `TestClient` deprecation.

M4-D release-candidate closure on 2026-09-02:

- `scripts/evaluate_m4c_all.py --accept-product-owner-fixture-waiver` returned `PASS_WITH_PRODUCT_OWNER_WAIVER`: 20 files, 72/72 location/Rule/subtype matches, 0 unexpected candidates, 0 non-target normal-range candidates, 0 clean-control candidates, 0 scan failures, 0 base-result regressions, and 0 formula/value exposure fields. The only accepted exception is the two immutable target/normal label overlaps recorded as `M4C-2026-09-02-source-label-conflict`; source labels and checksums remain unchanged.
- `scripts/evaluate_formula_patterns.py --performance-runs 3` returned synthetic 24 TP / 0 FP / 0 FN and `CONDITIONAL_GO`; the relative performance limit remains an internal-beta operating constraint.
- Final `scripts/verify.ps1`: frontend Vitest 23 and Vite production build passed; API pytest 35 and Ruff passed. The non-failing Starlette `TestClient` deprecation warning remains documented.
- `docs/32_M4D_RELEASE_CANDIDATE.md` through `docs/36_M4D_FINAL_RELEASE_CANDIDATE_REPORT.md` record the RC contract, safe skip limits, memo-free local feedback, hosted-beta prerequisites, manual synthetic review, and final closure. No deployment or external user validation was performed.
