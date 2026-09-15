# ORCH-01 — PL / Builder / Reviewer 운영 구성

2026-09-15 · **CONFIGURED_VERIFIED_AWAITING_OWNER / 다음 단위 전 정지**. 사용자 요청은 세 역할 구성과 서비스 방향·측정 가능한 편의성 기준이다. 이번 변경은 운영 설정/지침/진행 기록이며 제품 기능·화면·배포·push는 포함하지 않는다. 기존 D08 PARTIAL·Proposal Flow 완료 증거와 사용자 미커밋 파일을 보존한다.

## 실제 변경·재사용

- `.codex/config.toml`과 `.codex/agents/pl.toml`, `builder.toml`, `reviewer.toml`: 루트 PL + 하위 동시성2, 모델/추론 상속, PL/리뷰어 read-only 요청, 빌더 workspace-write 요청.
- `docs/54_AGENT_ORCHESTRATION.md`: 서비스 대전제·한 단위 작업지시·자동 인계·승인·역할별 책임·실제 증거·편의성 측정 기준.
- `AGENTS.md`, context index, 기존 운영 가이드와 milestone-runner 연결. 기존 ‘진행 기록 교체’ 지시를 ‘현재 결과 추가/기존 기록 보존’으로 보완했다.
- 현재 milestone/progress/decision/review/owner_action은 기존 원문 앞에 이번 결과만 추가한다. progress JSON은 `agent_orchestration` delta만 추가하고 기존 값을 유지한다.
- PL은 고객의 탐지→지원 수정안→정확한 승인→사본/변경내역/재검증 수령을 대전제로 유지한다. 빌더만 승인된 제품 소스를 수정하고 리뷰어는 독립 검증한다. 이번에도 실제 builder/reviewer 위임·수정 반환·재검토를 수행했다.
- 기존 RP01/RP02와 무료/M4/비교/보안/결제 경계를 재사용한다. Ponytail의 재사용/최소 변경 원칙을 반영했고 플러그인은 설치하지 않았다.

## 편의성 예산과 현재 판정

주요4단계 이하, 빈 작업부터 **세 산출물 수령까지** 필수 앱 activation10회 이하, 필수 셀 주소/수식 입력0회, 같은 정보 재입력0회, 현재 다음 주CTA1개를 초기 목표로 정의했다. 필수 상세 공개·동의·별도 승인·실행·3개 다운로드도 포함한다. OS/Access/스크롤/선택적 상세/대기·포커스 이동 등은 별도 보고하며 숨기지 않는다. 업무 판단을 AI가 대신하거나 승인을 약화해 목표를 달성하지 않는다.

모두 **NOT_MEASURED**이며 실제 사람의 이해·편의성 시험은 **NOT_RUN**이다. 기존4단계 코드를 읽은 것을 새 UX 합격으로 세지 않는다. 후속 승인 작업에서 기본/부분선택/정상/미지원/조건 변경 경로를 측정한다. 클릭 수뿐 아니라 재입력·되돌아감·도움 요청과 실제 설명 가능 여부를 본다.

## 실제 검증·실패·원인 수정

| 명령/검토 | 결과 |
|---|---|
| `git status --short --branch`, `git log -1 --format='%H %s'` | exit0, 시작 main6681dc6, origin/main보다33 commits 앞선 로컬 추적 상태. 원격 재조회 없음 |
| `codex --version`, `codex --help`, `codex debug --help` | exit0, 0.154.0-alpha.6.2. 제한된 홈 임시 PATH 정리 경고 있음 |
| 빌더 최초4설정 생성 | 승인 검토 capacity로 프로세스 미실행. 경로/부재 확인 후 같은 승인 경로 재시도 exit0 |
| `codex --strict-config features list` | exit1, 해당 명령이 옵션을 지원하지 않음. 설정 자체 실패로 해석하지 않음 |
| 기본 홈 app-server config/read | exit1, SQLite 초기화 권한 부족. 모델 호출 없음 |
| `python <scratch>/probe_config.py` | 격리 CODEX_HOME에서 설치 Codex app-server --strict-config → initialize → config/read exit0. 실제 project layer 활성·enabled=true·동시성2. 사용자 전역 홈 변경/추가 모델 호출0 |
| `python <scratch>/record_builder_evidence.py` | exit0. 4TOML 파싱/3역할명/필수필드/모델 상속/sandbox 요청/합성 증거 허용 확인 |
| 독립 reviewer 초회 → 빌더 수정 → 재검토 | CHANGES_REQUIRED → 문구3곳 수정 → 내용 PASS. 모든 workbook 내용 금지가 합성 예상/실제값 보고와 충돌하므로 실고객/비밀값 금지·값 없는 운영 로그·지정 합성 증거 허용을 구분 |
| `python <scratch>/apply_operating_docs.py` 1–3회 | 자동 승인 검토 ‘Selected model is at capacity’로 프로세스 미실행/exit없음. 경로·구문 검토 및 독립 리뷰 수행 |
| 같은 정상 승인 경로4회차 | **exit0**, 운영 지침5파일 반영. 권한 우회 없음. 사용자에게 요청했던 작업 폴더 전환은 도구 결과상 아직 DigitalTwin이며 정상 승인 경로 복구로 작업 진행 |
| `python <scratch>/apply_operating_docs.py --stage`, `prepare_records.py`, `finalize_records.py` | stage 준비와 기존 progress 의미/원문 보존 확인. 실제 repo 최종 적용은 별도 명령으로 검증 |

`<scratch>` = `C:/Users/JinwonLee/project/DigitalTwin/.tmp/workbookcare-orchestration`. 마지막 적용·검증 명령/exit는 [기계 판독 증거](evidence/ORCHESTRATION.json)에 남긴다. 선별 local commit 명령·exit·최종 SHA는 로컬 [commit 기록](../../../artifacts/verification/orchestration/commit.json)과 Git 이력에서 확인한다.

## 검증의 한계와 미실행

설정 파싱과 실제 project config/read, 역할 지침을 전달한 builder/reviewer 인계는 확인했다. config/read는 개별 역할 정의 목록을 노출하지 않으므로 **네이티브 개별 역할 자동 발견/선택·Desktop 재로드는 미검증**이다. 현재 도구가 이름별 역할 선택을 지원하지 않으면 PL이 역할 TOML 지침을 읽어 메시지로 전달하는 fallback을 계약에 명시했다.

`read-only`는 요청 sandbox이며 부모의 실행 중 권한이 우선할 수 있다. 파일별 allowlist와 소스 수정 금지는 운영 지침이고, 실제 OS/도구 강제 권한 분리 성공으로 주장하지 않는다.

제품·기존 샘플·사용자 미추적 파일460개 hash를 기록해 보존을 확인했다. 과거 검증을 이번 제품 회귀로 세지 않는다. 제품 전체 회귀·베타 화면·다운로드/Excel·PG·UX 실측·사람의 이해는 이번에 실행하지 않았다. 제품 코드/화면 변경이 없으므로 설정 검증을 수행했다. 기존 보호 베타 승인 범위는 보존하지만 이번 운영 설정을 배포하지 않았다. 원격 push·실고객 자료·실결제/환불·새 자원·익명 공개 없음.

**다음 한 단위 제안:** FLOW-01 — 기존 RP01/RP02의 탐지→실제 수정→동일 검사로 후보 해결 확인과, 그 실제 베타 경로의 사용자 행동 수 측정. 미승인·미실행이다. 이전 다음 제안과 D08 PARTIAL 판정을 보존한다.
