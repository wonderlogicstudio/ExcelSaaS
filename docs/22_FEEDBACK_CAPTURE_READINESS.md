# Feedback Capture Readiness — M4-A

> H3 update (2026-09-09): this document describes the local-only M4 baseline
> below. H3 adds a separately designed, category-only Worker persistence path for
> Formula Audit synthetic feedback; it is not deployed because the required
> private Cloudflare KV namespace could not be created (Cloudflare API error
> `10000`). The live hosted public Formula Audit UI remains disabled. The current
> H3 contract and processing inventory are in `docs/44` and `docs/45`.

## 상태

이 문서는 호스팅 이후 외부 사용자 검증을 준비하기 위한 개발 환경용 기반을 설명한다. 현재 Feedback UI는 `VITE_FEEDBACK_CAPTURE_ENABLED=true`일 때만 보이며, 기본값은 꺼져 있다. 서버 API, DB, 클라우드 저장, 운영 분석, 자동 전송은 없다.

## 분리 원칙

기존 Finding 처리 상태(`확인 전`, `확인함`, `수정 예정`, `무시`, `정상으로 판단`)는 사용자의 개인 작업 메모다. Feedback은 탐지 품질과 설명 품질에 대한 의견이다. 두 데이터는 서로 변환하거나 scanner 결과·위험 점수·가격·수정 가능성에 영향을 주지 않는다.

## 저장 구조

`FeedbackRepository` 인터페이스와 `LocalFeedbackRepository`가 분리되어 있다. 현재 구현은 아래의 허용 필드만 `localStorage`에 저장한다.

| 필드 | 설명 |
|---|---|
| `feedback_id` | 브라우저가 만든 무작위 식별자 |
| `feedback_scope` | `RESULT` 또는 `FINDING` |
| `feedback_category` | 의견 유형 |
| `rating` | 도움이 됨/안 됨의 선택적 긍정·부정 값 |
| `memo` | 최대 500자의 선택 메모 |
| `rule_code` | Finding 피드백일 때의 규칙 코드 |
| `opaque_finding_id` | 위치를 담지 않는 API Finding UUID |
| `scanner_version` | 결과 해석에 쓴 scanner 버전 |
| `created_at` | 브라우저 생성 시각 |

다음은 코드가 자동 수집하거나 저장하지 않는다: 파일명, 시트명, 셀 주소, 셀 값, 수식 원문, `finding_key`, 원본 Excel 데이터. 메모는 사용자가 직접 입력하는 값이므로 UI에서 회사명·고객정보·실제 셀 값·비밀번호 입력 금지를 명시한다. 사용자는 같은 패널에서 이 브라우저의 테스트 의견을 전부 삭제할 수 있다.

## 의견 유형

전체 결과: 찾고 싶은 문제 미발견, 설명 어려움, 정상 항목이 문제처럼 보임, 중요한 문제 누락 가능성, 수정 방법 상세 필요, 자동수정 또는 검토 표시본 필요, 기타.

개별 Finding: 도움 됨, 도움 안 됨, 잘못 탐지된 것 같음, 설명 부족.

## 운영 전 교체 조건

호스팅 후에만 별도 승인으로 `ApiFeedbackRepository`를 만들 수 있다. 그 전에는 전송 성공·운영 수집·저장 기간을 암시하지 않는다. API로 교체하기 전에는 명시적 동의, 보관·삭제 정책, 접근 통제, 입력 검증, 운영 목적을 별도 검토해야 한다.
