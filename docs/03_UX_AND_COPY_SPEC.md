# UX and copy specification

## Primary user flow — M2.5

```text
Landing
  → Try sample or select workbook
  → Quick privacy notice
  → Scan progress with named stages
  → Free-scan scope and limits
  → Diagnosis summary
  → Next actions: priority check / re-scan / CSV download
  → Priority findings and full findings: fact / impact / Excel check / normal case / action / limit
  → Local user handling status
  → Manual re-validation comparison
  → CSV result download
  → Repairability classification
  → Repair-readiness and planned resolution path
  → File-specific precision-verification recommendation
  → Planned deliverables and beta price range
```

The current M2.5 Extension stops at direct, same-session re-validation and a CSV download. It has no signup, request form, payment, quote approval, repair processing, or output-file delivery.

## Conversion objective

The first page has one primary action: **무료로 검사하기**.

Secondary action: **샘플 결과 보기**.

Do not place pricing plans, account signup, or generic AI chat ahead of the scan.

## Above-the-fold content

### Eyebrow

`중요한 Excel 사용·공유 전 점검 · 현재 베타`

### Headline

`문제를 찾고, 수정 방향을 정리하세요.`

### Supporting copy

`무료 진단은 깨진 수식 표기, 외부 통합문서 참조, 숨김 시트 같은 구조 위험 신호를 찾습니다. 중요한 파일을 사용하거나 공유하기 전에, 고칠 방법을 더 확인해야 하는 항목과 수정 여부를 판단할 근거를 먼저 보여드립니다.`

### Trust row

- `가입 없이 시작`
- `원본 파일 변경 없음`
- `규칙 기반 무료 진단`

### Upload card

Required states:

- Empty.
- Drag-over.
- File selected.
- Uploading.
- Scanning with stage labels.
- Success.
- Unsupported file.
- Too large.
- API unavailable with sample fallback.

Allowed extensions in the current vertical slice: `.xlsx`, `.xlsm`.

Copy below upload:

`현재 정적 진단만 수행하며 매크로와 외부 연결은 실행하지 않습니다.`

## Scan progress

Do not show a fake percentage that advances independently of real work. Use deterministic stages:

1. `파일 형식 확인`
2. `워크북 구조 분석`
3. `수식과 참조 검사`
4. `위험도와 수정 가능 여부 계산`

For asynchronous production scans, stages must come from backend events or polling state.

## Diagnosis summary

Show the free-scan scope before the summary, then show these answers:

1. How risky is the workbook?
2. How many issues were found?
3. Which issues are critical?
4. Which repairability classifications are present?
5. Which file-specific precision checks are recommended?

### Summary cards

- Structural risk band: `낮음`, `보통`, or `높음`; `critical` is displayed as `높음 · 우선 확인 필요`.
- Numeric score only with the label `규칙 기반 우선순위 점수`; it is not a probability or correctness score.
- Total findings.
- Four repairability summaries: safe candidate, confirmation required, expert review, information only.
- A `해결 경로 검토 대상` count derived only from safe-candidate, confirmation-required, and expert-review findings. It is not an available repair count.

Always include:

`이 결과는 정적 구조 분석이며 Excel 계산 엔진을 실행한 결과가 아닙니다.`

The top of results must also show a `권장 다음 행동` panel with these active controls:

- `우선 문제 확인하기` — moves to the priority findings.
- `수정 후 다시 검사` — asks for a manually edited test workbook and starts same-session comparison.
- `CSV 결과 다운로드` — downloads the current findings and guidance as UTF-8 BOM CSV.

## Findings table/card

### Progressive disclosure

The initial state is a compact, closed Finding row. It shows only severity, rule code, sheet/cell location, title, and a clear `자세히 보기` affordance. Keep all Finding rows in one complete list; do not repeat the same Finding in separate representative and full-detail cards. The global next-action panel remains visible above the list.

On expand, show the full evidence and control set below. The detail content is not removed or simplified; it is deferred until the user chooses the Finding they need to inspect.

Each finding requires:

