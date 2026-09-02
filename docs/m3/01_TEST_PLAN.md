# M3-A 사용자 이해·전환 의향 테스트 계획

## 상태와 범위

상태: `Preparation` (M3-A 준비 완료 전용). 이 문서는 실제 참여자 세션, 사용자 반응 또는 M3 완료를 기록하지 않는다.

목적은 M2.5 결과 화면이 사용자의 이해와 다음 행동을 돕는지 정성적으로 확인하는 것이다. 결제율, 시장 규모, 가격 확정, 자동수정 정확도, 사업 성공은 이 테스트의 판단 대상이 아니다.

테스트할 현재 화면은 Finding을 중복된 대표/전체 카드로 보이지 않는다. 하나의 접힌 전체 목록에서 기본 카드의 심각도·규칙 코드·위치·제목을 읽고, `자세히 보기`를 열어 발견 사실·가능한 영향·Excel 확인법·이번 검사 한계·처리 상태를 찾는 구조다.

## M2.5 기준선

| 항목 | 기준 |
|---|---|
| 기준선 확인일 | 2026-09-01, 로컬 개발 환경 |
| Git 기준 | 이 작업공간은 Git 저장소가 아니므로 commit hash 없음 |
| scanner / rule set | `0.1.2` / `2026.08.2` |
| Scenario A | `samples/demo-risky-workbook.xlsx`와 `apps/web/src/data/demo-result.fixture.json` |
| Scenario B | `samples/m3/low-or-zero-findings.xlsx`와 대응 fixture |
| Scenario C | `samples/m3/revalidation-before.xlsx`, `revalidation-after.xlsx`와 대응 fixture |
| 사전 전체 검증 | `scripts/verify.ps1` 통과: frontend Vitest 16, Vite build, API pytest 18, Ruff |

이 기준선은 검사 결과의 버전·샘플·fixture로 식별한다. 시나리오 fixture는 실제 scanner + recommendation engine 결과에서 생성되며, `apps/api/tests/test_m3_scenario_fixtures.py`가 정합성을 검사한다.

## 참여자와 라운드

총 8명의 정성적 표본을 사용한다. 시장 전체나 결제율을 대표하지 않는다.

| 라운드 | 인원 | 목적 | 제품 변경 규칙 |
|---|---:|---|---|
| Round 1 | 3 | P0/P1 오해, 정보 과밀, CTA·상세 구조 혼란 탐색 | P0 또는 반복 P1은 최소 수정안을 별도 승인받은 뒤에만 수정 |
| Round 2 | 5 | Round 1의 반복 혼란 감소와 통과 기준 확인 | Round 1 승인 수정 외에는 새 기능을 추가하지 않음 |

대상은 중요한 Excel 파일을 작성·수정·검토·전달하기 전에 오류를 걱정하는 실무자다. Excel을 자주 쓰되 전문 개발자가 아닌 사용자, 매출·재고·비용·보고서 파일 담당자, 검토·승인 사용자, 일부 Excel 숙련자를 섞는다. 모든 참여자를 강의 수강생 또는 Excel 전문가로 구성하지 않는다.

## 방식과 자료

- 참여자당 핵심 세션은 15~20분, 화면 공유 또는 같은 PC에서 진행한다.
- 진행자는 시작 시 제품·정답·기능 범위를 설명하지 않는다. 참여자가 생각을 말하며 수행한다.
- 실제 회사 파일, 개인정보, 파일 업로드를 쓰지 않는다. 모든 자료는 `samples/`의 합성 파일이다.
- 이름 대신 `U01`~`U08`을 사용한다. 별도 동의 없이는 녹화하지 않는다.
- 핵심 과제는 Task 1~6이다. Task 7~9은 시간이 남을 때만 진행하는 후반 모듈이다.
- 관찰은 `05_OBSERVATION_TEMPLATE.csv`, 판정은 `06_SCORECARD.md`를 쓴다.

## 고정 범위

M3-A와 실제 테스트 동안 새로운 진단 규칙, 자동수정, 수정본 XLSX, 결제·신청·계정·DB·분석 도구·AI API·배포·관리 화면·M4/M5 기능을 만들지 않는다. 실제 사용자 Round 1 전에는 카피·레이아웃·정보 구조도 바꾸지 않는다.

## 종료 조건

M3-A는 테스트 자료와 운영 문서, 실제 scanner 결과 기반 시나리오, 최소 실행 절차가 준비되면 종료한다. Round 1/2 결과는 비어 있어야 하며, 제품 변경이나 M3 완료 선언은 하지 않는다.
