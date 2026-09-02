# M4-B Internal Beta Product Contract

## 상태

`IMPLEMENTED — M4-B INTERNAL BETA — DESKTOP/MOBILE VISUAL CAPTURE PENDING`

M4-A.5의 `CONDITIONAL GO`와 M4-A.6 계약, 제품 소유자가 보고한 합성 수동 검토 완료를 바탕으로 제한된 내부 베타를 구현했다. 이는 공개 기능, 새 탐지 규칙, 자동수정, 유료 기능 또는 M4-C의 시작 승인이 아니다.

## 근거와 해석

- 고정 합성 코퍼스 40개 case에서 `precision=1.00`, `recall=1.00`, `F1=1.00`이었다.
- 이 결과는 엔진과 같은 개발 과정에서 만든 현재 합성 사례에만 적용된다. 실제 업무 파일의 상용 정확도, 업무 수식의 정답, 결제 가치, 실제 false-positive 비율을 증명하지 않는다.
- 독립적으로 작성한 합성 holdout 사례와, 향후 별도 개인정보 승인 아래에서만 가능한 비민감 사례 검토가 필요하다. M4-A.6에서는 실제 회사 파일·개인정보 파일·사용자 반응을 사용하거나 수집하지 않는다.
- 분리된 내부 감사 경로를 다시 측정한 결과, 1k / 10k / 30k 수식 셀의 평균 추가 시간은 0.0333초 / 0.4320초 / 1.2835초이고 비율은 1.771× / 2.158× / 2.062×였다. 절대 시간만으로 허용 여부를 판단하지 않으며, 10k·30k의 2× 초과 상대 증가를 계속 기록·검토한다.

## 베타 대상·접근 경계

M4-B는 공개 웹 기능이 아니다. 계정 기능이 없으므로 브라우저의 숨은 플래그나 CSS 숨김만으로 내부 베타를 보호했다고 주장할 수 없다.

- `POST /v1/formula-audits`는 `APP_ENV=development|internal_beta` **및** `FORMULA_PATTERN_AUDIT_ENABLED=true`를 모두 요구하며, 그 밖의 환경에서는 `404 FORMULA_AUDIT_NOT_AVAILABLE`로 fail-closed 한다.
- 브라우저는 `VITE_FORMULA_AUDIT_INTERNAL_BETA_ENABLED=false`가 기본이다. 이 값은 내부 화면 노출 제어일 뿐 접근 제어 수단이 아니며, 공개 사이트에는 CTA·선택 API·가격·자동수정 표현을 노출하지 않는다.
- 내부 화면의 피드백은 `도움이 됨 / 오탐 의심 / 설명 부족` 카테고리만 현재 브라우저의 localStorage에 저장한다. 메모 입력, 피드백 API, 서버 저장, 분석 추적, 고객 파일 데이터 수집은 추가하지 않는다.

## 허용 규칙과 내부 베타 보류 규칙

내부 베타에서 검토 가능한 rule code는 다음 둘뿐이다.

| rule code | quality state | 허용 evidence subtype | 내부 베타 표현 |
| --- | --- | --- | --- |
| `FORMULA_PATTERN_OUTLIER` | `PROTOTYPE / CONDITIONAL / INTERNAL_ONLY` | 함수·참조 시트·참조 셀·상대/절대 참조·범위 경계가 **확실히** 구분된 경우 | 주변 수식과 다른 패턴 후보 |
| `FORMULA_PATTERN_GAP` | `PROTOTYPE / CONDITIONAL / INTERNAL_ONLY` | 상수 덮어쓰기 후보, 빈 셀 후보 | 수식 영역의 상수/빈 셀 후보 |

다음은 내부 베타 결과를 만들지 않거나 노출하지 않는다.

- `GENERIC_PATTERN_DRIFT`
- 현재 정규화가 지원하지 않는 수식 문법, 외부 통합문서 수식, 이름 범위, 배열, Excel Table 구조
- `scan_truncated=true`인 파일 전체
- 계산 결과·캐시 값·업무 규칙·재무·통계 모델·안전한 대체 수식·자동 수정 판단

함수·참조 시트·참조 셀·상대/절대 참조·범위 이탈은 `FORMULA_PATTERN_OUTLIER`의 evidence subtype이며 독립 rule code·별도 경고 수·별도 가격 요인이 아니다.

## 기본 무료 진단과의 불변성 계약

