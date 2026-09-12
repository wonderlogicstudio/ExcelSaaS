# D01 사용자 확인

현재 승인: **D01만**. 판정: **ENGINEERING_VERIFIED_AWAITING_OWNER**.
로컬 구현 커밋: `40e2e8998beef87cb844c1fc400f1e75eced2fa1`. 원격 push·공개 배포 없음.

로컬 확인 화면: http://127.0.0.1:5187 (로컬 API 8187). 합성 샘플만 사용한다.
이 세션의 검토 서버가 종료됐다면 아래의 재현 명령을 사용한다.

1. **샘플 결과 보기**를 눌러 유형 설명을 펼치고 개별 시트·셀 위치와 근거를 찾는다.
2. **유형별 보기 ↔ 전체 항목 표**, 시트/상태 필터를 바꾼 뒤 CSV를 받는다. 유형의 ‘확인함’이 개인 상태만 바꾸고 구매나 변경 승인이 되지 않는지 읽는다.
3. **두 자료 비교** 안내에서 보고서 두 파일과 ‘수정본 미포함·B는 정답 아님’을 읽고, 수정 패키지에는 **수정본 XLSX·변경내역 XLSX·재검증 HTML** 세 파일이 예정돼 있는지 확인한다. 두 상품이 준비 중이며 구매되지 않아야 한다.
4. 휴대폰 너비에서도 표 제목·위치·초점이 읽히는지 확인한다. 필요하면 로컬 합성 `artifacts/verification/d01/synthetic-many-findings.xlsx`로 재검사해 **전체 150 / 상세 120 / 생략 30** 및 신규·미탐지 확정 불가 안내를 확인한다.

## 재현 명령 (각각 별도 PowerShell, 프로젝트 루트)

```powershell
# 로컬 API
$env:APP_ENV='development'
$env:FORMULA_PATTERN_AUDIT_ENABLED='false'
$env:CORS_ORIGINS='["http://127.0.0.1:5187"]'
Push-Location apps/api
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8187 --no-access-log
```

```powershell
# 로컬 화면
$env:VITE_API_BASE_URL='http://127.0.0.1:8187'
$env:VITE_FORMULA_AUDIT_INTERNAL_BETA_ENABLED='false'
$env:VITE_FEEDBACK_CAPTURE_ENABLED='false'
$env:VITE_HOSTED_BETA_FEEDBACK_ENABLED='false'
npm.cmd run dev --workspace @workbookcare/web -- --host 127.0.0.1 --port 5187 --mode d01-review
```

실제 검증: web 59 / Worker 13 / API 75, build/Ruff/M4-C 36 exact, 로컬 Chrome 1440/390 통과.
실행 명령·exit code·파일/보존 증거는 `reviews/D01.md`와 `reviews/evidence/`에 있다.
Excel 계산·PG·실고객·판매/운영 검증 및 실제 수정 산출물 납품은 수행하지 않았다.
현재 어떤 결제·원본 변경·공개 배포도 승인할 필요가 없는 D01 화면 확인이다.

다음 추천 한 단위: **D02** — 한 파일 수정 적합성·업무 확인·불변 입력. 별도 승인 전 실행하지 않는다.
