# Formula Audit Quality Gate — M4-A.5

## 목적과 경계

M4-A.5는 M4-A의 두 내부 수식 패턴 후보를 평가하는 품질 게이트다. 새 진단 규칙, 계산 결과 검증, 업무 규칙 검증, 자동수정, 수정 수식, XLSX 출력, M4-B 사용자 화면은 구현하지 않는다.

평가 결과의 precision·recall·F1은 **합성 라벨 코퍼스 기준**이다. 실제 업무 파일 전체의 정확도, 수식의 업무적 정답, 사용자 이해도, 결제 가능성을 보장하거나 추정하지 않는다.

## 기준선

이 작업공간에는 Git 메타데이터가 없다. 기준선은 2026-09-01, scanner `0.1.3`, rule set `2026.09.4`, `FORMULA_PATTERN_AUDIT_ENABLED=false`, `samples/m4-evaluation/`과 성공한 `scripts/verify.ps1`으로 식별한다.

M4-A와 M2.5 Results UX는 기본 비활성 상태를 유지한다. M4 finding은 기본 무료 결과나 M4-B 화면에 표시하지 않는다.

## 재현 가능한 합성 코퍼스

`scripts/generate_m4_evaluation_corpus.py`가 다음 자산과 `manifest.json`을 재생성한다.

- 지원 대상 24개: 함수·참조 시트·상대 참조·절대 참조·범위 끝 위치 이탈, 수식 셀이 상수로 바뀐 후보, 빈 수식 셀 후보, 혼재 후보.
- 정상·명시적 제외 12개: 소계·총계·헤더·빈 구분 행·영역 경계·수동 조정 행·정상 상대 참조·병합 셀·Excel Table·여러 정상 구간·정상 파일.
- 미지원 3개: `SUM`·`AVERAGE`의 직접 상수 인수, 외부 통합문서 문법, 이름 범위.
- 절단 스캔 1개: M4-A 전체 생략을 확인한다.
- 성능 파일 3개: 약 1,000 / 10,000 / 30,000 수식 셀.

모든 파일과 값은 합성이다. 실제 회사 파일·개인정보는 프로젝트에 넣지 않는다.

## 라벨과 측정 원칙

각 case는 `workbook_id`, `sheet`, `cell`, 기대 탐지·패턴 유형·subtype·처리, 정상 예외 이유, 메모를 가진다.

- `SHOULD_DETECT` / `EMIT_CANDIDATE`: precision·recall의 지원 대상이다.
- `SHOULD_NOT_DETECT` / `SUPPRESS_EXCLUDED` 또는 `CLEAN_PASS`: 정상·제외 사례다.
- `UNSUPPORTED` / `SKIP_UNSUPPORTED`: 정확도 분모에서 제외하며 후보가 나오면 별도 안전 실패다.
- `SKIP_TRUNCATED`: 정상 무경고가 아니라 검사 생략이며 정확도 분모에서 제외한다.

엔진의 실제 결과가 라벨과 다르면 라벨을 맞추지 않고 false positive 또는 false negative로 기록한다. 안정성은 동일 파일을 두 번 스캔해 rule·location finding key 순서를 비교한다.

## 초기 M4-B 내부 베타 게이트

다음은 상용 정확도 보장이 아니라 M4-B 검토 진입 판단 기준이다.

- 지원 대상 recall 85% 이상, 전체 precision 90% 이상
- 정상 통합문서 무경고 80% 이상, 정상 통합문서당 평균 false positive 1건 이하
- 소계·총계·헤더·경계·병합·Table 등 명시적 제외 구조에서는 후보 0건
- 미지원 구조 후보 0건, 파일 손상·스캔 오류 0건
- 모든 candidate에 근거·정상 가능성·현재 한계가 있고 finding key가 안정적
- 기존 M0~M2/M2.5 회귀 0건
- 소·중·대형 파일을 동일 환경에서 세 번씩 측정하고, M4 활성화 시간이 기본 스캔의 2배를 넘으면 사람 검토가 필요하다.

상대 성능 기준은 매우 빠른 기본 스캔에서는 작은 절대 시간 증가도 크게 보일 수 있다. 따라서 초과 시 숨기지 않고 `CONDITIONAL GO` 또는 `NO-GO`로 기록하며, 사람이 내부 베타 허용 여부를 결정한다.

## 설명 가능한 근거

M4-A.5는 탐지 조건을 넓히지 않고 기존 private normalized signature에서 다음의 선택적 value-free summary를 만든다.

- `pattern_subtype`: 함수·참조 시트·상대/절대 참조·범위 끝 위치·상수/빈 셀 또는 `GENERIC_PATTERN_DRIFT`
- `evidence_summary`, `dominant_pattern_summary`, `current_pattern_summary`
- `comparison_locations`, `neighbor_count`, `normal_case_possibility`, `current_limitations`

원문 수식, 셀 값, 외부 파일명, 대체 수식은 response·평가 결과·피드백에 저장하지 않는다. 근거만으로 subtype을 확실히 분류할 수 없으면 `GENERIC_PATTERN_DRIFT`를 유지하며, 이 subtype은 M4-B 공개 보류 대상이다.

## 로컬 비민감 파일 수동 검토

`local-evaluation/`은 `.gitignore`에 포함된다. 비민감하거나 익명화한 파일만 이 폴더에 둘 수 있다.

```powershell
.\apps\api\.venv\Scripts\python.exe scripts\evaluate_formula_patterns.py --local-dir local-evaluation
```

출력은 `LOCAL-001` 같은 case/finding 참조와 집계 수만 포함한다. 파일명·sheet·cell·finding key·셀 값·수식 원문은 저장하지 않는다. `samples/m4-evaluation/local-review-template.csv`의 판정값은 `실제 이상 후보`, `정상 패턴`, `판단 불가`, `업무 규칙 확인 필요` 중 하나만 사용한다. 로컬 파일에는 자동 정답을 만들지 않는다.

## 실행

```powershell
.\apps\api\.venv\Scripts\python.exe scripts\generate_m4_evaluation_corpus.py
.\apps\api\.venv\Scripts\python.exe scripts\evaluate_formula_patterns.py --performance-runs 3
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\verify.ps1
```

합성 평가 결과는 `artifacts/m4-a5/evaluation.json`과 `evaluation.csv`에 쓴다. M4-B는 이 결과가 어떻든 제품 소유자의 별도 승인 없이는 시작하지 않는다.
