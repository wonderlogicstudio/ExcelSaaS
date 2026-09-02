# Formula Pattern Audit — M4-A

## 목적과 상태

M4-A는 Excel 수식의 업무적 정답을 판정하지 않는다. 같은 열의 연속된 수식 영역에서 주변과 다른 **수식 패턴 이상 후보**만 찾는, 기본 비활성 내부 엔진 프로토타입이다.

`formula_pattern_audit_enabled`는 API 설정의 기본값이 `false`다. 따라서 현재 무료 Results UI·샘플 fixture·기본 업로드 결과에는 M4 Finding이 포함되지 않는다. M4-B 승인 전에는 사용자용 정식 표시를 추가하지 않는다.

## 구현한 탐지 대상

1. `FORMULA_PATTERN_OUTLIER`
   - 같은 열에서 연속된 수식 영역 안의 한 수식이 주변의 지배적 정규화 패턴과 다를 때 후보를 만든다.
2. `FORMULA_PATTERN_GAP`
   - 같은 열에서 충분한 주변 수식 패턴 사이의 한 셀이 비어 있거나 상수일 때 후보를 만든다.

두 경우 모두 최소 세 개의 비예외 주변 수식이 같은 정규화 패턴을 보여야 하며, 대상 셀은 영역의 시작·끝이 아니어야 한다. 이는 함수 유형, 참조 시트, 상대·절대 참조, 범위 끝 위치 차이를 별도 규칙으로 늘리지 않고 ‘패턴 이탈’의 근거로 다루는 의도적인 제한이다.

## 정규화 방식과 근거

수식은 `openpyxl` tokenizer로 제한적으로 해석한다. 지원하는 A1 셀·범위 참조는 수식 셀을 기준으로 상대 위치 표기(`C[+n]R[+n]`)로 바꾸고, 절대 참조와 참조 시트는 구분을 보존한다. 이후 정규화 문자열은 일방향 hash ID로만 남긴다.

M4 Finding에는 원문 수식이나 실제 셀 값을 넣지 않고 다음만 담는다.

- pattern type, formula region, dominant/current pattern ID
- 동일 패턴 주변 수식 수와 비교 위치
- 탐지 근거와 현재 한계

M4-A.5에서는 기존 signature에서 확실히 구분할 수 있는 경우에만 value-free subtype과 근거 요약을 추가한다. 함수·참조 시트·참조 셀·상대/절대 참조·범위 끝 위치·상수/빈 셀을 설명할 수 있으며, 확실하지 않으면 `GENERIC_PATTERN_DRIFT`로 남긴다. 이 요약에도 원문 수식, 실제 셀 값, 외부 파일명, 대체 수식은 넣지 않는다.

이 근거는 ‘주변 수식과 다르다’는 설명용이며, 교체할 수식이나 수정안을 생성하지 않는다.

## 의도적으로 탐지하지 않는 대상

- 수식 계산 결과, 캐시 값, 업무 규칙, 회계·통계 모델의 정답
- 배열, Excel Table, 외부 통합문서, 이름 범위 등 M4-C 정규화가 확실히 처리하지 않는 수식
- 병합 셀, Excel Table 영역, 숨김 행, 제목·헤더, 시작·끝 행
- `소계`, `합계`, `총계`, `조정`, `보정`, `Adjustment`, `Manual` 등 요약·수동 계산 표식이 있는 행
- `scan_truncated = true`인 파일 전체

M4-C는 숫자·텍스트·논리·오류 리터럴을 실제 값이 아닌 token category로만 정규화해, `IF`, `IFERROR`, `SUMIF/SUMIFS` 같은 반복 수식을 비교할 수 있다. 리터럴의 값·의미·업무적 적절성은 비교하거나 반환하지 않는다. 다만 `SUM`·`AVERAGE`의 직접 상수 인수는 의도된 수동 조정일 가능성이 있어 별도 quality gate 전까지 미지원으로 유지한다. 위 제외는 여전히 오탐을 줄이는 대신 탐지 누락을 만든다.

## M4-C 통합 최종 검증 상태

`scripts/verify-m4c.ps1`는 두 개의 checksum-verified 합성 팩을 함께 실행하고, 기본 진단 불변성·finding key 안정성·수식/셀 값 비노출도 함께 확인한다. 2026-09-01 실행은 20개 파일에서 위치·상위 Rule·subtype 72/72, unexpected 0, 비대상 normal-range false positive 0, 정상 통제 0, 스캔 실패 0, 기본 결과 회귀 0을 기록했다.

이 실행의 상태는 `BLOCKED`다. 추가 팩 원본 manifest가 `배부계산!E13`과 `배부계산!F22`를 expected target과 normal exception range에 동시에 넣었기 때문이다. 엔진의 탐지 결과를 맞추기 위해 source label을 변경하지 않으며, checksum-verified 수정본을 받은 뒤에만 M4-C Completed 판정을 다시 시도한다. 이 결과는 상용 정확도 주장이 아니며, 실제·비식별 파일 검증도 대체하지 않는다.

## 분류와 한계

M4-A Finding은 `EXPERT_REVIEW`를 사용하지만, guidance는 `DEEP_VALIDATION_REQUIRED`와 `CURRENTLY_NOT_SUPPORTED`로 표시된다. 이는 자동수정·수정 후보·수정본 생성이 현재 제공되지 않는다는 뜻이다. 패턴 후보는 오류 확정, 손실, 업무적 부정확성, 수정 가능성을 의미하지 않는다.

