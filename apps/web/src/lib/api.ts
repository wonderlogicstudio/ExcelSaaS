import type { ApiErrorPayload, FormulaAuditResult, ScanResult } from '../types';

export function resolveApiBaseUrl(configuredBaseUrl: string | undefined, isProduction: boolean): string {
  const configured = configuredBaseUrl?.trim().replace(/\/$/, '');
  if (configured) {
    return configured;
  }
  // A hosted build cannot accidentally expose the Cloud Run origin merely
  // because a build variable was omitted. Local Vite development keeps its
  // explicit FastAPI default for the existing offline workflow.
  return isProduction ? '/api' : 'http://localhost:8000';
}

const apiBaseUrl = resolveApiBaseUrl(
  import.meta.env.VITE_API_BASE_URL as string | undefined,
  import.meta.env.PROD,
);

export class ScanApiError extends Error {
  readonly code: string;

  constructor(message: string, code = 'SCAN_FAILED') {
    super(message);
    this.name = 'ScanApiError';
    this.code = code;
  }
}

export async function scanWorkbook(file: File, signal?: AbortSignal): Promise<ScanResult> {
  const form = new FormData();
  form.append('file', file);

  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl}/v1/scans`, {
      method: 'POST',
      body: form,
      signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw error;
    }
    throw new ScanApiError(
      '분석 서버에 연결할 수 없습니다. 백엔드를 실행하거나 샘플 결과를 이용해 주세요.',
      'API_UNAVAILABLE',
    );
  }

  if (!response.ok) {
    let payload: ApiErrorPayload | undefined;
    try {
      payload = (await response.json()) as ApiErrorPayload;
    } catch {
      payload = undefined;
    }

    const message =
      payload?.error?.message ??
      payload?.detail ??
      '파일을 분석하지 못했습니다. 다른 파일로 다시 시도해 주세요.';
    const code = payload?.error?.code ?? `HTTP_${response.status}`;
    throw new ScanApiError(message, code);
  }

  return (await response.json()) as ScanResult;
}

export async function runFormulaAudit(
  file: File,
  signal?: AbortSignal,
): Promise<FormulaAuditResult> {
  const form = new FormData();
  form.append('file', file);

  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl}/v1/formula-audits`, {
      method: 'POST',
      body: form,
      signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw error;
    }
    throw new ScanApiError(
      '수식 패턴 정밀검사 서버에 연결할 수 없습니다. 기본 무료 진단 결과는 유지됩니다.',
      'FORMULA_AUDIT_UNAVAILABLE',
    );
  }

  if (!response.ok) {
    let payload: ApiErrorPayload | undefined;
    try {
      payload = (await response.json()) as ApiErrorPayload;
    } catch {
      payload = undefined;
    }
    throw new ScanApiError(
      payload?.error?.message
        ?? payload?.detail
        ?? '수식 패턴 정밀검사를 완료하지 못했습니다. 기본 무료 진단 결과는 유지됩니다.',
      payload?.error?.code ?? `HTTP_${response.status}`,
    );
  }

  return (await response.json()) as FormulaAuditResult;
}
