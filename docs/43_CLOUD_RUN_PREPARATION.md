# Cloud Run 배포 준비 — 2026-09-09

이번 단계는 기존 `apps/api`의 로컬 컨테이너 준비와 검증까지다. Google Cloud
리소스 생성, 이미지 push, Cloud Run 배포, frontend 배포, Cloudflare/R2 연동을
실행하지 않았다. 회원가입·결제·자동수정·진단 규칙·기존 제품 응답을 변경하지 않았다.
이전 H2 문서는 후속 설계이며 이번 작업의 실행 범위를 넓히지 않는다.

## 저장소와 실제 실행 경로

현재 세션의 시작 폴더는 `DigitalTwin`이었지만, 실제 WorkbookCare 저장소는
`C:\Users\JinwonLee\project\ExcelSaaS`다. 아래 명령은 이 저장소 루트 기준이다.
기존 미커밋 문서 변경은 보존했다.

- `apps/web`: React/TypeScript. 자동 테스트와 로컬 production build만 재실행.
- `apps/api/app/main.py`: 실제 FastAPI 객체 `app`, 즉 **`app.main:app`**.
- `apps/api/app/scanner.py`: 기존 정적 진단. 이번 단계에서 수정하지 않음.
- `apps/api/pyproject.toml`: 기존 Python 패키지와 runtime/dev 의존성.
- `infra/cloudrun/deploy.ps1.example`: 후속 승인 후 사용할 배포 명령 예제.

## 변경과 검토 결과

| 파일 | 변경 이유 |
| --- | --- |
| `apps/api/Dockerfile` | 기존 Python 3.12 slim, non-root `app`, private `TMPDIR`, healthcheck를 유지하고 CMD만 `python -m app.runtime`으로 변경 |
| `apps/api/app/runtime.py` | `PORT` 검증, 기본 8080, `0.0.0.0`, 단일 worker, URL access log 비활성화, 원문 예외/파서 경고를 내용 없는 이벤트로 변환 |
| `apps/api/.dockerignore` | build context를 Dockerfile·패키지 정의·Python 소스로 제한; `.env`, 파일, 로그, venv, 테스트 유입 방지 |
| `apps/api/tests/test_runtime.py` | 예외·인수·stack·warning 내용 미노출과 잘못된 PORT 거부 검증 |
| `apps/api/tests/test_upload_cleanup.py` | 실제 multipart spool을 강제로 디스크에 넘긴 뒤 성공, 413, 415, 422, gate 404, 500, 중단된 업로드에서 close 확인 |
| `scripts/verify_cloudrun_container.py` | 실제 Docker HTTP, 기본/대체 포트, 결과 동일성, 임시파일/열린 핸들, 로그, UID, healthcheck, SIGTERM 검증 자동화 |
| `infra/cloudrun/deploy.ps1.example` | 검증한 이미지 digest 배포, IAM 필수, 포트/probe 명시; source 재빌드 경로 교체 |
| `docs/09_CURRENT_MILESTONE.md`, `docs/10_PROGRESS.md`, `docs/11_DECISIONS.md`, `docs/14_HOSTING_DEPLOYMENT.md`, 이 문서, `docs/MILESTONE_REVIEW.md` | 이번 승인 범위·검증 증거·배포 전 중단 상태를 기록 |

### PORT, 바인딩, health

