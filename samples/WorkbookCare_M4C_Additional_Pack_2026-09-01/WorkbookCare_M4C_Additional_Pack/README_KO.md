# WorkbookCare M4-C 추가 실무형 샘플 팩

## 구성

- `samples/`: 신규 업무형 합성 Excel 파일 10개
- `expected/M4C_추가팩_예상결과_및_검증가이드.xlsx`: 예상 탐지·정상 예외·성과지표
- `expected/m4c_additional_manifest.json`: 구조화된 전체 정답표
- `expected/m4c_additional_expected_findings.csv`: 예상 탐지 36건
- `expected/m4c_additional_normal_exceptions.csv`: 정상 예외 36건
- `CODEX_EVALUATION_PROMPT.md`: Codex에 전달할 간단한 실행 지시

## 팩 구성

- Calibration: 11~18번 파일
- Holdout: 19~20번 파일
- 예상 M4 Finding: 36건
- 정상 예외: 36건
- Clean Control: `20_다중사업부_정상통제.xlsx` — 예상 M4 Finding 0건

## 1차 합격 기준

1. 예상 위치 36건을 `FORMULA_PATTERN_OUTLIER` 또는 `FORMULA_PATTERN_GAP`으로 탐지
2. 위치와 상위 Rule을 우선 평가
3. Subtype 정확도는 2차 지표
4. 정상 예외 36건에서 False Positive 0건을 목표
5. Clean Control에서 M4 Finding 0건
6. 기존 무료 진단·점수·견적에 영향 없음

## 실행 순서

1. 기존 첫 번째 M4-C 팩 36건 기준선을 고정합니다.
2. 11~18번 Calibration 파일을 실행합니다.
3. 반복 미탐·오탐만 최소 범위에서 수정합니다.
4. 엔진과 Rule Set 버전을 고정합니다.
5. 19번 Holdout 이상 파일을 한 번 실행합니다.
6. 20번 Clean Control 파일을 마지막에 실행합니다.
7. 검증 가이드의 실제 탐지·실제 Rule·실제 Subtype을 입력합니다.
8. `05_성과지표`를 확인합니다.

## 주의

- 샘플 안에는 이상 위치를 표시하지 않았습니다.
- 정답은 검증 가이드와 manifest에만 있습니다.
- Finding은 업무 오류 확정이 아니라 확인할 이상 후보입니다.
- 실제 사용자 파일의 상용 정확도를 증명하는 데이터가 아닙니다.
- 모든 데이터는 합성 데이터입니다.
