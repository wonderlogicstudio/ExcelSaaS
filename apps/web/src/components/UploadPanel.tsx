import { type ChangeEvent, type DragEvent, useRef, useState } from 'react';
import {
  ArrowRight,
  FileSpreadsheet,
  LockKeyhole,
  PlayCircle,
  ShieldCheck,
  UploadCloud,
} from 'lucide-react';

export type ScanStage =
  | '파일 형식 확인'
  | '워크북 구조 분석'
  | '수식과 참조 검사'
  | '위험도와 수정 가능 여부 계산';

interface UploadPanelProps {
  busy: boolean;
  stage: ScanStage | null;
  error: string | null;
  revalidationPending?: boolean;
  onFile: (file: File) => void;
  onDemo: () => void;
}

const allowedExtensions = ['xlsx', 'xlsm'];
const maxFileBytes = 10 * 1024 * 1024;

function validateFile(file: File): string | null {
  const extension = file.name.split('.').pop()?.toLowerCase() ?? '';
  if (!allowedExtensions.includes(extension)) {
    return '현재는 .xlsx와 .xlsm 파일만 검사할 수 있습니다.';
  }
  if (file.size > maxFileBytes) {
    return '현재 테스트 버전은 10MB 이하 파일만 지원합니다.';
  }
  if (file.size === 0) {
    return '비어 있는 파일은 검사할 수 없습니다.';
  }
  return null;
}

export function UploadPanel({
  busy,
  stage,
  error,
  revalidationPending = false,
  onFile,
  onDemo,
}: UploadPanelProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const chooseFile = (file?: File) => {
    if (!file) return;
    const validationError = validateFile(file);
    setLocalError(validationError);
    if (!validationError) onFile(file);
  };

  return (
    <aside className="upload-card" aria-label="엑셀 파일 검사 시작">
      <div className="upload-card__topline">
        <span className="status-dot" aria-hidden="true" />
        <span>{revalidationPending ? '수정 후 재검사 대기' : '무료 수식·구조 진단'}</span>
        <span className="upload-card__limit">최대 10MB</span>
      </div>

      <div
        className={`drop-zone${dragActive ? ' drop-zone--active' : ''}${busy ? ' drop-zone--busy' : ''}`}
        onDragEnter={(event: DragEvent<HTMLDivElement>) => {
          event.preventDefault();
          if (!busy) setDragActive(true);
        }}
        onDragOver={(event: DragEvent<HTMLDivElement>) => event.preventDefault()}
        onDragLeave={(event: DragEvent<HTMLDivElement>) => {
          event.preventDefault();
          if (event.currentTarget === event.target) setDragActive(false);
        }}
        onDrop={(event: DragEvent<HTMLDivElement>) => {
          event.preventDefault();
          setDragActive(false);
          if (!busy) chooseFile(event.dataTransfer.files[0]);
        }}
      >
        <input
          ref={inputRef}
          className="visually-hidden"
          type="file"
          accept=".xlsx,.xlsm"
          disabled={busy}
          onChange={(event: ChangeEvent<HTMLInputElement>) => {
            chooseFile(event.currentTarget.files?.[0]);
            event.currentTarget.value = '';
          }}
          aria-label="엑셀 파일 선택"
        />

        {busy ? (
          <div className="scan-progress" aria-live="polite">
            <span className="scan-progress__spinner" aria-hidden="true" />
            <strong>파일 구조와 수식 참조를 검사하고 있습니다.</strong>
            <span>{stage ?? '검사 준비'}</span>
            <div className="scan-progress__steps" aria-hidden="true">
              {[0, 1, 2, 3].map((item) => (
                <span key={item} className={stage ? 'is-active' : ''} />
              ))}
            </div>
          </div>
        ) : (
          <>
            <span className="drop-zone__icon" aria-hidden="true">
              <UploadCloud size={30} />
            </span>
            <strong>{revalidationPending ? '직접 수정한 테스트용 파일을 다시 선택하세요.' : '테스트용 Excel 파일을 놓아주세요.'}</strong>
            <span>{revalidationPending
              ? '이전 검사 결과와 같은 정적 규칙으로 비교합니다. 이전 원본 파일은 보관하지 않습니다.'
              : '.xlsx 또는 .xlsm · 민감한 실제 파일은 올리지 말고 샘플 결과로 먼저 확인하세요.'}</span>
            <button
              className="button button--primary button--wide"
              type="button"
              onClick={() => inputRef.current?.click()}
            >
              <FileSpreadsheet size={18} />
              {revalidationPending ? '수정 후 파일 선택' : '테스트용 파일 선택'}
              <ArrowRight size={17} />
            </button>
          </>
        )}
      </div>

      {(localError || error) && (
        <p className="form-error" role="alert">
          {localError ?? error}
        </p>
      )}

      <button className="demo-button" type="button" onClick={onDemo} disabled={busy}>
        <PlayCircle size={18} />
        민감한 파일 없이 샘플 진단 보기
      </button>

      <div className="upload-trust-grid" aria-label="파일 처리 원칙">
        <span>
          <ShieldCheck size={17} />
          원본 파일 미변경
        </span>
        <span>
          <LockKeyhole size={17} />
          매크로·외부 연결 실행 안 함
        </span>
      </div>
    </aside>
  );
}
