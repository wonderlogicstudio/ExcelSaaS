# M4-B Manual Review Checklist — Synthetic Cases Only

## 상태

`PRODUCT OWNER REPORTED COMPLETED — detailed observations are not stored here`

제품 소유자는 대표 합성 파일 5개의 수동 확인을 완료했다고 보고했다. 개별 검토자 ID·시각·관찰 문구는 전달받지 않았으므로, 이 저장소는 이를 자동 평가 결과나 수치화된 수동 검토 기록으로 바꾸지 않는다. 아래 양식은 다음 내부 재검토에도 사용할 수 있으며, 실제 회사 파일·개인정보 파일·사용자 반응은 사용하지 않는다.

## 재현 기준

- 기준일: 2026-09-01
- scanner / rule set: `0.1.3` / `2026.09.4`
- corpus generator: `scripts/generate_m4_evaluation_corpus.py`
- expected labels: `samples/m4-evaluation/manifest.json`
- automatic evaluator: `scripts/evaluate_formula_patterns.py --performance-runs 3`
- M4 상태: `FORMULA_PATTERN_OUTLIER`, `FORMULA_PATTERN_GAP`만 내부 프로토타입이며 기본 비활성

검토 전에 합성 자산을 다시 만들고 자동 평가가 통과하는지 확인한다.

```powershell
.\apps\api\.venv\Scripts\python.exe scripts\generate_m4_evaluation_corpus.py
.\apps\api\.venv\Scripts\python.exe scripts\evaluate_formula_patterns.py --performance-runs 3
```

Excel에서만 수식을 확인하고 파일을 저장하지 않는다. 이 체크리스트는 M4-B UI 검증이 아니라 합성 workbook·기대 라벨·정적 감사 근거의 수동 교차 확인이다.

## 공통 확인 절차

1. 지정한 합성 `.xlsx` 파일을 Excel에서 연다.
2. 지정 Sheet와 Cell로 이동해 수식 표시줄과 같은 열의 주변 수식을 확인한다.
3. “후보”가 업무 오류 확정이나 자동 수정 지시가 아니라는 점을 유지한다.
4. `manifest.json`의 case ID, rule code, subtype, expected action과 비교한다.
5. 아래의 실제 관찰 결과를 직접 기입한다. 실행하지 않았으면 빈 칸으로 둔다.

## 대표 합성 사례 5개

### MR-01 — 정상 수식 패턴

- 파일: `samples/m4-evaluation/normal-exceptions.xlsx`
- manifest case: `clean`
- 확인 위치: `Clean` 시트 `C4`
- 의도된 상태: 주변 수식 패턴이 일관되고 이상 후보가 없음
- 정상 예외: 이 파일에는 소계·총계·헤더·병합·Table 같은 별도 제외 사례도 포함되지만, 이 사례의 기준 위치는 `Clean!C4`임
- 기대 결과: `CLEAN_PASS`, M4 후보 0건
- Excel에서 확인: `C4`와 인접 수식이 동일한 역할·참조 이동을 유지하는지 확인

| 실제 검토 일시 | 검토자 ID | 주변 수식 확인 | 기대 결과와 일치 | 실제 관찰 결과 | 추가 메모 |
| --- | --- | --- | --- | --- | --- |
|  |  | [ ] 예 [ ] 아니오 | [ ] 예 [ ] 아니오 |  |  |

### MR-02 — 함수 패턴 이탈 후보

- 파일: `samples/m4-evaluation/detected-patterns.xlsx`
- manifest case: `functiondrift-1`
- 확인 위치: `FunctionDrift` 시트 `C4`
- 의도적으로 삽입된 이상: 주변 수식의 지배 함수 패턴과 다른 수식 구조
- 정상 예외: 현재 workbook에는 없음. 실제 업무 파일에서는 서로 다른 함수가 의도된 계산일 수 있음
- 기대 결과: `FORMULA_PATTERN_OUTLIER`, `FUNCTION_PATTERN_DRIFT`, `EMIT_CANDIDATE`
- Excel에서 확인: `C4`와 같은 열의 양쪽/인접 수식을 비교하고, 차이가 실제로 존재하는지 확인. 올바른 대체 수식은 판단하지 않음

| 실제 검토 일시 | 검토자 ID | 주변 수식 차이 확인 | 기대 결과와 일치 | 실제 관찰 결과 | 추가 메모 |
| --- | --- | --- | --- | --- | --- |
|  |  | [ ] 예 [ ] 아니오 | [ ] 예 [ ] 아니오 |  |  |

### MR-03 — 상수 덮어쓰기 후보