기본 `scan_workbook()`은 이제 M4 후보를 호출하지 않는다. 기본 `ScanResult.findings`, 요약, 위험 점수, 복잡도, 견적, 수리 가능성 집계와 CSV는 무료 진단만으로 완결한다.

선택형 M4 결과는 별도 endpoint의 `FormulaAuditResult`에만 담긴다. 이 결과는 후보 목록·실행 상태·수식 셀 수·검사 시트/후보 영역 수·한계·처리 시간을 가지며, 기본 결과 또는 현재 가격에 영향을 주지 않는다. API 회귀 테스트는 감사 요청 전후의 기본 finding(실행별 ID 제외), workbook 요약, 위험 점수, 견적, 한계가 동일함과 후보가 기본 목록에 섞이지 않음을 확인한다.

계약 기준: **기본 위험 점수에 반영하지 않음**. M4 후보는 현재 견적·수정 가능 개수·무료 결과 요약을 바꾸지 않는다.

### 최소 응답 계약 — 구현됨

기존 `POST /v1/scans` 호환성을 유지하기 위해 별도 내부 endpoint `POST /v1/formula-audits`를 사용한다.

```text
FormulaAuditResult {
  status: COMPLETED | ABSTAINED_INSUFFICIENT_EVIDENCE |
          SKIPPED_TRUNCATED | SKIPPED_FORMULA_LIMIT |
          SKIPPED_UNSUPPORTED_STRUCTURE | FAILED
  formula_cell_count: integer
  audited_sheet_count: integer
  audited_formula_region_count: integer
  candidates: Finding[]
  limitations: string[]
  elapsed_ms: integer
  scanner_version: string
  rule_set_version: string
}
```

이 envelope는 원문 수식, 셀 값, 외부 파일명, 대체 수식, 자동수정 계획을 포함하지 않는다. `Finding` 카드의 일반 구조는 재사용할 수 있지만, M4-A.5의 `pattern_subtype`, 근거 요약, 비교 위치, 정상 가능성, 한계가 들어 있는 optional evidence 타입을 프런트엔드도 완전하게 수용해야 한다.

## 실행 결과 상태

다음은 규칙의 `current_status`, `quality_gate_status`, `exposure_status`와 별개인 **한 번의 감사 실행 결과**다.

| 실행 상태 | 의미 | 후보 생성 |
| --- | --- | --- |
| `NOT_REQUESTED` | 사용자가 내부 베타 검사를 요청하지 않음 | 없음 |
| `COMPLETED` | 지원 범위 내 분석 완료. 후보가 없을 수도 있음 | 조건부 |
| `ABSTAINED_INSUFFICIENT_EVIDENCE` | 비교할 수 있는 충분한 주변 패턴이 없어 판단을 유보 | 없음 |
| `SKIPPED_TRUNCATED` | 기본 스캔 범위가 잘려 M4 전체를 생략 | 없음 |
| `SKIPPED_FORMULA_LIMIT` | 검증된 내부 베타 수식 셀 한도를 초과 | 없음 |
| `SKIPPED_UNSUPPORTED_STRUCTURE` | 지원하지 않는 구조 때문에 안전하게 유보 | 없음 |
| `FAILED` | 감사 처리 오류. 기본 진단 결과는 유지 | 없음 |

`ABSTAINED_INSUFFICIENT_EVIDENCE`와 `SKIPPED_UNSUPPORTED_STRUCTURE`는 오류나 clean result가 아니다. 모두 “이번 정밀검사에서 판단하지 않음”으로 보여야 하며, 근거가 부족한 수식을 억지로 후보화하지 않는다.

## 내부 베타 사용자 흐름 — 구현됨

1. 사용자가 먼저 기본 무료 진단을 완료한다.
2. 내부 베타 화면은 기본 결과가 완전하고 수식 셀이 1~30,000개인 경우에만 실행 버튼을 활성화한다. 이 클라이언트 precondition은 서버 파일 보관 또는 과거 scan 상태 검증을 뜻하지 않는다.
3. 사용자가 명시적으로 실행을 선택한다. 서버 파일 식별자·재사용 API가 없으므로 같은 브라우저가 보유한 `File`을 다시 전송한다. 서버가 파일을 보관하거나 자동 삭제한다고 주장하지 않는다.
4. 현재 API는 동기식이다. 실제 진행률·퍼센트·남은 시간을 만들지 말고, 완료 전에는 불확정 “분석 중” 상태만 표시한다.
5. 결과는 기본 무료 finding 목록과 분리된 “수식 패턴 정밀검사 — 내부 베타” 영역에만 표시한다.
6. 사용자는 근거·정상 가능성·Excel 확인 방법·현재 한계를 읽고, 로컬 처리 상태와 값 없는 로컬 피드백을 남길 수 있다.

