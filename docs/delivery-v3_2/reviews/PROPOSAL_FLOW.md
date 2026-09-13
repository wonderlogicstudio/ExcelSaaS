# Proposal Flow — 이해할 수 있는 수정 제안과 원하는 결과 대조

2026-09-13 · **ENGINEERING_VERIFIED_AWAITING_OWNER / 작업 정지**. [보호 베타](https://workbookcare-beta.wonderlogic-studio.workers.dev/)에 반영했습니다. D08 전체는 **PARTIAL**입니다. [기계 판독 증거](evidence/PROPOSAL_FLOW.json).

사용자에게 셀 주소와 기술 용어부터 요구하면 진단 결과를 이해하기 어렵다는 의견을 반영했습니다. 기존 탐지·수정 규칙이 지원하는 제안을 먼저 보여주고, 업무 의도를 확인한 뒤 실제 계산 결과를 제시합니다. 주변 수식만으로 업무 정답을 확정하거나 원하는 숫자가 나오도록 수식을 만들어내지는 않습니다.

## 실제 구현·재사용

| 변경 | 동작 |
|---|---|
| 시트 선택 → 수정 제안 | 무료 결과에서 셀을 고르지 않아도2단계에 진입. 파일의 실제 시트와 발견된 셀을 시트·열·지원 규칙으로 묶음. 후보 없음/미지원/검증할 후보를 구별하며, 후보를 수정 가능 확정으로 표시하지 않음 |
| 이해할 수 있는 기준 | ‘필드 역할’을 금액·개수·구분 번호 질문으로 바꿈. 원본 예시와 열 위쪽의 실제 설명 표시. 열 이름으로 업무 역할을 단정하지 않으며 식별자는 차단 |
| 빈 셀의 계산 방식 | 원본에 실제로 존재하는 기준 수식을 선택. 저장값과 실제 계산값을 구분. 사용자가 같은 업무 계산이라고 확인해야 다음으로 진행 |
| 선택 범위 | 기존 무료 단계의 선택을 우선 유지. 전체 후보 전환은 명시적 선택이며 자동 확장 없음. 제안 안에서 개별 셀 제외 가능. 수동 주소 지정은 보조 진입 |
| 의견 입력 | 기본값은 ‘별도 의견 없이 규칙으로 확인’. 선택적으로 숫자 희망값 또는 기준 셀의 계산 방식 요청. 대상 시트·발견 위치는 선택하고 필요하면 주소 입력 |
| 대표 예시 먼저 | 기존 격리 계산과 권리 확인을 통과한 실제 계획에서 현재→계산 후 예시1개, 변경 수·간접 영향 수를 표시. 다음 버튼은 예시 아래.3단계에서 전체 전후 값·수식을 열어 확인해야 별도 승인 가능 |
| 요청 대조 | 실제 계획의 숫자 결과와 정확한 십진 비교. 다른 값/미포함 셀/입력 불가/기준 불일치는 승인 경로 차단. 요청을 바꾸면 이전 작업을 삭제하고 새 계획 확인. 일치 자체는 승인 아님 |
| 서비스 안내 | 정밀 검증의 미구현 추가 업무 검증과 메인 흐름의 제한된 요청 대조를 구별. 비교는 B를 정답으로 보지 않는 별도 보고서 유지 |

기존 L01–L08·CF·UXR의 진단·위치·근거·필터·구조 CSV·위험 점수·개인 메모·재검사, M4 값 없는 탐지 API, D02–D08의 RP01/RP02·원본 고정·OOXML 보존 패치·격리 계산·불변 계획·권리·별도 승인·실행·세 파일 납품을 재사용했습니다. H3 private/default-off, Access, HMAC, private R2/KV, private API와 결제OFF를 변경하지 않았습니다. 새 API·엔진·런타임 의존성·LLM 호출은 없습니다.

브라우저 ZIP reader의 기존 크기·CRC·경로·XML·암호화·취소 보호를 유지하며 실제 시트 메타데이터와 요청한 셀만 읽습니다. reader는 한 번에64셀 이하를 받고 제안은 대표 위치·제공 근거 최대6개·열 상단 최대8셀을 읽습니다. 원본 미리보기와 희망값은 브라우저 세션에만 보관합니다. **사용자가 선택하고 확인한 기준 셀 주소·수식은 기존 private 사전 검사 정책으로 전달**되며, 이를 새 AI/로그/피드백 수집으로 확대하지 않았습니다.

## 실제 베타·예상값 검증

기존 `WorkbookCare_Complex_Validation_2026-09-13/expected`를 그대로 사용했습니다. 예상값을 현재 코드 출력에 맞춰 변경하지 않았습니다.

| 시험 | 실제 결과 |
|---|---|
| 03 무료 검사 | 구조8 + 수식3 = **11건/2유형**, 기본 의견 없음. 정산 후보11곳, 보존정보 후보 없음 |
| RP01 일부 | 자동 제안8곳 중 B12/B24/B78/B111만 선택. 문자 “-1,250”→숫자-1,250. 정확한4변경·간접20계산 전후 UI 대조 PASS, J130 **2,029,526** |
| RP02 숫자 요청 | F31에10을 요청하고 F30 기준으로 계산 → **5,232**, 불일치 설명·3/4단계 잠금·승인 없음. 작업 삭제 후 요청을5232로 바꿔 새 계획 → 일치, 별도 승인 요구 |
| RP02 전체 | F31/F64/F107 **5,232 / 3,551 / 7,800**, 정확한 복원 수식3개·계산 위치16개 UI 대조 PASS. J130 **937,923**. 승인과 별도 실행 후3파일 |
| 기준 셀 요청 | ‘F31도 F8과 같은 계산 방식’ → 실제 F8 수식 선택·저장값1742 확인, 자동 업무 확인 없음. 실제 계산5232·요청 대조 완료. 전체 목록 공개 전 승인 없음. 이 추가 시험은 승인/실행하지 않고 임시 작업 삭제 |
| 구분 번호 | 실제 라디오 선택 후 제안 버튼 차단. 앞자리0·고유 표기 보존 안내 |
| 복합01 | 기존 **16건/3유형** 유지, 고정값/기존 수식 변경은 미지원. 채널요약 시트 미지원과 빈 셀 후보를 구분 |
| 정상02 / 서식04 | **0건 / 구조1·수식0**, 후보 없는 시트와 미지원 문서 위험 표시. 후속 승인·수령 잠금. 이번에는04의 수동 사전 검사 API 시험을 재실행하지 않음 |

실제 다운로드 **6파일**의 수정본별725개 고정 예상값, 변경내역4/3행, HTML9검사와 영향20/13개, 원본·비대상·ZIP member7개 보존 PASS. 설치 **Excel16.0/build20326**에서 실제 XLSX4개를 읽기 전용으로 열어 수정본별725개 재계산 값, 수식602/605개, 비대상 원본값854/858개를 확인했습니다. 다운로드 hash 불변이며 Excel이 출력한 합계 PDF2페이지도 이미지로 확인했습니다. 계약 모형의12나 큰 정수 시험을 실제 Excel/PG 검증으로 세지 않았습니다.

1440/1024/390/412폭 실제 화면을 확인했습니다. [최종 대표 예시](../../../artifacts/screenshots/proposal-flow/1440-final-reference-example.jpg), [모바일 단계와 예시](../../../artifacts/screenshots/proposal-flow/412-final-approval-overview.jpg), [희망값 불일치](../../../artifacts/screenshots/proposal-flow/1440-intent-mismatch.jpg), [모바일 수령](../../../artifacts/screenshots/proposal-flow/390-RP02-ready.jpg). 초기 `390-intent-mismatch` 캡처는 viewport 전환 직후의 오래된 프레임이 잘렸으므로 모바일 통과 증거로 사용하지 않았습니다. `1440-subset-confirm`도 체크 직전 프레임이어서 승인 상태의 근거로 세지 않았습니다. 이후 DOM·수령·모바일 화면으로 확인했습니다.

## 명령·원인 수정·재시험

실행 위치는 프로젝트 루트, `<scratch>`는 `C:/Users/JinwonLee/project/DigitalTwin/.tmp/proposal-flow`입니다. 세부 단계 명령·exit·hash는 증거 JSON과 `artifacts/verification/proposal-flow/`에 기록했습니다. helper는 `executed-helpers/`에 보존했습니다.

| 명령 | 결과 |
|---|---|
| `npm.cmd run verify --workspace @workbookcare/web` baseline | 121 PASS·타입·빌드, exit0 |
| 같은 명령 web-1 / web-2 | 125PASS·4FAIL exit1 / 138PASS·1FAIL exit1 |
| 같은 명령 web-3 / web-final / web-copy | 각각 **139 PASS/27파일**, 타입·빌드 PASS, exit0 |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify-m4-release.ps1 -AcceptProductOwnerFixtureWaiver` | 내부 전체 `verify.ps1` 포함. 웹139/Worker16/API231/Ruff/M4 exact36 PASS, exit0. 기존 CONDITIONAL_GO fixture waiver 유지 |
| `<scratch>/verify_plan_ui.py RP01_SUBSET`, `RP02_ALL` | 실제 DOM의 전후 값·고정 oracle 대조, 각각 exit0 |
| `<scratch>/collect_complex_downloads.py begin/collect <case>` | 두 기존 프로필의 실제3파일씩, 네 명령 exit0 |
| `<scratch>/verify_complex_downloads.py` | 실제6파일·고정 expected PASS, exit0 |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File <scratch>/verify_complex_download_excel.ps1 -Mode repair` | 실제4XLSX 설치Excel PASS, exit0 |
| `<scratch>/render_native.py`, `preservation.py` | PDF2페이지 및 owner83/기존샘플68/복합고정13 hash 보존, 각각 exit0 |
| release / release_final / release_copy helper baseline/build/upload/deploy | 각 exit0, 기존 바인딩·API spec/traffic/IAM·9경로 Access 확인 |
| `git diff --check` | exit0 |

첫 웹 실패4개는 이전 UI의 진입ID/명칭과 즉시 펼쳐진 전체 상세를 가정한 시험이었습니다. 기존 진입ID를 보존하고 새 선택·공개 흐름을 실제 클릭하도록 수정했습니다. 다음1개는 만료 경고가 나타나기 전에 숨겨진 승인 유무만 기다린 시험이므로 실제 만료 상태를 기다리게 고쳤습니다. 선택 변경 시 이전 전체 후보 설정이 남지 않도록 선택 subset 효과를 보완했고, 요청 위치가 실제 blank→formula patch에 존재하는지도 검사합니다. 숫자는 Number 반올림/허용 오차 대신 정확한 십진 문자열 비교를 사용합니다.

첫 파일 편집 helper는 실제 div를 section으로 가정해 중단됐고 남은 위치만 확인 후 보완했습니다. 읽기 전용 경로 추정 실패는 실제 파일 검색으로 복구했습니다. CUA의 접근성 이름/클릭 타이밍/지원하지 않는 DOM `compareDocumentPosition` 호출은 새 snapshot·키보드·문서 순서 읽기로 확인했습니다. 예상값이나 통과 기준을 낮추지 않았습니다. 전체 회귀 후 변경은 다음 단계 버튼 위치·주석과 별도 서비스 안내 두 문장뿐이며 웹139·타입·빌드를 재시험했습니다. 기존 API Starlette 경고1개는 남습니다.

## 배포·보존·제한

최종 Worker **`1fa2992b-c75d-400b-8acc-14dd484c7a40`100%**. 이전 `6372fd95-9810-4cdd-8ebe-c8d01e35ad3d`, 첫 제안 버전 `93719bc2-a601-4fc0-94fc-cf4c8d9b56e6`, 단위 전 `4f756e00-dc3d-4c2c-ae5c-862e79b6422c`. 첫 버전에서 숫자 일치/불일치와 실제6다운로드·Excel을 검증했고, 두 번째에서 대표→다음 버튼·기준 셀 요청·모바일·미지원 사례를 확인했습니다. 최종 차이는 ProductPages 안내 두 문장으로, 최종 정밀/비교/메인·식별자 화면을 확인했습니다. 모든 기능 시험을 마지막 버전에서 재실행했다고 주장하지 않습니다.

private API **`workbookcare-api-beta-00014-nah`**, Gateway·Access·HMAC·private R2/KV·기존 플래그·결제OFF를 유지했습니다. API 배포/새 자원/원격 push/롤백 실행 없음. 기존 기록은 앞에 현재 결과를 추가하고 JSON delta로 보존했습니다. 시작부터 있던 내용 차이 없는 API lock 표시와 사용자 미추적83문서·과거 스크린샷은 커밋에서 제외했습니다.

**현재 한계:** 의견은 브라우저 세션의 제안 대조 조건이며 서버의 불변 승인 기록이나 납품 HTML에 저장하는 계약이 아닙니다. 새로고침·새 파일에서 사라집니다. 임의 자연어·AI 제안·기존 SUM 범위 변경·기존 값 덮어쓰기·고객 업무 정답 판정은 제공하지 않습니다. 제안 그룹은 발견된 위치만 대상으로50개까지 표시하며 전체 시트의 모든 문제를 찾는 기능이 아닙니다. 요청 위치의 검증된 결과가 계획에 없으면 대조 불가로 차단합니다. 현재 등록 합성 파일만 수정 시험 가능, 작업15분 임시 보관, 일반 구매/공식PG·가격·상용 영속 운영·동시 부하/전체 최대 조합·실사용자 수용은 미완료입니다. 이번에는 비교888행·최대한도·HTML 자체 브라우저 열기 시험을 반복하지 않았습니다.

[사용자 확인5행동](../owner_action.md)을 남기고 멈춥니다. **다음 한 단위 제안은 ‘사용자 요청 조건을 서버 승인계획·재검증 보고서에 연결’**입니다. 현재 세션의 숫자/기준 요청을 원본·계획에 고정하고 보고서에도 일치 여부를 남기는 범위로 제한하며, AI나 새 수정 규칙은 별도입니다. 지금 실행하지 않습니다.
