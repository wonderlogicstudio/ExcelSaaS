# Milestone review — H2 upload routing correction

**2026-09-09: H2 IN PROGRESS, synthetic-only.** This current section supersedes
the historical preparation/preflight reviews below. It is not H2 completion or
permission to invite users, upload real workbooks, or start H3/M5.

The browser upload's `Not Found` was traced to Gateway's operation-level
`CONSTANT_ADDRESS`: Cloud Run logs showed `POST /` returning 404, and the deployed
service config confirmed the rewrite. The OpenAPI template now explicitly uses
`APPEND_PATH_TO_ADDRESS`, preserving `/v1/scans` and the body-bound HMAC path.

Verification:

- A template-driven regression reproduced the exact 404 before the fix; after
  the fix, the real FastAPI scan route behind hosted HMAC validation returns 200
  for a synthetic workbook and denies an unsigned call with 401.
- Worker cleanup tests cover both a downstream 404 and a network failure.
- Full M4 release/general verification passed: web 25, Worker 5, API 70,
  TypeScript/production build, Ruff, supplied 36-target pack, and M4-C 72/72
  under the existing named fixture waiver. M4-A.5 remains `CONDITIONAL_GO`.
- Replacement Gateway config `workbookcare-beta-config-20260909203335` is
  deployed; the existing Gateway is ACTIVE on it at 11:44:10 UTC. Google's
  compiled backend rule has `APPEND_PATH_TO_ADDRESS` and
  preserves the exact Access issuer/audience and Cloud Run JWT audience.
- Cloud Run stays on `workbookcare-api-beta-00002-d5l` at 100%; no IAM, secret,
  Access policy, Worker runtime, frontend, or scanner changes for this fix.
- Wrangler reports zero objects/zero bytes and the enabled one-day lifecycle
  rule for all prefixes. This is configuration/inventory evidence, not proof
  of per-request deletion or an observed lifecycle expiration.
- Post-rollout anonymous checks: Worker 302 (Access redirect), Gateway POST 401,
  Cloud Run 403. R2 public development access is disabled with no custom domain.
- An authenticated browser synthetic upload then displayed the normal diagnosis
  result. Cloud Run records `POST /v1/scans` 200 at 11:52:25 UTC and the R2 bucket
  immediately returned to zero objects/zero bytes. This completes the positive
  browser flow and successful-request cleanup evidence.
- A deliberately malformed synthetic `.xlsx` reached `POST /v1/scans`, returned
  415 at 12:09:52 UTC, and R2 again immediately reported zero objects/zero bytes.
  This completes the malformed browser-failure cleanup check without exposing
  workbook content in logs.
- Worker version `50128bfe-4942-48e1-9732-b1bd07205464` now rate-limits each
  authenticated Access assertion to five upload attempts per minute. The counter
  uses only an irreversible token hash, returns 429 before R2, and is covered by
  a Worker regression test. The browser and Worker now also reject a synthetic
  file above 10 MiB before it reaches R2.
- Post-deployment checks remain private: Worker 302 without Access, Gateway 401
  without a bearer assertion, direct Cloud Run 403, R2 zero objects/bytes, no
  `r2.dev` or custom domain, and enabled one-day expiration. The project has an
  existing KRW 10,000 budget with 50%, 90%, and 100% alert thresholds. The owner
  reports browser CSV download success.

Open gates: direct Gateway denial with a valid Access assertion but no Worker HMAC,
browser re-validation, and observed one-day lifecycle backstop. The configured
lifecycle rule and normal plus malformed-path immediate cleanup are verified; an
elapsed one-day expiration has not yet been observed. No persistent test route or
service credential was created merely to simulate the valid-Access/no-HMAC call.
A single content-free synthetic lifecycle probe was remotely written and read back
at 2026-09-09 12:37 UTC without recording its key or bytes; it awaits the existing
one-day expiration rule.
Live resource IDs and rollback config are in `42_HOSTED_BETA_H2_PREFLIGHT.md`.

## Historical review — Cloud Run preparation only

> **Historical H1 review; H2 activation update (2026-09-09):** H1 remains
> completed. H2 is approved and in progress for synthetic-only deployment. This
> review is not H2 completion evidence; current H2 controls and open gates are in
> `docs/42_HOSTED_BETA_H2_PREFLIGHT.md` and `docs/40_HOSTED_BETA_H2_RUNBOOK.md`.

**2026-09-09: COMPLETED / STOPPED BEFORE DEPLOYMENT.**

실제 WorkbookCare 저장소 `C:\Users\JinwonLee\project\ExcelSaaS`에서 작업했다.
이번 사용자 승인은 backend Cloud Run 준비까지이며 이전 H2 배포 승인을 재개하지 않는다.
실제 Google Cloud 리소스·이미지 push·frontend 배포·Cloudflare/R2 연동은 수행하지 않았다.
회원가입, 결제, 자동수정, 진단 규칙, 기존 API 제품 응답/feature gate는 변경하지 않았다.