- Severity: critical / warning / info.
- Rule code.
- Plain-language title.
- `발견된 사실`.
- `발생 가능한 영향` without claiming a confirmed error or loss.
- `이번 검사에서 확인하지 않은 내용`.
- `다음 정밀검증 항목`.
- `향후 해결 경로`: current repair-readiness classification, required future steps, and a visible `준비 중` state.
- Sheet and cell/range when available.
- `탐지 확실도`: `직접 확인`, `패턴 추정`, or `참고 신호`. Do not show `confidence` percentages unless a documented calibration exists.
- Action Category: `수정 또는 확인 우선 권장`, `사용자 확인 필요`, `정밀 검증 필요`, or `정보 제공`.
- `Excel에서 확인하는 방법`, `정상일 수 있는 조건`, and `조치를 우선 권장하는 경우`.
- Local `사용자 처리 상태`: `확인 전`, `확인함`, `수정 예정`, `무시`, or `정상으로 판단`. It is a user memo, not a system verdict.
- Repair class:
  - `자동 수정 후보`
  - `사용자 확인 필요`
  - `전문가 검토`
  - `정보 제공`

Do not expose formulas or cell values in telemetry.

## Manual re-validation

The user may edit a workbook in Excel and choose `수정 후 다시 검사`. The application keeps only the previous scan result in the current React session; it never keeps the previous workbook file. It compares stable, value-free finding keys and displays:

- `이번 재검사에서 더 이상 탐지되지 않음`
- `계속 탐지됨`
- `새롭게 탐지됨`

Use the first phrase instead of `해결됨`. Show an explicit warning when scanner/rule-set versions differ or either scan was truncated. The comparison does not prove business correctness or recalculated Excel results.

## CSV download

Generate the CSV in the browser with a UTF-8 BOM. Include scan metadata, current scope, finding location and guidance, Action Category, and local user status. Do not add PDF generation or server-side result storage.

## Quote preview

The M2.5 panel is a planned-service preview, not a contract or a checkout.

Display:

- Work level and beta price range, or a statement that the range cannot yet be estimated.
- Current findings used for the recommendation.
- Included and excluded expected scope.
- Planned deliverables and service status.
- A clear notice that payment and actual repair are unavailable.
- A planned sequence: precision verification → change preview → user approval → separate repaired file → re-validation. This sequence must not expose a purchase or repair action until implemented.

Primary copy:

`베타 가격 가설이며 현재 결제는 진행되지 않습니다. 최종 작업 범위와 가격은 향후 사용자 확인 후 확정됩니다.`

The current prototype disables real checkout and labels it clearly.

## Comparison section

Use a factual comparison focused on workflow rather than attacking competitors.

| General AI help | WorkbookCare |
|---|---|
| User must explain the problem | Workbook is scanned systematically |
| Answers may be conversational | Findings include location and rule evidence |
| Scope can change while working | Scope and price are fixed before payment |
| Modification history may be unclear | Separate output plus change log |

## Privacy section

Required messages:

- Original is never overwritten.
- Macros and external connections are not executed.
- 무료 진단은 AI API를 사용하지 않는다.
- 매크로와 외부 연결은 실행하지 않는다.
- 진단은 원본 파일을 변경하거나 다시 저장하지 않는다.

Do not claim retention, automatic deletion, encryption, residency, certification, training policy, or browser-only processing until technically and contractually true.

## FAQ priorities

1. Can it detect every Excel error?
2. Will my original file change?
3. Are VBA and Power Query supported?
4. Is my company data sent to AI?
5. When do I pay?
6. What happens if the file cannot be repaired?
7. Which files are supported?

## Visual direction

- Professional, calm, audit-oriented, not playful.
- Light background with deep navy text and restrained aqua accents.
- Warm amber/red used only for warning/critical states.
- Rounded cards but not oversized pill-shaped everything.
- Product output is the hero visual; no stock illustration required.
- Dense information becomes progressively visible after scan.
- Desktop-first because users handle workbooks on PCs, but responsive down to 360 px.

## Accessibility acceptance

- WCAG-oriented color contrast.
- Upload zone is keyboard operable and uses a native file input.
- Status changes use `aria-live` without excessive announcements.
- No information is conveyed by color alone.
- Focus indicators remain visible.
- Motion respects `prefers-reduced-motion`.
- Buttons have specific action labels.

## Localization

- Korean is default for launch.
- All UI strings must be centralized for later English support.
- Currency and number formatting must use locale APIs.
- Do not concatenate translated fragments in code.