- 파일: `samples/m4-evaluation/detected-patterns.xlsx`
- manifest case: `constantgaps-1`
- 확인 위치: `ConstantGaps` 시트 `C4`
- 의도적으로 삽입된 이상: 수식 영역 중간의 한 수식 셀을 상수로 바꾼 구조
- 정상 예외: 실제 업무에서는 수동 조정 값이 의도될 수 있음
- 기대 결과: `FORMULA_PATTERN_GAP`, `CONSTANT_OVERRIDE_CANDIDATE`, `EMIT_CANDIDATE`
- Excel에서 확인: `C4`가 수식이 아니라 상수인지, 인접 수식의 패턴이 충분한지 확인. 상수를 수식으로 바꾸지 않음

| 실제 검토 일시 | 검토자 ID | 상수/주변 수식 확인 | 기대 결과와 일치 | 실제 관찰 결과 | 추가 메모 |
| --- | --- | --- | --- | --- | --- |
|  |  | [ ] 예 [ ] 아니오 | [ ] 예 [ ] 아니오 |  |  |

### MR-04 — 빈 수식 셀 후보

- 파일: `samples/m4-evaluation/detected-patterns.xlsx`
- manifest case: `blankgaps-1`
- 확인 위치: `BlankGaps` 시트 `C4`
- 의도적으로 삽입된 이상: 수식 영역 중간의 한 셀이 비어 있는 구조
- 정상 예외: 실제 업무에서는 구분 행·보류 행·수동 입력 행이 정상일 수 있음
- 기대 결과: `FORMULA_PATTERN_GAP`, `BLANK_GAP_CANDIDATE`, `EMIT_CANDIDATE`
- Excel에서 확인: `C4`가 비어 있고, 전후 수식이 같은 지배 패턴인지 확인. 빈 셀을 채우거나 수정하지 않음

| 실제 검토 일시 | 검토자 ID | 빈 셀/주변 수식 확인 | 기대 결과와 일치 | 실제 관찰 결과 | 추가 메모 |
| --- | --- | --- | --- | --- | --- |
|  |  | [ ] 예 [ ] 아니오 | [ ] 예 [ ] 아니오 |  |  |

### MR-05 — 여러 후보가 섞인 수식 영역

- 파일: `samples/m4-evaluation/mixed-candidates.xlsx`
- manifest cases: `mixed-outlier`, `mixed-constant`, `mixed-blank`
- 확인 위치: `Mixed` 시트 `C4`, `D4`, `E4`
- 의도적으로 삽입된 이상: 함수 패턴 이탈 후보 1개, 상수 덮어쓰기 후보 1개, 빈 셀 후보 1개
- 정상 예외: 실제 업무 파일에서는 각 차이가 의도된 수동 조정·계산 구간 구분일 수 있음
- 기대 결과:
  - `C4`: `FORMULA_PATTERN_OUTLIER` / `FUNCTION_PATTERN_DRIFT`
  - `D4`: `FORMULA_PATTERN_GAP` / `CONSTANT_OVERRIDE_CANDIDATE`
  - `E4`: `FORMULA_PATTERN_GAP` / `BLANK_GAP_CANDIDATE`
- Excel에서 확인: 세 위치를 주변 수식과 각각 비교하고, 하나의 rule code가 여러 subtype을 설명할 수 있음을 확인. 업무 오류나 수정 방법을 단정하지 않음

| 실제 검토 일시 | 검토자 ID | C4 확인 | D4 확인 | E4 확인 | 기대 결과와 일치 | 실제 관찰 결과 | 추가 메모 |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  | [ ] 예 [ ] 아니오 | [ ] 예 [ ] 아니오 | [ ] 예 [ ] 아니오 | [ ] 예 [ ] 아니오 |  |  |

## 수동 검토 기록 원칙

- 이 문서는 자동 평가 결과를 복사해 “검토 완료”로 채우지 않는다.
- 실제 관찰이 기대 결과와 다르면 outcome을 수정하지 말고, case ID와 이유만 별도 내부 메모로 기록한다.
- 실험 메모에 실제 파일명, 실제 시트/셀, 셀 값, 원문 수식, 고객 정보, 화면 녹화를 넣지 않는다.
- 이 다섯 사례를 확인하더라도 실제 업무 파일 정확도·사용자 이해도·M4-B 공개 승인을 증명하지 않는다.

## 완료 기록 원칙

- 제품 소유자가 완료를 보고한 5개 대표 합성 사례: MR-01~MR-05.
- 개별 관찰 결과가 제공되지 않았으므로, 빈 표를 임의로 채우거나 pass/fail 수치를 추정하지 않는다.
- 실제 회사 파일·개인정보·사용자 반응을 사용하지 않았다는 경계는 계속 유지한다.
- M4-B UI 구현은 이 체크리스트와 별개이며, 새 탐지 규칙을 추가하지 않았다.
