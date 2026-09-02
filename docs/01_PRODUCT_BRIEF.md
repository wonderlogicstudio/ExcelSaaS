# Product brief — WorkbookCare

## Working name

`WorkbookCare` is a codename. The final name should not depend on the Microsoft Excel trademark and should be checked for domain and trademark conflicts before launch.

## One-sentence promise

**파일의 구조적 위험 신호와 현재 검사 한계를 먼저 확인하고, 정밀 검증·승인 기반 수정·재검증이 필요한지 판단하게 돕는다.**

## Current M2.5 boundary

현재 구현은 무료 정적 진단, 결과별 직접 확인 가이드, 현재 열린 브라우저 화면 안의 처리 상태, 직접 수정 후 동일 규칙 재검사, CSV 결과 다운로드까지다. 실제 파일 수정, 사용자 승인, 결제, 견적 요청, AI API, 회원가입은 제공하지 않는다. 정밀 검증·승인 기반 수정·수정본 생성은 향후 서비스로만 안내하며, 가격은 검증된 판매가가 아닌 베타 가설 범위로 표시한다. 세부 범위는 `docs/20_SERVICE_SCOPE.md`와 `docs/21_ACTIONABLE_RESULTS_AND_REVALIDATION.md`를 따른다.

## Problem

People inherit and share workbooks whose formulas, external links, hidden sheets, manual overrides, inconsistent ranges, and formatting drift are difficult to inspect. Existing choices usually fall into one of four groups:

1. Excel's built-in checks, which focus on visible errors.
2. General AI assistants, which explain or edit a workbook but do not provide a contract-like repair scope.
3. Professional audit tools, which are powerful but aimed at finance/model-risk teams and often require installation or enterprise purchasing.
4. Free browser utilities, which diagnose basic issues but stop before safe, approved repair.

The commercial opportunity is not another formula generator. It is an evidence-first repair workflow that reduces uncertainty and disagreement.

## Target customer sequence

### Initial beachhead

Korean office workers, freelancers, small businesses, and Excel-heavy operators who have one problematic workbook and do not want a subscription.

Typical jobs:

- "This workbook became slow and I do not know why."
- "The totals look wrong after somebody inserted rows."
- "I inherited a workbook and need to know whether it is safe to use."
- "There are broken links and hidden sheets, but I do not know what can be removed."
- "I want the file cleaned up without rebuilding the entire system."

### Later expansion

- Accounting and finance teams needing review evidence.
- Excel consultants who want pre-scoping and lead qualification.
- Small organizations needing recurring workbook governance.
- Enterprise local/desktop agent for files that cannot leave the device.

## Jobs to be done

1. Tell me whether this workbook is risky before I send or rely on it.
2. Show me exactly where the problems are and why they matter.
3. Tell me what I can check or change directly, and which items require a human or deeper verification.
4. 현재 무료 검사로 확인할 수 있는 범위와 확인할 수 없는 범위를 구분해 달라.
5. 향후 정밀 검증 또는 별도 수정을 선택할 때 무엇을 추가로 확인해야 하는지 알려 달라.
6. Avoid exposing confidential workbook contents unnecessarily.

## Product principles

- **Evidence before AI prose.** Every finding has a rule code, severity, location, 발견된 사실, 가능한 영향, 검사 한계, 다음 검사 항목을 남긴다.
- **Evidence grade, not fake accuracy.** 현재 화면은 보정되지 않은 `confidence` 퍼센트 대신 탐지 근거 등급을 사용한다.
- **Approval before modification.** Diagnosis, scope, quote, approval, payment, repair, and download are separate states.
- **No surprise charges.** A paid scope cannot expand without a second explicit approval.
- **Original remains untouched.** Output is always a separate file.
- **Deterministic first.** Use static rules for scanning and quote calculation; use LLMs only for bounded explanation or ambiguity.
- **Privacy is a product feature.** Offer a browser-only quick scan, explicit consent for deep upload, short retention, and no model training.
- **Do not overpromise.** Complex VBA, encrypted files, external systems, calculation engines, and unsupported OOXML parts must be disclosed and routed appropriately.

## Initial value proposition

### Free

- No-signup quick scan.
- Workbook risk score and issue counts.
- Top findings with exact sheet/cell references.
- Automatic-fix eligibility estimate.
- Clear limitations.

### Planned per-file precision verification

- 파일별 정밀 검증 범위와 추가 확인 항목.
- 사용자 승인 전 변경 방법 또는 수정 후보 미리보기.
- 원본과 분리된 수정본, 변경 내역, 전후 비교·재검사 보고서.
- 제공 여부와 가격은 별도 승인·검증 후 결정.

### Expert

- Complex formula logic.
- VBA and Power Query.
- Dashboard redesign.
- Multi-file workflows.
- Business-rule reconstruction.

## Non-goals for the first release

- Replacing Excel, Copilot, or a full BI platform.
- Conversational analysis of arbitrary business data.
- Executing macros or external queries.
- Guaranteed detection of every logical error.
- Fully automatic repair of financial models.
- Subscription-first pricing.
- Mobile-native applications.

## North-star behavior

A visitor uploads or tries a sample workbook, 이해 가능한 발견 사실·확인 방법·한계를 확인하고, 직접 수정한 파일을 같은 규칙으로 재검사할 수 있다. 어떤 항목이 향후 정밀 검증·사용자 판단·승인 기반 수정의 검토 대상인지도 구분한다. 현재 단계의 성공은 결제 전환이 아니라 검사 범위와 해결 경로를 오해 없이 전달하는 것이다.