`python -m app.runtime`이 `app.main:app`을 `0.0.0.0:$PORT`에서 실행한다.
PORT가 없으면 8080이며 1–65535 범위 밖 또는 숫자가 아닌 값은 입력 원문을
출력하지 않고 시작을 거부한다. 개발용 `uvicorn --reload`를 container CMD로
덮어쓰지 않는다. Cloud Run의 PORT 주입과 바인딩 규약은
[공식 runtime contract](https://docs.cloud.google.com/run/docs/container-contract)에 따른다.

기존 endpoint를 그대로 사용한다: `/health` → `ok`, `/health/live` → `live`,
`/health/ready` → `ready` 및 scanner/rule/RC 버전. readiness는 현재 프로세스의
응답/버전 확인이며, 미구현 저장소나 IAM 연결의 정상 여부를 보증하지 않는다.
Docker HEALTHCHECK는 로컬 검증용이고, 배포 명령에서 Cloud Run startup/liveness
probe를 별도로 지정한다.
[Cloud Run healthcheck 문서](https://docs.cloud.google.com/run/docs/configuring/healthchecks)

### 의존성 설치

기존 `pip install .`가 `pyproject.toml`의 runtime 의존성만 설치한다. dev 도구는
이미지에 설치하지 않는다. 로컬 전체 검증 환경은 `pip install -e '.[dev]'`를 사용한다.
현재 범위와 기본 이미지는 lock/digest로 고정되어 있지 않아 미래의 재빌드는 달라질
수 있다. 이번에는 의존성을 임의로 업그레이드하는 소스 변경을 하지 않았으며,
후속 배포는 이 단계에서 테스트한 이미지 자체를 push하고 registry digest로 지정한다.
재빌드했다면 다시 검증해야 한다.

### 업로드 수명과 로그

FastAPI의 multipart request exit stack은 `UploadFile`의 `SpooledTemporaryFile`을
응답/예외 경로에서 닫는다. 설치된 Starlette parser는 읽기 실패/연결 중단도 정리한다.
scanner는 bytes/`BytesIO`를 사용하며 원본을 저장하거나 ZIP을 디렉터리에 풀지 않는다.
새 저장소·삭제 스케줄러는 필요하지 않아 추가하지 않았다. 이번 테스트는 단순 디렉터리
확인 외에 Linux `/proc/1/fd`도 확인해 이름이 지워진 채 열린 임시파일을 점검한다.
`FILE_RETENTION_HOURS=24`는 현재 이 경로의 보관 타이머나 삭제 보장을 구현하지 않는다.

기존 generic 500 handler 뒤에 Starlette가 예외를 다시 던지므로 Uvicorn이 원문을
기록할 수 있었다. openpyxl의 잘못된 print-area warning에도 workbook-defined
text가 들어갈 수 있었다. 새 실행기는 warning을 logging으로 보내고, 일반 runtime
로그의 message/args/traceback/stack을 직렬화하지 않는다. `runtime_log`,
`runtime_warning`, `runtime_exception`과 severity만 남긴다. 기존 allowlist
`workbookcare.safe_events`는 기존 구조를 유지한다. 상세 예외가 사라져 운영 원인
분석에는 내용 없는 이벤트와 안전한 로컬 재현이 필요하다.

## 로컬 실행과 검증 명령

```powershell
Set-Location C:\Users\JinwonLee\project\ExcelSaaS
docker build --platform linux/amd64 -t workbookcare-api:cloudrun-prep -f apps/api/Dockerfile apps/api
& .\apps\api\.venv\Scripts\python.exe scripts/verify_cloudrun_container.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify-m4-release.ps1 -AcceptProductOwnerFixtureWaiver
```

마지막 명령은 M4-C 통합평가, M4-A.5 품질/성능 평가, `scripts/verify.ps1`의 웹
테스트·타입검사/build·API pytest·Ruff·공급 샘플 평가를 모두 실행한다. 실행 정책
옵션은 해당 PowerShell 프로세스에만 적용되며 시스템 정책을 바꾸지 않는다.
기존 승인 예외 `M4C-2026-09-02-source-label-conflict`는 두 source label 충돌에만 적용된다.

수동 local smoke 실행은 다음과 같다. 포트 18080이 비어 있어야 한다.

```powershell
docker run --rm --name workbookcare-api-local -p 127.0.0.1:18080:8080 --memory=1g --cpus=1 --cap-drop=ALL --security-opt=no-new-privileges:true -e APP_ENV=hosted_beta -e CORS_ORIGINS=https://beta.example.invalid -e FORMULA_PATTERN_AUDIT_ENABLED=false -e AI_EXPLANATIONS_ENABLED=false workbookcare-api:cloudrun-prep
# 다른 터미널:
Invoke-RestMethod http://127.0.0.1:18080/health/ready
curl.exe --fail-with-body -F 'file=@samples/demo-risky-workbook.xlsx' http://127.0.0.1:18080/v1/scans
docker stop workbookcare-api-local
```

## 후속 승인 후에만 사용할 Cloud Run 절차 — 이번에는 실행하지 않음

승인된 project/billing/APIs, `asia-northeast3`의 Artifact Registry repository,
전용 runtime service account, 배포 운영자의 CLI 인증/권한이 먼저 있어야 한다.
runtime service account에는 이 stateless 분석을 위해 별도 데이터 접근 역할이 필요하지
않다. 이 단계에서 CLI 설치·로그인·API 활성화·repository·service account를 생성하지 않았다.

1. 기존 registry에 **검증한 로컬 이미지**를 tag/push한다. 아래 값은 실제 승인된
   project/repository로 교체한다. 이 명령은 후속 작업이며 비용/외부 변경을 일으킨다.

```powershell
$ProjectId = "REPLACE_WITH_APPROVED_PROJECT"
$Region = "asia-northeast3"
$Repository = "REPLACE_WITH_EXISTING_REPOSITORY"
$Registry = "${Region}-docker.pkg.dev"
$ImageTag = "${Registry}/${ProjectId}/${Repository}/workbookcare-api:cloudrun-prep"
gcloud auth configure-docker $Registry
docker tag workbookcare-api:cloudrun-prep $ImageTag
docker push $ImageTag
```

2. Artifact Registry 콘솔에서 해당 이미지의 업로드된 버전을 열고 `sha256:...` digest를
   복사한다. 다음 전체 이미지 참조를 만든다.
   `asia-northeast3-docker.pkg.dev/PROJECT/REPOSITORY/workbookcare-api@sha256:DIGEST`.
   로컬 Docker image ID와 registry manifest digest를 혼동하지 않는다.
3. `infra/cloudrun/deploy.ps1.example`의 실제 `gcloud run deploy` 명령을 사용한다.
   `$ProjectId`, `$Image`, `$RuntimeServiceAccount`는 승인된 실제 값으로 설정하고,
   `$Service='workbookcare-api-beta'`, `$Region='asia-northeast3'`,
   `$FrontendOrigin='https://beta.example.invalid'`를 기본으로 사용한다. `.invalid`는
   frontend가 아직 없는 operator-only 준비 단계의 비활성 CORS 자리표시자다.

```powershell
gcloud run deploy workbookcare-api-beta `
  --project $ProjectId --region asia-northeast3 --image $Image `
  --service-account $RuntimeServiceAccount `
  --no-allow-unauthenticated --invoker-iam-check --ingress all `
  --port 8080 --cpu 1 --memory 1Gi --concurrency 1 --timeout 60 `
  --min 0 --max 2 --max-instances 2 `
  --startup-probe "httpGet.path=/health/ready,httpGet.port=8080,periodSeconds=5,timeoutSeconds=3,failureThreshold=12" `
  --liveness-probe "httpGet.path=/health/live,httpGet.port=8080,periodSeconds=30,timeoutSeconds=5,failureThreshold=3" `
  --set-env-vars "APP_ENV=hosted_beta,CORS_ORIGINS=https://beta.example.invalid,FORMULA_PATTERN_AUDIT_ENABLED=false,AI_EXPLANATIONS_ENABLED=false"
```

이 명령은 **실제로 Cloud Run 서비스를 생성/수정한다**. 이번 단계에서 실행하지 않았다.
플래그는 [공식 gcloud run deploy 참조](https://docs.cloud.google.com/sdk/gcloud/reference/run/deploy)에서
확인했다. Cloud Run command/args override를 설정하지 않아 이미지 실행기를 유지한다.

4. 다음 단계에서 IAM 정책에 `allUsers`, `allAuthenticatedUsers`, 불필요한 project-wide
   Invoker가 없는지 검증하고 승인된 운영자만 호출한다. 익명 요청 거부와 인증된 health/
   합성 업로드를 검증한다. CORS는 인증 수단이 아니다. 일반 브라우저 제품 연결은
   아직 준비되지 않았고 frontend/R2/Access/Gateway/HMAC은 별도 승인 단계다.

## 환경변수

| 변수 | 이번 컨테이너/후속 비공개 API 값 | 설명 |
| --- | --- | --- |
| `PORT` | 로컬 기본 8080; 테스트 9091 | Cloud Run이 `--port 8080`에 따라 자동 주입. `--set-env-vars`로 중복 지정하지 않음 |
| `APP_ENV` | `hosted_beta` | 기존 hosted 설정 검증과 M4 gate 유지 |
| `CORS_ORIGINS` | `https://beta.example.invalid` | 한 개의 정확한 HTTPS origin. frontend 미배포 상태용; 실제 origin은 후속 승인 후 변경 |
| `FORMULA_PATTERN_AUDIT_ENABLED` | `false` | 기존 내부 수식 audit 기본 off 및 hosted 차단 유지 |
| `AI_EXPLANATIONS_ENABLED` | `false` | 기존 off 유지 |
| `TMPDIR` | `/tmp/workbookcare` | 이미지에 생성된 app 소유 0700 디렉터리. 임의 경로로 덮어쓰지 않음 |
| `MAX_UPLOAD_MB` | 기존 기본 10 | 코드 기본값 유지 |
| `MAX_UNCOMPRESSED_MB` / `MAX_ZIP_ENTRIES` | 기존 기본 120 / 5000 | OOXML 제한 유지 |
| `MAX_COMPRESSION_RATIO` / `SCAN_CELL_LIMIT` / `FINDING_LIMIT` | 기존 기본 250 / 250000 / 120 | 기존 진단 제한 유지 |

기존 Python unbuffered/no-bytecode/pip-no-cache 설정도 Dockerfile에 유지한다.
현재 backend 실행에는 R2, database, OpenAI, 결제, HMAC, Google key 환경변수가 필요 없다.

## 남아 있는 보안·운영 제한

- 컨테이너는 API 자체 사용자 인증/요청 빈도 제한을 추가하지 않았다. Cloud Run IAM이
  필수이며, 이번 로컬 검증은 실제 IAM 거부 동작을 증명하지 않는다. 공개 배포/초대는 별도 단계다.
- 10 MB 제한은 multipart 파싱 **후** 적용된다. 요청 전체 크기/속도와 동시 업로드에
  대한 edge 제한은 아직 없다. 신뢰되지 않은 공개 트래픽을 허용하면 임시 메모리/CPU가
  먼저 소모될 수 있다. `concurrency=1`, 1 GiB는 초기 설정이며 최대 파일 부하 검증이 아니다.
- Cloud Run writable filesystem은 instance 메모리를 사용하며 종료 후 지속되지 않는다.
  OS 종료/OOM/강제 kill 시 Python finally 실행을 보장할 수 없고, bytes 즉시 secure erase도
  보장하지 않는다. 현재 immediate close 검증을 R2 삭제나 zero-retention 주장으로 확대하지 않는다.
  [공식 filesystem contract](https://docs.cloud.google.com/run/docs/container-contract#file_system_access)
- 동기 scanner는 event loop와 health 응답을 오래 점유할 수 있다. Cloud Run 요청 timeout은
  계산 강제 중지나 작업별 cancellation을 구현하지 않는다. 별도 작업 격리/실행시간 제한은
  후속 운영 작업이다. 이 단계는 기존 동작 보존을 위해 scanner를 변경하지 않았다.
  [Cloud Run request timeout](https://docs.cloud.google.com/run/docs/configuring/request-timeout)
- 애플리케이션 원문 로그 차단과 별개로 Cloud Run의 플랫폼 request log는 URL/IP 등 HTTP
  메타데이터를 포함할 수 있다. filename/내용/token을 URL에 넣지 않고, 실제 로그 접근권한·보관기간·
  제외 규칙은 배포 단계에서 검토해야 한다. 이 단계에서는 Cloud Logging을 구성하지 않았다.
  [Cloud Run logging](https://docs.cloud.google.com/run/docs/logging)
- mutable base image와 범위형 Python 의존성은 future rebuild 재현성을 보장하지 않는다.
  lock/hash 및 이미지 취약점 검사는 남아 있다. 검증한 image digest로 배포하더라도 보안 패치
  주기와 재검증은 필요하다. `pip check`는 취약점 검사가 아니다.
- max instance 설정은 엄격한 비용 상한이 아니다. 실제 budget/alert, revision 교체 중 instance,
  지연·메모리 관측, region/data-policy 판단과 운영 경보는 아직 구성하지 않았다.
  [Cloud Run maximum instances](https://docs.cloud.google.com/run/docs/configuring/max-instances)

## 검증 결과

최종 결과와 이미지 식별자는 `docs/MILESTONE_REVIEW.md`에 기록한다. 로컬 테스트
컨테이너는 검증 후 모두 제거하며, 빌드한 이미지는 후속 검토용으로 남긴다.
**이 문서를 작성한 단계는 배포 준비에서 멈춘다.**
