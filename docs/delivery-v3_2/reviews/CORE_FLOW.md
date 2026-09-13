# Core Product Flow / IA — 구현·보호 베타 검증 완료

2026-09-13 · **ENGINEERING_VERIFIED_AWAITING_OWNER**. 사용자 첨부 명세에 따른 D08 이후의 한정된 IA 후속이다. D08 전체 상용 판정은 **PARTIAL**이며 D09를 시작하지 않는다. 기존 진행·review·owner 문서와 예상 값을 보존했다. [기계 판독 증거](evidence/CORE_FLOW.json), [현재 베타](https://workbookcare-beta.wonderlogic-studio.workers.dev/).

## 1. Before / After 정보구조

| 이전 | 현재 |
|---|---|
| 홈에 진단·수정 진입·비교·주문·카탈로그·긴 안내가 함께 노출 | 홈은 무료 진단 → 문제 이해 → 수정 검토 중심 |
| 보조 서비스가 같은 긴 페이지 안의 섹션 | 정밀 검증 / 비교·대사 / 업무 자동화의 독립 URL |
| 수정 범위를 다시 수동 입력하는 진입 | Finding 또는 유형의 검토 선택에서 기존 사전 검사로 연결 |
| 결과의 필터 안에서 전체 표를 선택 | 유형별 보기 / 전체 항목 표를 직접 전환 |

보완 결정: 정밀 검증 페이지를 분리해도 **무료 구조·수식 후보의 결과 목록은 통합 상태를 유지**한다. 후보를 선택하는 행위는 지원 판정·결제·변경 승인이 아니다. 기존 제한된 수정 엔진을 재사용하고 미지원 고급 기능을 판매 가능하게 만들지 않는다.

## 2. Main Funnel

파일 업로드 → 무료 통합 진단 → 전체 요약 → 문제 유형 → 시트·셀 근거 → 수정 검토 선택 → 지원 가능 여부/범위 확인 → 이용 권리 → 정확한 변경계획·별도 승인 → 별도 수정본·재검증 → 세 파일 수령.

제품 목표의 **범위·가격 → 결제**는 현재 일반 고객에게 연결되지 않았다. 보호 베타에서는 등록된 합성 원본에 대한 시험권으로만 이후 경로를 검증한다. 시험권도 변경 승인을 만들지 않는다. 수정본 XLSX·변경내역 XLSX·재검증 HTML은 실제 기존 서버에서 생성했다.

## 3. Header / Menu

무료 진단 / 정밀 검증 / 비교·대사 / 업무 자동화 / 도움말. 오른쪽 Primary CTA는 **무료 진단 시작**. 모바일은 메뉴 버튼과 무료 진단 CTA를 유지한다. 수정 의뢰는 상단 판매 메뉴 대신 진단 결과의 다음 행동으로 연결한다.

## 4. Route와 복구

| URL | 동작 |
|---|---|
| `/`, `/diagnosis` | 무료 진단·결과·수정 검토 |
| `/precision-verification` | 제공 중인 패턴 확인 / 미구현 업무 검증 구분 |
| `/compare` | 기존 독립 두 파일 비교·보고서 |
| `/automation` | 표준 자동화 / 맞춤 제작 모두 현재 준비 상태 |
| `/help` | 카탈로그·파일 원칙·FAQ·이용/운영 안내 |
| `/repair` | 직접 방문 시 무료 진단 또는 지원 범위 안내 |
| `/orders` | 기존 소유권 검증이 있는 임시 베타 주문 확인 |
| `/privacy`, `/terms` | 기존 안내 내용 보존, 공통 탐색 구조 |
| 알 수 없는 경로 | 명시적 찾을 수 없음 안내 |

새 라우팅 의존성 없이 History API를 사용했다. 메뉴 이동 중 진단 결과·필터·처리 상태·검토 선택·펼친 셀·기존 작업을 유지한다. back/deep link와 기존 해시를 연결했다. 새로고침은 새 진단이며 파일의 영속 저장을 주장하지 않는다. 비교 새로고침 후에는 **‘두 파일 비교 사전 확인’을 한 번 눌러 기존 보관 작업을 복구**한다. 실제 464그룹 작업으로 확인했다. `/orders`는 가짜 계정 페이지가 아니며 실제 확인 시 보관 주문 0건이었다.

## 5. 재사용한 기능

L01~L08·CF·UXR의 무료 위치/근거·P1 필터·Action Category·사용자 상태·CSV·위험 점수·수동 재검사, M4 통합/내부 분리, H3 private/default-off 피드백과 기존 카탈로그를 재사용했다. D02~D08의 원본 검증·RP01/RP02 사전 검사·한정 계산·불변 계획·별도 승인·OOXML 보존 패치·재검증·원자적 세 파일·비교 두 보고서·임시 주문/만료/복구를 그대로 호출한다. 엔진·API·Worker 소스·배포 설정·기본 gate는 수정하지 않았다.

## 6. 실제 변경

- Home의 핵심 메시지·업로드·4단계 안내와 결과 기반 CTA. 현재 진행인 척하는 고정 단계 표시는 사용하지 않는다.
- 요약에 유형 수 / 위치 수 / 우선 확인 수를 분리. 공통 설명은 유형에 한 번, 시트별 셀은 차이·처리 상태·수정 검토 선택을 표시. 기술 근거·추가 판단 기준은 접어서 제공한다.
- 숫자 텍스트 단일 셀은 RP01, 명시적 실제 빈 셀 후보는 RP02 사전 검사로 연결한다. 나머지는 판단 필요/미지원으로 남긴다. 같은 시트·프로필 한 묶음씩 선택하며 지원 수를 미리 확정하지 않는다.
- 필터에 **표시된 항목만** 유형 단위로 검토 선택. ‘확인함’은 별도 버튼/상태다. 원본 고정 전 제외는 이전 초안을 무효화한다. 원본 고정 후에는 검토 선택을 잠그고 기존 기준 변경·재계획·일부 제외/재승인을 사용한다.
- 시트·셀·프로필만 전달한다. 업로드 동의·업무 기준 확인·필드 의미·기준 셀/수식·변경 승인은 자동 입력하지 않는다. 기존 수동 지정도 접힌 보조 진입으로 보존한다.

## 7. 삭제하지 않고 이동한 기능

정밀 검증 안내는 전용 페이지, 비교 작업은 `/compare`, 자동화 방향은 `/automation`으로 이동했다. 서비스 카탈로그·파일 원칙·FAQ·AI와의 역할 안내·운영 안내는 도움말에, 임시 주문 확인은 Footer에 배치했다. 기존 Quote는 결과의 ‘향후 수정 범위와 참고 견적 · 준비 중’으로 남겼다. Formula Audit internal beta와 피드백은 기존 플래그/분리를 유지한다.

## 8. 미구현 단계와 한계

일반 고객용 확정 지원 범위·견적/가격 정책과 구매 연결, 공식 PG checkout/인증/승인/조회/취소/webhook, 영속 상용 원장이 미완료다. 업무 정답·기대값 검증·범용 자동수정·자동화 상품도 미구현이다. 준비 상태로 표시하며 실제 가격을 확정하지 않았다.

기존 만료·오류·0지원·부분 지원·실행/파일/재검증 실패·복구 경로와 테스트는 보존했다. **이번 실제 베타에서 결제 실패·결제 후 취소·동시 부하·전 실패 유형을 새로 유발한 것은 아니다.** 공식 PG 시험은 계정 미준비로 NOT_RUN. 15분 임시 보관/재시작 손실, 동시 처리·모든 최대 조합, 별도 hard OS deadline, 상용 가격·세무·법률·지원 및 실제 사용자/구매 증거는 남아 있다. 합성 성공을 상용 준비나 모든 Excel 정확성으로 보고하지 않는다.

## 9. Desktop 실제 검증

1440에서 홈/업로드·정밀 검증·비교 입력/결과·탐색을, 1024에서 홈과 RP02 사전 검사/정확한 계획/세 파일 수령을 확인했다. 좁은 화면은 전체 폭 읽기 순서를 유지했다. 고정된 좌우 상세 패널은 추가하지 않았고 기존 펼침 구조를 재사용했다. [1440 홈](../../../artifacts/screenshots/core-flow/final-home-1440.jpg), [1024 납품](../../../artifacts/screenshots/core-flow/rp02-ready-1024.jpg).

## 10. Mobile 실제 검증과 예상 값

390에서 홈·메뉴·16건 유형/셀·전체 표·상태/선택·정상 재검사·RP01 일부 선택과 납품을 확인했다. 412에서 자동화·셀 상세·복합 비교의 긴 금액을 확인했다. 가로 넘침이 없고 주요 CTA/선택/승인/다운로드가 읽힌다. [390 홈](../../../artifacts/screenshots/core-flow/final-v5-home-390.jpg), [412 셀 상세](../../../artifacts/screenshots/core-flow/final-detail-412.jpg), [412 비교](../../../artifacts/screenshots/core-flow/compare-big-detail-412.jpg).

고정 `WorkbookCare_Complex_Validation_2026-09-13`의 독립 expected를 변경하지 않았다.

| 실제 베타 과업 | 화면과 산출물에서 대조한 값 |
|---|---|
| 01 다채널 혼합 | 구조1 + 수식15 = **16건 / 3유형**, 16개 위치 전체 일치, 온라인 필터5/전체16 |
| 02 정상 예외 | 구조0 / 수식0. 수동 재검사의 구조 기준 비탐지1 / 유지0 / 신규0; 업무 완전 해결로 표현하지 않음 |
| 03 RP01 일부 | 검토8 → B39/B52/B65/B94 제외 → **B12/B24/B78/B111 4개**, J130 **2,029,526**, 간접영향20 |
| 03 RP02 | **F31 5,232 / F64 3,551 / F107 7,800**, J130 **937,923**, 직접3+간접13 위치 |
| 05 비교 A/B | **464그룹**, A448/B440행. 일치350/금액차이41/A만23/B만23/모호14/자료오류13 |
| 큰 정수 | A 9,007,199,254,740,993 / B 9,007,199,254,740,992 → **차액1원** |

RP01/RP02는 시험권 뒤에도 승인 버튼의 별도 확인을 요구했다. 실제 베타 다운로드 **8파일**, 설치 Excel16.0/build20326 재개봉 **XLSX5개** PASS. 수정본은 각각725개 예상 값·수식·비대상 값과7개 비대상 ZIP member/원본hash, 비교는888원천행·정확한 분류/금액을 확인했다. 실제 Excel 출력3페이지도 시각 검토했다. 이번 화면에서888행의 모든 페이지를 다시 넘긴 것은 아니며 다운로드·Excel에서 전체를 검증했다. 이전 D08 전체 페이지 UI 증거는 보존했다. HTML은 실제 다운로드 내용을 파싱 대조했으며 이번에 브라우저로 HTML 파일 자체를 연 검증은 NOT_RUN이다.

검증 버전: 정상/CSV/상태 복귀는 v2, 실제 수정·비교/다운로드는 v4, 16개 위치는 v4에서 재확인했다. 마지막 v5 변경은 Header의 Esc 처리 범위뿐이며 웹 전체95개와 실제 모바일 버튼·링크의 Esc/초점 복원을 재시험했다. 이전 단계 결과를 v5에서 전부 다시 수행했다고 주장하지 않는다.

## 11. Accessibility / 성능

네이티브 button/link/select/details, label, 상태 텍스트, current-page 표시, skip link, 단일 main, 페이지 제목/헤딩 초점, 메뉴 Esc와 초점 복원을 확인했다. reduced-motion 대응을 유지했다. 전문 스크린리더·전체 WCAG/대비 감사는 별도로 수행하지 않았다. 새로운 라우터/상태관리 의존성은 없으며 최종 일반 빌드 JS349.23KB(gzip100.11KB), CSS64.72KB(gzip13.83KB)다. 상세를 펼쳐 읽는 기존 구조를 재사용했고 근거 없이 가상화를 추가하지 않았다.

## 12. 시험 명령 / exit code

| 명령 | 결과 |
|---|---|
| `npm.cmd run test --workspace @workbookcare/web` (시작 기준) | 78 PASS, exit0 |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify-m4-release.ps1 -AcceptProductOwnerFixtureWaiver` | exit0; 내부 `verify.ps1`까지 실행. 웹91 / Worker16 / API231 / Ruff / M4 exact36(no extras); 기존 quality CONDITIONAL_GO waiver 유지 |
| `npm.cmd run test --workspace @workbookcare/web -- src/App.navigation.test.tsx` (Esc 결함 재현) | 13 PASS / 1 FAIL, exit1 |
| `npm.cmd run verify --workspace @workbookcare/web` (마지막 수정 후) | **95 PASS / 22파일**, TypeScript·production build PASS, exit0 |
| 기존 실제 다운로드 검증기 복사본 `verify_complex_downloads.py` | 실제8파일/예상725셀씩/비교888행 PASS, exit0 |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File …\verify_complex_download_excel.ps1 -Mode repair` | 설치 Excel의 수정/변경내역4개 PASS, exit0 |
| 위 명령 `-Mode comparison` | 설치 Excel 비교1개 PASS, exit0 |
| `preservation.py` | 기존 owner83 / 이전 샘플68 / 복합 고정13 hash PASS, exit0 |
| 배포 helper v1~v5의 baseline → build → upload → deploy | 각 phase exit0; 실제 명령/바인딩 hash/Access 결과는 증거 JSON |

최종 full 회귀 뒤 추가 변경은 프런트엔드뿐이다. 마지막 웹95개 재시험을 full script의 웹91개와 구별했다. 원시 로그는 `artifacts/verification/ia-main-flow*.log`, 실제 산출물과 검증기는 `artifacts/verification/ia-main-flow/`에 보존했다. 실행 helper의 정확한 파일·명령·hash도 증거에 기록한다.

## 13. 실패 → 원인 수정 → 재시험 / 배포

처음 정적 섹션 이동에서 누락 아이콘 import로 build 실패, 숨긴 정밀 페이지 중복 문구로 UI 시험 실패가 있었다. import와 정적 페이지 조건부 렌더링을 고쳐 재시험했다. 실제 화면의 CSS 우선순위·큰 제목 줄바꿈·모바일 CTA 숨김·기존 grid 충돌·중복 수정 진입을 발견해 수정하고 각 웹 시험·화면을 재검증했다. 마지막 메뉴 버튼 Esc 실패는 이벤트가 nav에만 있던 원인으로, Header로 범위를 옮기고 재현 시험과 실제 버튼/링크에서 통과했다.

RP02 DOM 검증기의 직접 DD/간접 article 구조 차이, UTF8 읽기, 자동화 선택자/파일 chooser/스크롤 timeout과 잘못된 전역 Python의 httpx 부재는 도구/검증기 실패로 분리했다. 기존 프로젝트 Python과 실제 DOM을 사용해 복구했으며 숫자 예상 값이나 합격 기준을 바꾸지 않았다. 해소 전 임시 PASS 표시는 최종 증거에서 제거했다.

최종 Worker **`5a857656-3807-4fb5-84a5-70b6b49517ee` 100%**, private API **`workbookcare-api-beta-00014-nah`** 그대로다. 모든 기존 바인딩 hash·API spec/traffic/IAM을 대조했다. 9개 사이트/API 경로는 익명 접근302→기존 Access. HMAC/private R2/KV·기본 gate·PAYMENT_MODE OFF 유지. 기존 Gateway를 변경하지 않았으며 신규 자원/Docker/Cloud Run 수정/원격 push는 없다. [배포·롤백 기록](../../50_BETA_RELEASE_WORKFLOW.md).

## 14. 변경 파일

- `apps/web/src/App.tsx`
- `apps/web/src/App.test.tsx`
- `apps/web/src/App.navigation.test.tsx`
- `apps/web/src/main.tsx`
- `apps/web/src/product-flow.css`
- `apps/web/src/components/Header.tsx`
- `apps/web/src/components/Brand.tsx`
- `apps/web/src/components/Footer.tsx`
- `apps/web/src/components/ProductPages.tsx`
- `apps/web/src/components/StaticSections.tsx`
- `apps/web/src/components/LegalPage.tsx`
- `apps/web/src/components/M25ResultsPanel.tsx`
- `apps/web/src/components/ProgressiveFindingViews.tsx`
- `apps/web/src/components/RepairReview.tsx`
- `apps/web/src/components/RepairReview.test.tsx`
- `apps/web/src/components/DeliveryWorkspace.tsx`
- `apps/web/src/lib/navigation.ts`
- `apps/web/src/lib/repairReview.ts`
- `docs/09_CURRENT_MILESTONE.md`
- `docs/10_PROGRESS.md`
- `docs/11_DECISIONS.md`
- `docs/MILESTONE_REVIEW.md`
- `docs/50_BETA_RELEASE_WORKFLOW.md`
- `docs/51_CORE_PRODUCT_FLOW.md`
- `docs/delivery-v3_2/reviews/D08.md`
- `docs/delivery-v3_2/owner_action.md`
- `docs/delivery-v3_2/delivery-progress.json`
- `docs/delivery-v3_2/release_manifest.json`

선택한 시각 증거는 `artifacts/screenshots/core-flow/`. 원시 로그/다운로드는 ignored artifacts에 남긴다. 기존 미변경 내용의 API lock 표시, owner 원본 미추적83개, 이전 미추적 스크린샷은 커밋에서 제외한다.

## 15. Git commit

기준 `297c57a55561d5ca7fdc62566280c3d3882d6a0d`, main. 검증한 변경만 `refactor: simplify WorkbookCare core product flow`로 선별 로컬 커밋한다. 완료 hash·명령 exit·선택 파일은 [커밋 증거](evidence/CORE_FLOW-commit.json)에 기록한다. 원격 push 없음.

## 16. 사용자가 확인할 다섯 행동

1. 베타 새로고침 후 홈에서 무료 진단을 시작하고, 모바일 메뉴의 추가 서비스가 별도 페이지로 열리는지 확인한다.
2. 복합01을 올려 **16건/3유형** → 시트 → F22 근거를 펼친다. 전체 표·필터·확인함·메뉴 이동 후 복귀가 유지되는지 본다.
3. 복합03의 숫자 텍스트8개를 검토 선택하고4개만 남겨 RP01을 진행한다. J130 **2,029,526**과 별도 승인, 세 파일을 확인한다.
4. 같은 원본에서 RP02 F31/F64/F107과 기준F8을 지정한다. **5,232 /3,551 /7,800 /합937,923**, 수정본·변경내역·재검증을 확인한다. [정확한 입력 안내](../../../samples/WorkbookCare_Complex_Validation_2026-09-13/README.md)를 사용한다.
5. 별도 비교 페이지에서05 A/B를 비교해 **464그룹/차액1원**을 확인한다. 정밀 검증의 미지원 범위와 자동화 준비 상태가 구매 상품으로 보이지 않는지 본다.

## 17. 다음 한 단위 제안 / 여기서 정지

**‘지원 가능 여부 → 수정 의뢰 범위·견적’의 일반 사용자용 연결**을 다음 한 단위로 제안한다. 이미 계산·수정·재검증 경로가 있으므로 앞쪽의 미지원/부분지원·제외 항목·정확한 납품 범위를 확정하는 화면/계약을 먼저 연결한다. 가격 정책·구매 승인 전에는 결제나 판매를 켜지 않는다. 이번에 자동 실행하지 않으며 사용자 검토를 기다린다.
