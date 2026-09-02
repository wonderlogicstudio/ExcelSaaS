from __future__ import annotations

from fastapi import FastAPI, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import formula_audit_is_available, get_settings
from .errors import WorkbookCareError
from .models import ErrorBody, ErrorResponse, FormulaAuditResult, ScanResult
from .recommendation_engine import add_finding_guidance, enrich_scan_result
from .scanner import run_formula_audit, scan_workbook

settings = get_settings()

app = FastAPI(
    title="WorkbookCare API",
    version="0.1.0",
    description=(
        "Static OOXML workbook diagnosis. "
        "Macros, formulas, and external links are never executed."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.exception_handler(WorkbookCareError)
async def workbookcare_error_handler(
    _request: Request,
    exc: WorkbookCareError,
) -> JSONResponse:
    payload = ErrorResponse(error=ErrorBody(code=exc.code, message=exc.message))
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "workbookcare-api"}


@app.post("/v1/scans", response_model=ScanResult)
async def create_scan(file: UploadFile) -> ScanResult:
    filename = file.filename or "workbook.xlsx"
    payload = await file.read(settings.max_upload_bytes + 1)
    if len(payload) > settings.max_upload_bytes:
        raise WorkbookCareError(
            "FILE_TOO_LARGE",
            f"파일은 {settings.max_upload_mb}MB 이하여야 합니다.",
            status_code=413,
        )
    return enrich_scan_result(scan_workbook(filename, payload, settings))


@app.post("/v1/formula-audits", response_model=FormulaAuditResult)
async def create_formula_audit(file: UploadFile) -> FormulaAuditResult:
    """Run a separately gated M4 internal-beta audit.

    This endpoint deliberately has no analysis ID or file-reuse mechanism. The
    current browser must re-send its in-memory File, and the server does not
    retain it after this response.
    """

    if not formula_audit_is_available(settings):
        raise WorkbookCareError(
            "FORMULA_AUDIT_NOT_AVAILABLE",
            "수식 패턴 정밀검사 내부 베타를 현재 환경에서 사용할 수 없습니다.",
            status_code=404,
        )

    filename = file.filename or "workbook.xlsx"
    payload = await file.read(settings.max_upload_bytes + 1)
    if len(payload) > settings.max_upload_bytes:
        raise WorkbookCareError(
            "FILE_TOO_LARGE",
            f"파일은 {settings.max_upload_mb}MB 이하여야 합니다.",
            status_code=413,
        )

    result = run_formula_audit(filename, payload, settings)
    return result.model_copy(update={"candidates": add_finding_guidance(result.candidates)})