기본 진단이 `scan_truncated=true`, 수식 셀이 30,000개 초과, 지원 범위 부족, 처리 실패인 경우에는 기본 결과를 그대로 유지하고 M4 후보를 표시하지 않는다. M4 실패는 전체 무료 스캔 실패가 아니다.

## 허용·금지 표현

허용 표현:

- 수식 패턴 이상 후보
- 주변 수식과 다른 패턴
- 사용자 확인 필요
- 업무적으로 정상일 수 있음
- 현재 검사만으로 정답 여부를 판단할 수 없음

금지 표현:

- 잘못된 수식, 확정 오류, 업무 결과가 틀림
- 이 수식은 특정 함수여야 함
- 자동 수정 가능, 수정본 생성 가능
- 안전한 대체 수식 또는 자동 수정 수식

## 성능·보안·회귀 게이트

M4-B에서 아래를 자동화 테스트와 내부 검토로 확인했다.

- 기본 스캔 완료 후에만 eligibility를 판단하고, `scan_truncated=false`와 `formula_count <= 30,000`를 엄격히 적용한다.
- 1,000 / 10,000 / 30,000 수식 셀에서 기본·M4 시간, 절대 추가 시간, 상대 비율을 반복 측정한다. M4-B 분리 경로의 현재 수치(추가 0.0333초 / 0.4320초 / 1.2835초 및 1.771× / 2.158× / 2.062×)를 기준선으로 보존한다.
- M4 비요청 기본 결과는 finding, summary, risk, quote, repair count, limitations의 정규화 비교에서 완전히 동일해야 한다. 분석 ID와 시각처럼 본질적으로 달라지는 값은 제외한다.
- M4 요청·유보·미지원·실패 결과가 기본 무료 결과를 바꾸지 않는지 확인한다.
- raw formula, cell value, filename, sheet/cell, finding key를 서버 로그·평가 산출물·피드백 저장에 남기지 않는다.
- 매크로·수식·외부 연결·VBA·사용자 코드를 실행하지 않고, 파일을 저장·수정하지 않는다.

## UI/API 구현 상태

| 항목 | M4-B 구현 상태 | 경계 |
| --- | --- | --- |
| rule code별 카드 | 별도 접힌 M4 후보 카드 | 기본 Finding 카드에 섞지 않음 |
| 기본 finding 목록 | `ScanResult`에서 M4 호출 제거 | `FormulaAuditResult.candidates`만 사용 |
| 위험·견적·수리 집계 | 감사 후보와 완전 분리 | 기본 점수·가격·CSV 불변 |
| M4 evidence 타입 | optional subtype/요약/비교 위치를 web type에 반영 | `GENERIC_PATTERN_DRIFT`는 표시하지 않음 |
| 실행 상태 | `COMPLETED`, 유보, 생략, 실패를 별도 표시 | 후보 없음은 정확성 보장이 아님 |
| 사용자 처리 상태 | 후보 key 기준, 현재 화면 세션에만 유지 | 기본 상태와 별도 state |
| 피드백 | 내부 화면에서 category-only localStorage | 메모·서버 전송 없음 |

이 구현은 새 탐지 규칙·자동수정·수정본·결제·계정·DB·AI·계산 엔진을 추가하지 않는다.

## M4-C 전 확인 항목

1. 30,000 수식 셀 한도와 재측정된 상대 비용(중형·대형 2× 초과)을 내부 베타에서 계속 수용할지
2. 격리된 internal-beta 운영 환경의 배포·접근 절차를 별도 승인할지
3. 독립 합성 holdout 검증의 범위와, 실제 비민감 파일 검토가 필요해질 경우의 별도 개인정보 승인을 결정할지
4. 외부 M3 사용자 검증을 호스팅 후 언제 재개할지

M4-B의 내부 베타 코드와 자동 검증은 완료했다. 실제 데스크톱·모바일 캡처는 브라우저 런타임 부재로 보류되었으며, M4-C·자동수정·결제·새 탐지 규칙은 시작하지 않는다.