## 변경

- `apps/api/app/runtime.py`: 기존 `app.main:app`을 `0.0.0.0:$PORT`에 단일 worker로 실행.
  기본 8080, 잘못된 PORT는 안전하게 거부. URL access log off. Uvicorn 예외와
  openpyxl 경고는 원문을 제거한 event/severity만 기록.
- `apps/api/Dockerfile`: 위 실행기로 CMD 변경. Python 3.12 slim, non-root app,
  0700 `/tmp/workbookcare`, 기존 liveness healthcheck 유지.
- `apps/api/.dockerignore`: 소스/패키지 정의만 허용하는 build context.
- `apps/api/tests/test_runtime.py`, `apps/api/tests/test_upload_cleanup.py`: 로그/PORT와
  multipart 성공·실패·연결 중단 후 spool close를 검증하는 15개 회귀 테스트.
- `scripts/verify_cloudrun_container.py`: 실제 HTTP/Docker 합성 검증 자동화.
- `infra/cloudrun/deploy.ps1.example`: registry digest, IAM, port/probe/resource limits가
  명시된 후속 명령. 작성만 했고 실행하지 않음.
- `docs/09_CURRENT_MILESTONE.md`, `docs/10_PROGRESS.md`, `docs/11_DECISIONS.md`,
  `docs/14_HOSTING_DEPLOYMENT.md`, `docs/43_CLOUD_RUN_PREPARATION.md`, 이 보고서:
  승인 범위, 작업 결과, 후속 절차와 위험 기록. 이전 미커밋 내용은 보존.

## 필수 검토 10개

| 항목 | 결과 |
| --- | --- |
| 실제 FastAPI entrypoint | `apps/api/app/main.py`의 `app.main:app` 확인; 변경 없음 |
| PORT | 기본 8080과 환경변수 9091로 실제 container 실행 통과; 잘못된 값 거부 테스트 통과 |
| binding | `0.0.0.0`; Docker port mapping을 통한 외부 HTTP 응답 확인 |
| container build | 기존 Dockerfile, `linux/amd64` build 통과 |
| health | 기존 `/health`, `/health/live`, `/health/ready` 모두 200; Docker health `healthy` |
| 의존성 | 기존 `pyproject.toml`에서 runtime `pip install .`; 이미지 `pip check` 통과 |
| 임시 업로드 정리 | 성공, 413/415/422/404/500, missing field, multipart disconnect에서 close 확인; 실제 container TMPDIR/열린 tmp fd 없음 |
| 고객 내용 로그 | 합성 filename/cell/formula/print-area warning/exception/query sentinel이 container stdout/stderr에 없음; runtime warning/exception 이벤트는 존재 |
| 로컬 container | 기본 8080, 변경 9091, 강제 500의 3회 모두 통과; non-root, private tmp, SIGTERM exit 0; 검증용 container 제거 |
| 전체 자동 테스트 | 아래 전체 RC 검증 명령 exit 0 |

## 실행한 검증과 결과

```powershell
docker build --platform linux/amd64 -t workbookcare-api:cloudrun-prep -f apps/api/Dockerfile apps/api
& .\apps\api\.venv\Scripts\python.exe scripts/verify_cloudrun_container.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify-m4-release.ps1 -AcceptProductOwnerFixtureWaiver
```

- 변경 전 기준: 웹 **23**, API **50**, build/Ruff/공급 M4-C pack 통과.
- 변경 후: 웹 **23**, API **65**, TypeScript/Vite production build, API Ruff 통과.
- 추가 검증 스크립트 Ruff와 `git diff --check` 통과.
- M4-C 공급 pack: **36 exact candidates / no extras**.
- M4-C 통합 20파일: **72/72 location, rule, subtype**; 기존 승인된 두 label 충돌
  예외 `M4C-2026-09-02-source-label-conflict` 유지. 소스 fixture는 변경하지 않음.
- M4-A.5: **24 TP / 0 FP / 0 FN**, synthetic precision/recall/F1 1.0.
  성능 판정 **CONDITIONAL_GO 유지**: 1k/10k/30k formula M4/base 비율
  **1.913 / 2.061 / 2.302**. 실제 고객 성능/정확도 보장이 아님.
- 기존 Starlette TestClient의 httpx deprecation warning 1개는 남아 있고 실패는 없음.
- 실제 container 진단 결과는 로컬 scanner와 비교하여 기존 UUID/실행 시각을 제외한
  Findings/key·summary·risk·quote·limitations 등 전체 응답이 동일했다.

