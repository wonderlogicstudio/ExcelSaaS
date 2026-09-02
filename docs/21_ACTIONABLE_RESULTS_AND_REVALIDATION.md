# Actionable Results & Re-validation — M2.5 Extension

## 1. 무료 진단의 역할

무료 진단은 현재 구현된 정적 규칙으로 파일 구조, 수식 문자열, 외부 통합문서 참조 표기, 숨김 구조, 제한적인 데이터 형식·성능 신호를 찾는다. 결과는 발견 위치와 근거, 가능한 영향, Excel에서 직접 확인할 방법, 다음 행동을 제공한다.

이는 계산 결과·업무 규칙·통계 모델의 정확성 검사나 파일 수정이 아니다. 무료 사용자는 발견 사실을 확인하고 직접 수정한 뒤 같은 규칙으로 다시 검사할 수 있다.

## 2. 무료와 향후 유료의 경계

무료는 실제 Finding 전체, 위치·근거, 직접 확인 방법, 처리 상태, 직접 재검사, CSV 내보내기를 제공한다. 향후 정밀검증·Approved Repair의 가치는 더 많은 경고가 아니라 수식·업무 의미의 정밀 검토, 변경 전 미리보기, 사용자 승인, 원본과 분리된 수정본, 변경 내역, 재검증 보고서다.

정밀검증과 Approved Repair는 현재 `준비 중` 또는 `향후 제공`으로만 표시한다. 결제·신청·수정 실행 버튼은 없다.

## 3. Action Category

Action Category는 scanner의 사실·severity·repair class를 바꾸지 않는 결과 해석 계층이다. `recommendation_engine.py`가 기존 repair class에서 결정론적으로 매핑한다.

| Action Category | 의미 | 현재 무료에서의 행동 |
|---|---|---|
| `FIX_RECOMMENDED` | 수정 또는 확인 우선 권장 | 사용자 확인 후 Excel에서 직접 조치하고 재검사 |
| `USER_CONFIRMATION` | 업무 의도에 따른 사용자 판단 필요 | 연결·숨김·용도를 확인하고 유지·변경 결정 |
| `DEEP_VALIDATION_REQUIRED` | 정적 검사만으로 판단하기 어려움 | 정밀 검증 필요성을 설명, 현재는 실행하지 않음 |
| `INFO_ONLY` | 참고·유지보수 신호 | 필요할 때만 성능·구조를 검토 |

## 4. 문제별 가이드 구조

현재 지원 rule code마다 다음 템플릿을 제공한다.

- 발견된 사실
- 발생 가능한 영향
- Excel에서 확인하는 방법
- 정상일 수 있는 조건
- 조치를 우선 권장하는 경우
- 사용자 권장 행동
- 이번 검사에서 확인하지 않은 내용
- 다음 정밀검증 항목
- 탐지 근거 등급과 Action Category

가능한 영향은 오류·손실을 단정하지 않는다. 가이드는 AI API를 사용하지 않으며, 수식 후보를 생성하거나 파일을 변경하지 않는다.

## 5. 사용자 처리 상태

Finding별 상태는 `확인 전`, `확인함`, `수정 예정`, `무시`, `정상으로 판단`이다. 이는 시스템 판정이 아니라 화면 안의 사용자 메모다. 상태 변경은 severity, Action Category, 진단 결과, 가격, API 데이터를 바꾸지 않는다.

현재는 React local state만 사용한다. DB·계정·서버 저장·장기 이력·파일 내용 저장은 사용하지 않는다. 재검사 뒤에도 같은 finding key가 계속 탐지된 경우에만 같은 화면 상태가 적용될 수 있다.

## 6. 최소 재검사 설계

흐름은 다음과 같다.

```text
진단 → 사용자가 Excel에서 직접 확인 또는 수정 → 수정 후 파일 선택 → 같은 scanner 재검사 → 결과 비교
```

이전 원본 파일은 보관하지 않는다. 현재 열린 브라우저 화면의 이전 ScanResult와 새 ScanResult만 메모리에 둔다. 비교는 실제 scanner가 만든 결과만 사용한다.

## 7. Finding 비교 기준

각 Finding은 `finding_key`를 가진다. key는 `rule_code`와 정규화된 sheet/cell 또는 range만 조합하며, 셀 값·수식 본문·파일 내용은 포함하지 않는다.

- 이전에는 있었고 현재 key가 없으면: `이번 재검사에서 더 이상 탐지되지 않음`
- 양쪽에 같은 key가 있으면: `계속 탐지됨`
- 현재에만 key가 있으면: `새롭게 탐지됨`

중복 key는 한 번만 비교한다.

## 8. 재검사 한계

`더 이상 탐지되지 않음`은 이번 정적 규칙이 해당 위치에서 신호를 찾지 못했다는 뜻이다. 업무적 해결, 수식 계산 결과, 파일 전체 정확성을 보장하지 않는다.

- 시트 이름 변경 또는 셀 이동은 새 Finding처럼 보일 수 있다.
- scanner version 또는 rule set version이 다르면 비교는 근사치일 수 있다.
- 두 결과 중 하나가 `scan_truncated = true`이면 비교 범위가 완전하지 않을 수 있다.
- 외부 파일 내용, VBA, Power Query, 계산 결과는 비교하지 않는다.

## 9. CSV 다운로드 구조

브라우저에서 UTF-8 BOM CSV를 생성한다. Excel 한글 표시를 고려한 방식이며 서버 저장소·PDF 라이브러리를 쓰지 않는다.

필드: 검사 파일명, 검사 일시, scanner/rule-set version, 검사 범위, scan truncated 여부, rule code, severity, Action Category, sheet, cell/range, 발견된 사실, 가능한 영향, 탐지 근거, 사용자 권장 행동, Excel 확인 방법, 검사 한계, 사용자 처리 상태.

## 10. Approved Repair를 위한 최소 데이터 구조

현재 API에는 결과 수준의 `scanner_version`, `rule_set_version`, `scanned_at`와 Finding 수준의 선택적 `finding_key`가 있다. 가이드에는 `action_category`, `repair_eligibility`, `user_confirmation_required`, `repair_readiness`를 추가했다.

`user_status`, payment status, repair approval, account, long-term history는 백엔드 모델에 넣지 않는다. Approved Repair의 실제 승인·미리보기·수정본 생성·변경 내역은 M7 이전에 구현하지 않는다.

## 11. 이번 단계에서 구현하지 않은 기능

- 자동 Repair Engine, 수식 후보 생성, 수정본 XLSX, 변경 전 미리보기
- Excel 계산 엔진, VBA·Power Query·외부 연결 실행
- 계정, DB 이력, 결제, 신청 폼, 관리자 화면
- 서버 파일 장기 저장, 클라우드 배포, PDF 보고서
- M3 사용자 계측 또는 실제 유료 전환 실험
