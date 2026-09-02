# M4-A.5 Formula Audit Evaluation Report

## 판정

`CONDITIONAL GO — M4-B internal beta was separately approved; relative-cost limit remains`

정확도·정상 예외·안전·설명 가능성 게이트는 합성 코퍼스에서 통과했다. 다만 M4 활성화 시간이 기본 스캔의 2배를 넘는 상대 성능 게이트를 세 규모 모두에서 넘었다. M4-B 내부 베타 노출 여부는 이 시간 비용을 사람이 승인한 뒤에만 결정할 수 있다.

### M4-A.6 계약 준비 업데이트

M4-A.6 시점에는 이 `CONDITIONAL GO`를 계약·수동 검토 준비로만 수용했다. 이후 제품 소유자의 별도 M4-B 승인으로, 기본 결과와 분리된 audit envelope·서버 gate·불변성 회귀 테스트·내부 UI를 구현했다. 현재 M4-B 구현 상태와 재측정 성능은 `docs/28_M4B_PRODUCT_CONTRACT.md`와 `docs/10_PROGRESS.md`를 기준으로 하며, 이 평가 보고서의 합성 품질 판정 자체는 상용 정확도 주장이 아니다.

## 기준선과 코퍼스

- Git commit hash: 없음. 이 작업공간은 Git 저장소가 아니다.
- 실행 기준: 2026-09-01, scanner `0.1.3`, rule set `2026.09.4`, `FORMULA_PATTERN_AUDIT_ENABLED=false`.
- 코퍼스: 합성 workbook 5개 + 성능 workbook 3개, 라벨 case 40개.
- 지원 탐지 case: 24개. `FORMULA_PATTERN_OUTLIER` 16개, `FORMULA_PATTERN_GAP` 8개.
- 정상·제외 case: 12개, 미지원 case 3개, 절단 스캔 case 1개.

라벨은 `manifest.json`에 고정한다. `UNSUPPORTED` 및 `SKIP_TRUNCATED`는 accuracy 분모가 아니라 안전 경계로 측정했다.

## 탐지 결과

| 지표 | 결과 |
| --- | ---: |
| True positive / False positive / False negative | 24 / 0 / 0 |
| Precision / Recall / F1 | 1.00 / 1.00 / 1.00 |
| 정상 workbook 무경고 | 1 / 1 (100%) |
| 정상 workbook당 false positive | 0.00 |
| 명시적 제외 후보 | 0 |
| 미지원 구조 후보 | 0 |
| finding key 반복 안정성 | 통과 |
| 근거·정상 가능성·한계 존재 | 통과 |

이 수치는 고정된 합성 사례에만 적용된다. 일반 업무 통합문서의 정확도나 업무 수식의 정답을 뜻하지 않는다.

### 탐지 유형별 결과

- Outlier 16/16: 함수, 참조 시트, 상대 참조, 절대 참조, 범위 끝 위치 및 혼재 사례.
- Gap/constant 8/8: 수식 셀이 상수로 바뀐 경우와 빈 셀 경우.
- 정상 예외: 소계·총계·헤더·빈 구분 행·영역 시작/끝·수동 조정·정상 상대 참조·병합·Table·여러 정상 구간·clean case에서 후보 0건.

대표 false positive와 false negative는 이번 코퍼스에서 없었다. 표식 없는 의도적 예외 계산과 지원하지 않는 수식 문법은 여전히 탐지 누락될 수 있으며, 이는 오류 확정이 아닌 보수적 후보 설계의 한계다.

## 설명과 정보보호

각 candidate는 원문 수식·셀 값 없이 subtype, 근거 요약, 주변 패턴/대상 패턴 요약, 비교 위치, 이웃 수, 정상 가능성, 현재 한계를 제공한다. subtype을 확실히 알 수 없는 `GENERIC_PATTERN_DRIFT`는 M4-B 공개 보류 대상이다.

`local-evaluation/` 결과는 case/finding 참조와 집계만 저장하며 filename, sheet, cell, finding key, formula, value를 저장하지 않는다. 수동 정답은 자동 생성하지 않는다.

## 성능

현 개발 PC에서 각 workload를 세 번 실행했다. 메모리는 Python `tracemalloc`이 tokenizer 측정 자체를 크게 왜곡하므로 기록하지 않았고, 별도 의존성을 추가하지 않았다.

| 수식 셀 | 기본 M2 평균 | M4 활성 평균 | 추가 시간 | 비율 |
| ---: | ---: | ---: | ---: | ---: |
| 1,000 | 0.0373초 | 0.0950초 | 0.0577초 | 2.545× |
| 10,000 | 0.3688초 | 0.9258초 | 0.5570초 | 2.510× |
| 30,000 | 1.2455초 | 2.7376초 | 1.4920초 | 2.198× |

파일 손상·스캔 실패·절단은 없었다. 대형 파일에서 행별 요약/수동 예외 판별이 비선형으로 느려지는 구현 결함을 발견해, 탐지 조건을 바꾸지 않고 한 번의 행 순회로 수정했다. 위 수치는 수정 후 결과다. 상대 비율 2배 기준은 모두 초과했으므로 성능 게이트는 실패로 남긴다.

## 경고 분석

- React `act(...)`: 우리 테스트 환경 설정 문제였다. `IS_REACT_ACT_ENVIRONMENT`를 설정해 재검증 후 경고가 사라졌다.
- ZipFile cleanup: `.xlsm` 정적 검사에서 필요 없는 VBA 보존용 임시 ZIP을 만들던 경로를 제거하고 source stream도 명시적으로 닫았다. 전체 API suite를 unraisable warning 오류 승격으로 통과시켰다.
- Starlette TestClient: FastAPI `0.141.1` / Starlette `1.6.0` / httpx `0.28.1` 조합의 의존성 deprecation 경고다. 런타임 파일 손상 징후는 없고 현 milestone에서 의존성 대규모 변경은 하지 않는다. 호스팅 전 의존성 호환성 업데이트에서 재검토한다.

## 공개 가능성과 보류

- 내부 베타 후보: 24개 합성 case로 검증된 outlier와 gap/constant 두 rule class. 단, 결과는 여전히 후보이며 자동수정·업무 정답을 뜻하지 않는다.
- 공개 보류: `GENERIC_PATTERN_DRIFT`, 지원하지 않는 수식 문법, 표식 없는 의도적 예외 계산, 그리고 모든 M4-B 사용자 화면.
- 현재 공개 결과: 없음. M4-A flag와 M2.5 기본 Results UI는 그대로 비활성/미노출이다.

## 사람이 M4-B 전에 결정할 사항

1. 내부 베타에서 1.49초(3만 수식) 절대 증가와 2.2~2.5배 상대 증가를 허용할지.
2. 승인 시에도 `GENERIC_PATTERN_DRIFT`를 숨기고 검증된 subtype만 노출할지.
3. 호스팅 후 M3 Round 1/2의 실제 사용자 이해도 검증을 다시 시작할 시점.

M4-B는 이번 결과로 자동 시작하지 않는다.