## 합성 회귀 검증

`apps/api/tests/test_formula_patterns.py`는 다음을 검증한다.

- 함수 유형, 참조 시트, 상대참조, 범위 끝 위치가 다른 단일 수식 후보
- 반복 수식 영역의 상수 덮어쓰기·수식 누락 후보
- 헤더/경계, 소계 행, 완전한 빈 구분 행, 병합 영역, Excel Table의 비탐지
- 기본 비활성 상태, value-free API evidence, finding key 안정성, 기존 guidance 호환성

실제 회사 파일은 사용하지 않는다. 합성 테스트 통과는 실제 업무 파일에서의 정확도·결제 가치·false-positive 비율을 증명하지 않는다.

## M4-B 전에 결정할 사항

- 호스팅된 외부 사용자에게 M4 후보를 어떤 카피·우선순위·기본 펼침 상태로 보일지
- 실제 합성·안전하게 익명화된 코퍼스에서 허용 가능한 false-positive 기준
- 패턴 ID·비교 위치가 사용자에게 충분한 근거인지, 원문 수식 공개가 별도 프라이버시 위험을 만드는지
- 정밀검증과 향후 검토 표시본·Approved Repair에 M4 후보를 어떻게 연결할지
- M4-A.5 성능 게이트의 2.2–2.5× 상대 시간 증가를 제한된 내부 베타에서 허용할지
- `GENERIC_PATTERN_DRIFT`를 계속 비공개로 둘지
- `docs/25_FORMULA_AUDIT_EVALUATION_REPORT.md`의 `CONDITIONAL GO`를 M4-B 승인으로 바꿀지 여부

## M4-A.6 계약 준비 결과

제품 소유자는 `CONDITIONAL GO`를 M4-B 내부 베타 **계약 준비**로만 수용했다. M4-B 화면·API·공개 노출은 아직 승인되지 않았다.

- 현재 feature flag를 단순히 켜면 M4 후보가 기본 finding collector에 더해지고, 기본 risk score·summary·quote·Results 목록에 섞일 수 있다. 이는 내부 베타 계약에 맞지 않으므로 M4-B 구현 시 별도 `formula_audit` envelope와 기본 결과 불변성 회귀 테스트가 필요하다.
- 내부 베타는 기본 스캔이 완료되고 `scan_truncated=false`이며 수식 셀이 1~30,000개인 경우에만 선택적으로 검토한다. 현재 동기식 API에서는 실제 진행률을 표시하지 않고 불확정 분석 상태만 허용한다.
- `FORMULA_PATTERN_OUTLIER`와 `FORMULA_PATTERN_GAP`만 잠재 내부 베타 대상이다. `GENERIC_PATTERN_DRIFT`, 미지원 문법, 계산·업무 판단은 비공개로 유지한다.
- `ABSTAINED_INSUFFICIENT_EVIDENCE`, `SKIPPED_UNSUPPORTED_STRUCTURE`, `SKIPPED_TRUNCATED`, `FAILED`는 규칙의 개발 상태가 아니라 실행 결과이며 후보를 만들지 않는다.
- 상세 계약은 `docs/28_M4B_PRODUCT_CONTRACT.md`, 수동 합성 검토 양식은 `docs/29_M4B_MANUAL_REVIEW_CHECKLIST.md`를 따른다.

## M4-D Release Candidate 기록

현재 구현은 `m4-formula-audit-rc1` 로컬 릴리스 후보입니다. 기본 무료 진단과 별도로, 내부 개발·베타 환경에서만 사용자가 같은 브라우저의 파일을 다시 전송해 두 규칙(`FORMULA_PATTERN_OUTLIER`, `FORMULA_PATTERN_GAP`)을 선택 실행합니다. 이 감사 결과는 기본 Finding, 위험 점수, 참고 가격, 수정 가능성 요약, CSV, 재검사 결과에 섞이지 않습니다.

통합 M4-C 평가는 20개 합성 파일에서 위치·상위 Rule·subtype 72/72, 예상 밖 후보 0, 비대상 정상 범위 후보 0, 정상 통제 후보 0, 기본 결과 회귀 0을 확인했습니다. 추가 팩의 원본 답안지에는 `배부계산!E13`/`D6:I13`, `배부계산!F22`/`D22:I29`의 두 target/normal 중복이 남아 있습니다. 제품 소유자는 이를 `M4C-2026-09-02-source-label-conflict`라는 좁은 예외로 승인했으며, 원본 label·checksum은 변경하지 않았습니다. 이 예외는 다른 실패를 허용하지 않으며, 수정된 상위 답안지를 받으면 교체해야 합니다.

감사 한도는 설정으로 제어됩니다(시트 200개, 수식 셀 30,000개, 후보 120개 기본값). 한도를 넘으면 부분 후보를 반환하지 않고 명시적으로 생략하며, 기본 무료 진단은 유지됩니다. M4는 아직 호스팅·공개 기능이 아니고 자동수정, 정답 수식 제안, 수정본 XLSX, 결제, 계정, 서버 피드백 저장을 제공하지 않습니다. 상세 운영·호스팅 전제는 `docs/32_M4D_RELEASE_CANDIDATE.md`부터 `docs/36_M4D_FINAL_RELEASE_CANDIDATE_REPORT.md`까지를 따릅니다.