로컬 이미지 `workbookcare-api:cloudrun-prep`:

```text
Docker image ID: sha256:0a1c98a18313b832f8046f4f001c59fad32cd77736acbf37063c630aafdfe9da
Platform: linux/amd64
Runtime user: app
Python: 3.12.14
FastAPI: 0.141.1
Starlette: 1.6.0
Uvicorn: 0.52.4
openpyxl: 3.1.5
pip check: No broken requirements found.
```

위 식별자는 로컬 Docker 결과이며, 아직 존재하지 않는 Artifact Registry digest로
표현하지 않는다. 테스트 컨테이너는 모두 제거했고 이미지만 로컬에 남겼다.

## 실행/배포 방법과 남은 위험

정확한 local run/build, 후속 tag/push 및 `gcloud run deploy`, 환경변수와 위험은
[`43_CLOUD_RUN_PREPARATION.md`](43_CLOUD_RUN_PREPARATION.md)에 있다.
후속 명령은 **검증 이미지 digest**, IAM 필수, Seoul region, 1 CPU/1 GiB,
concurrency 1, timeout 60초, min 0/max 2, HTTP startup/liveness probe를 사용한다.

필수 hosted 설정: `APP_ENV=hosted_beta`, 정확한 HTTPS `CORS_ORIGINS`,
`FORMULA_PATTERN_AUDIT_ENABLED=false`, `AI_EXPLANATIONS_ENABLED=false`.
`PORT`는 Cloud Run이 주입하며 `TMPDIR`는 이미지 기본값을 유지한다.
frontend 미배포 단계는 `https://beta.example.invalid`를 비활성 CORS 자리표시자로 쓴다.
현재 backend에 R2/DB/payment/AI/Google key/HMAC secret은 필요하지 않다.

남은 위험: 실제 IAM 미검증, multipart 파싱 전 총량/속도 제한 없음, 동기 scanner의
작업별 강제 timeout 없음, OOM/강제 종료 때 secure erase 보장 없음, 플랫폼 HTTP
메타데이터 로그/보관정책 미설정, dependency lock·취약점 검사·최대 부하·비용 경보 미완료.
이번 검증은 **배포 준비 완료**이며 공개 hosted beta 운영 승인이나 고객 업로드 승인이 아니다.

**다음 단계 배포를 시작하지 않고 여기서 중단했다.**


<details>
<summary>Previous H2 preflight review (historical; preserved)</summary>

# Hosted Beta H2 — Preflight Review

## Status

`H2 BLOCKED — awaiting dedicated cloud targets, operator credentials, and H2 authentication configuration`

The H2 scope is approved, but actual deployment cannot safely begin on this PC. `gcloud` and `wrangler` are unavailable, no authenticated Cloudflare/Google Cloud target is configured, and no beta hostname/project has been supplied.

## Verified baseline

- H1 commit: `68cc3b6 chore: prepare hosted beta deployment foundation`.
- Working tree was clean before the H2 preflight documentation change.
- M4 RC verification passed with the existing narrow product-owner fixture waiver: 72/72 target locations and top-level rules.
- M4-A.5 retained `CONDITIONAL_GO`, precision/recall 1.0.

## Required security improvement

H1 correctly forbids both anonymous Cloud Run and a Google service-account key in Cloudflare. A direct Worker-to-Cloud-Run call would otherwise have no safe Google IAM identity.

H2 therefore requires this bridge before any deployment:

1. Cloudflare Access authenticates the browser and the Worker validates the exact Access JWT.
2. The Worker forwards that JWT to Google API Gateway.
3. API Gateway validates the exact Cloudflare issuer and audience, then calls Cloud Run with its own least-privilege backend-auth service account.
4. FastAPI separately validates a short-lived HMAC created only by the Worker.

This leaves Cloud Run non-anonymous, rejects a direct Cloud Run request by IAM, and rejects direct API Gateway calls that lack the Worker HMAC.

## Blocking prerequisites

- Operator-approved Cloudflare account ID, hosted-beta hostname, R2/Workers/Zero Trust permissions, and an Access policy restricted to the operator for synthetic testing.
- Operator-approved Google Cloud project ID, billing, region, APIs, least-privilege deployment roles, Artifact Registry, Cloud Run, API Gateway, Secret Manager, service accounts, and budget controls.
- Permission to install Google Cloud CLI and Wrangler using the internet.
- Approval to create the additional API Gateway bridge and accept its operational/cost footprint.

See `docs/42_HOSTED_BETA_H2_PREFLIGHT.md` for the exact preflight and no-secret handling rules.

## Stop condition

No cloud resource, credential, deployment, invitation, real workbook, M3/M3.5 test, H3 hardening, repair, payment, AI, or new diagnostic rule was started. H2 must resume only after the named prerequisites are available.

</details>
