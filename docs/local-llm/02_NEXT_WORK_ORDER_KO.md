# 다음 한 단위 작업지시
ID: LOCAL-LLM-FIXTURE01
상태: PROPOSED / 사용자 승인 대기
결과: 모델 없이도 후보·보류·검증 차단의 정오를 판정할 수 있는 합성 시험 계약과 독립 정답표.

## 승인 요청 범위
- 기존 dirty checkout을 보존하고 별도 작업 공간에서 수행. 초기 변경 목록과 기준 commit을 기록.
- [설계](00_DESIGN_KO.md)와 [평가 계약](01_EVALUATION_CONTRACT_KO.md)을 바탕으로 합성18사례/개발·평가 분할 작성.
- 각 사례의 업무 기준·변이·정확 수식/예상값·보류 이유·후보/실행 판정을 분리해 기록.
- 실제 제품 계산기 allowlist와 대조하여 첫 구현 가능한 가장 좁은 수식 집합을 지정. 미지원 조건식을 지원처럼 표시하지 않음.
- 후보 입출력 JSON Schema와 검증 상태 계약 작성. 모델 출력과 정답표 입력의 분리 확인.
- reviewer가 독립 산술/기준으로 oracle 및 설계 신뢰 경계를 검토. freeze manifest 작성.
- 설치 단계의 정확한 runtime release/파일·모델 revision·해시·용량·출처·license·설치 위치·무결성/삭제 방법을 읽기 전용으로 확정. 설치는 하지 않음.

## 허용 파일
새 작업 공간의 docs/local-llm/, samples/local-llm/fixture01/, artifacts/synthetic_validation/local-llm-fixture01/ 전용 증거.
필요한 합성 생성/계약 확인 스크립트는 fixture01 전용 폴더에만 작성.
진행 기록은 docs/09_CURRENT_MILESTONE.md, docs/10_PROGRESS.md, docs/MILESTONE_REVIEW.md, docs/delivery-v3_2/delivery-progress.json에 해당 단위 delta만 추가.
제품 apps/, engine lockfile, 기존 fixture/oracle/보안 설정과 사용자 변경은 수정 금지.
manifest는 자료일 뿐 외부 다운로드 승인이 아니다.

## 역할·순서
PL: 범위 고정·인계·보고. Builder1명: fixture/schema 작성·표적 검사. Reviewer1명: 수정 없이 독립 검토.
전체 대화 fork·중복 시험·상시 대기 agent 없이 순차 수행. 실제 runtime 모델/권한을 보고하고 설정만으로 격리를 주장하지 않음.
리뷰 지적은 최초 작성 후 수정1회까지. 같은 원인 미해결은 보고하고 STOP.

## 합격조건
1. 18사례와 기대 행동·값·출처·분할·해시가 완비되고 독립 정답 검토를 통과.
2. 모델 입력에 정답/변이 힌트가 없으며 정상 예외·정보 부족·미지원은 실행 불가로 계약됨.
3. 첫 허용 규칙 범위와 설치 manifest가 구체적이고 다음 승인에 바로 사용할 수 있음.

## 검사와 종료
fixture 구조/참조/기대값 산술·schema·hash 표적 검사만 수행. 모델 없이 가능해야 함.
전체 제품 회귀/브라우저/Excel 호환성은 NOT_RUN. 실제 XLSX 호환성 통과로 표현하지 않음.
보고: 변경 파일, 명령/exit code, 독립 review 판정, 실패/보류, 구체적 INSTALL01 제안 후 STOP.
설치·다운로드·모델 실행·제품 코드·기존 venv/driver 변경·Git commit/push·배포·고객자료·실결제·새 유료자원은 승인 범위 밖.

## 사용자가 보낼 승인 문구
“LOCAL-LLM-FIXTURE01을 위 작업지시 범위로 승인한다. 기존 변경을 보존하고 빌더와 독립 리뷰어를 분리해 진행한 뒤 결과와 설치 승인안을 보고하고 멈춰라.”
