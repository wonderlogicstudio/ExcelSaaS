# ORCH-02 — 역할·난이도별 모델 배정

2026-09-15 · **CONFIGURED_VERIFIED_AWAITING_OWNER**. 사용자 “역할과 작업 난이도에 따라 나누어서 진행” 승인에 따라 모델 설정만 변경했다. 기존 서비스·UX·검증·보안·원본 보존과 D08 PARTIAL 판정은 유지한다.

| 역할/작업 | 모델 / 추론 |
|---|---|
| PL 기본 | GPT-6 Astra / Medium |
| 빌더 기본 | GPT-5.5 / Medium |
| 리뷰어 | GPT-6 Astra / High |
| 빌더의 명확한 문구·간격 수정 | GPT-5.5 / Low |
| 수식·파일 보존·승인·재검증 연계 | GPT-5.5 / High |
| 충돌한 설계 판단·반복 실패 난제만 | GPT-6 Astra / High |

## 변경·재사용

기존4TOML에 모델/강도를 명시하고 일반 하위 작업 기본을5.5Medium으로 지정했다. 기존 name/description/sandbox/developer 지침은 보존하고 배정 정책·요청 모델 보고·저장과 실제 전환 구분 안내 한 문장만 추가했다. 동시 하위 작업2개와 세 역할 구성을 유지한다. docs54에 난이도 배정·전체 대화 복제 방지·고정 역할 설정 우선순위·일반 위임 경로를 추가했다. 진행 기록은 원문 앞에 추가하고 JSON에는 `agent_model_routing`만 추가한다.

고정 역할 TOML이 spawn의 model/effort보다 우선할 수 있으므로 비기본 Low/High는 역할 지침을 전달한 일반 위임으로 수행한다. 현재 도구에서는 `fork_turns="none"`과 짧은 작업지시·필요 경로/증거로 시작한다. Spark는 현재 위임 도구에 없어 선택하지 않고 GPT-5.5Low를 사용한다. 절감률은 측정하지 않았으며 보장하지 않는다. 낮은 모델도 동일한 검증을 통과해야 한다.

## 실제 명령·증거

`<scratch>`는 `C:/Users/JinwonLee/project/DigitalTwin/.tmp/workbookcare-routing`이다.

- 시작 `git status --short --branch`, `git log -1 --format='%H %s'`: exit0, main8012895·로컬 추적 기준34 commits ahead. 원격 조회 없음.
- `python <scratch>/apply_orch02_routing.py`: 최초 자동 승인 모델 capacity로 프로세스 미실행/exit없음. 대상 경로·기존hash·구문을 읽기 확인한 후 같은 정상 승인 경로 재시도 **exit0**. 권한 우회 없음.
- `python <scratch>/validate_orch02.py`: **exit0 / PASS**, 4TOML·역할3개·기존 지침/sandbox 보존.
- `python <scratch>/probe_config.py`: **exit0**, 격리 CODEX_HOME에서 설치된 Codex app-server --strict-config config/read로 root AstraMedium, 일반 하위5.5Medium, enabled=true/동시성2 확인. 검증용 추가 모델 호출0·사용자 전역 설정 변경 없음.
- `python <scratch>/update_contract.py --apply`: **exit0**, 운영 계약1파일 반영.
- 빌더에 GPT-5.5Medium, 리뷰어에 AstraHigh를 명시해 실제 작업을 위임했다. 리뷰어는 실제4TOML과 운영 계약·일반 위임 예외·기존 안전 조건을 읽고 **PASS**를 반환했다. 모든 검증 단계를 새 모델로 재실행하는 벤치마크는 하지 않았다.
- 최종 `record_and_check.py`: 기존 문서 원문·이전 progress JSON 값·제품/샘플/사용자파일460개hash, 설정값, diff 확인. 세부 exit/결과는 [증거](evidence/MODEL_ROUTING.json)에 기록한다.
- 선별 local commit 명령·exit·SHA는 [로컬 commit 기록](../../../artifacts/verification/model-routing/commit.json)에 기록한다. 원격 push 없음.

## 한계·미실행

프로젝트 설정을 저장해도 **이미 진행 중인 루트 대화의 모델은 변경되지 않는다**. 즉시 PL 강도를 바꾸려면 현재 실행 환경의 모델 선택이 필요하며 새 프로젝트 실행의 기본값과 구별한다. 네이티브 개별 역할 자동 발견/선택·Desktop 재로드·sandbox 강제성은 미검증이다. config/read는 역할 정의 목록을 노출하지 않으므로 TOML 파싱·project 설정 로딩·명시적 메시지 위임 증거와 구분한다.

제품 코드/화면/엔진/베타/PG/Excel/사용성/UX 횟수/절감률 검증은 이번에 실행하지 않았다. 제품 변경 없는 운영 설정 검증이다. 기존 검증을 이번 실행으로 세지 않는다. Spark 사용·새 플러그인·가격·새 유료 자원·push·배포 없음.

**다음 한 단위:** FLOW-01 — 기존 RP01/RP02의 같은 검사로 해소 확인과 실제 베타 사용자 행동 측정. 이번에는 미승인·미실행이다.
