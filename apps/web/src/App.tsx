import { useEffect, useRef, useState } from 'react';
import { ArrowRight, Check, FileSearch, ShieldCheck, Sparkles } from 'lucide-react';
import { Header } from './components/Header';
import { UploadPanel, type ScanStage } from './components/UploadPanel';
import { M25ResultsPanel as ResultsPanel } from './components/M25ResultsPanel';
import { FormulaAuditPanel } from './components/FormulaAuditPanel';
import { StaticSections } from './components/StaticSections';
import { Footer } from './components/Footer';
import { LegalPage } from './components/LegalPage';
import { demoResult } from './data/demo';
import { runFormulaAudit, scanWorkbook, ScanApiError } from './lib/api';
import { compareScanResults } from './lib/revalidation';
import {
  feedbackCaptureEnabled,
  HostedFormulaAuditFeedbackRepository,
  hostedFormulaAuditFeedbackEnabled,
  LocalFeedbackRepository,
} from './lib/feedback';
import type { FindingUserStatus, FormulaAuditResult, ScanResult } from './types';

const formulaAuditInternalBetaEnabled =
  import.meta.env.VITE_FORMULA_AUDIT_INTERNAL_BETA_ENABLED === 'true';

const stages: ScanStage[] = [
  '파일 형식 확인',
  '워크북 구조 분석',
  '수식과 참조 검사',
  '위험도와 수정 가능 여부 계산',
];

function wait(milliseconds: number) {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
}

export default function App() {
  if (window.location.pathname === '/privacy') {
    return <LegalPage kind="privacy" />;
  }
  if (window.location.pathname === '/terms') {
    return <LegalPage kind="terms" />;
  }
  const uploadRef = useRef<HTMLDivElement>(null);
  const [busy, setBusy] = useState(false);
  const [stageIndex, setStageIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [isDemo, setIsDemo] = useState(false);
  const [previousResult, setPreviousResult] = useState<ScanResult | null>(null);
  const [revalidationComparison, setRevalidationComparison] = useState<ReturnType<typeof compareScanResults> | null>(null);
  const [findingStatuses, setFindingStatuses] = useState<Record<string, FindingUserStatus>>({});
  const [sourceFile, setSourceFile] = useState<File | null>(null);
  const [formulaAuditResult, setFormulaAuditResult] = useState<FormulaAuditResult | null>(null);
  const [formulaAuditBusy, setFormulaAuditBusy] = useState(false);
  const [formulaAuditError, setFormulaAuditError] = useState<string | null>(null);
  const [formulaAuditStatuses, setFormulaAuditStatuses] = useState<Record<string, FindingUserStatus>>({});
  const [feedbackRepository] = useState(() => (
    feedbackCaptureEnabled ? new LocalFeedbackRepository() : null
  ));
  const [formulaAuditFeedbackRepository] = useState(() => (
    formulaAuditInternalBetaEnabled
      ? hostedFormulaAuditFeedbackEnabled
        ? new HostedFormulaAuditFeedbackRepository()
        : new LocalFeedbackRepository()
      : null
  ));

  useEffect(() => {
    if (!busy) return;
    const timer = window.setInterval(() => {
      setStageIndex((current) => Math.min(current + 1, stages.length - 1));
    }, 700);
    return () => window.clearInterval(timer);
  }, [busy]);

  useEffect(() => {
    if (result) {
      window.requestAnimationFrame(() => {
        const resultAnchor = formulaAuditInternalBetaEnabled && sourceFile
          ? '#formula-audit'
          : '#results';
        document.querySelector(resultAnchor)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    }
  }, [result, sourceFile]);

  const startUpload = () => {
    uploadRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  };

  const runDemo = async () => {
    setError(null);
    setResult(null);
    setIsDemo(true);
    setSourceFile(null);
    setFormulaAuditResult(null);
    setFormulaAuditError(null);
    setFormulaAuditStatuses({});
    setStageIndex(0);
    setBusy(true);
    await wait(2100);
    const scan = { ...demoResult, scanned_at: new Date().toISOString() };
    setResult(scan);
    setRevalidationComparison(previousResult ? compareScanResults(previousResult, scan) : null);
    setPreviousResult(null);
    setBusy(false);
  };

  const runFileScan = async (file: File) => {
    setError(null);
    setResult(null);
    setIsDemo(false);
    setSourceFile(null);
    setFormulaAuditResult(null);
    setFormulaAuditError(null);
    setFormulaAuditStatuses({});
    setStageIndex(0);
    setBusy(true);

    try {
      const scan = await scanWorkbook(file);
      setStageIndex(stages.length - 1);
      setResult(scan);
      setSourceFile(file);
      setRevalidationComparison(previousResult ? compareScanResults(previousResult, scan) : null);
      setPreviousResult(null);
    } catch (scanError) {
      const message =
        scanError instanceof ScanApiError
          ? scanError.message
          : '파일을 분석하지 못했습니다. 잠시 후 다시 시도해 주세요.';
      setError(message);
    } finally {
      setBusy(false);
    }
  };

  const reset = () => {
    setResult(null);
    setError(null);
    setIsDemo(false);
    setPreviousResult(null);
    setRevalidationComparison(null);
    setFindingStatuses({});
    setSourceFile(null);
    setFormulaAuditResult(null);
    setFormulaAuditError(null);
    setFormulaAuditStatuses({});
    window.requestAnimationFrame(startUpload);
  };

  const prepareRevalidation = () => {
    if (!result) return;
    setPreviousResult(result);
    setResult(null);
    setError(null);
    setRevalidationComparison(null);
    setSourceFile(null);
    setFormulaAuditResult(null);
    setFormulaAuditError(null);
    setFormulaAuditStatuses({});
    window.requestAnimationFrame(startUpload);
  };

  const updateFindingStatus = (findingKey: string, status: FindingUserStatus) => {
    setFindingStatuses((current) => ({ ...current, [findingKey]: status }));
  };

  const runCurrentFormulaAudit = async () => {
    if (!sourceFile || !result || formulaAuditBusy) return;
    setFormulaAuditBusy(true);
    setFormulaAuditError(null);
    try {
      setFormulaAuditResult(await runFormulaAudit(sourceFile));
    } catch (auditError) {
      const message = auditError instanceof ScanApiError
        ? auditError.message
        : '수식 패턴 정밀검사를 완료하지 못했습니다. 기본 무료 진단 결과는 유지됩니다.';
      setFormulaAuditError(message);
      setFormulaAuditResult(null);
    } finally {
      setFormulaAuditBusy(false);
    }
  };

  const updateFormulaAuditStatus = (findingKey: string, status: FindingUserStatus) => {
    setFormulaAuditStatuses((current) => ({ ...current, [findingKey]: status }));
  };

  return (
    <div id="top">
      <Header onStart={startUpload} />
      <main>
        <section className="hero" id="free-diagnosis" aria-labelledby="hero-title">
          <div className="hero__glow hero__glow--one" aria-hidden="true" />
          <div className="hero__glow hero__glow--two" aria-hidden="true" />
          <div className="shell hero__layout">
            <div className="hero__copy">
              <div className="hero__eyebrow">
                <Sparkles size={16} />
                중요한 Excel 사용·공유 전 점검 · 현재 베타
              </div>
              <h1 id="hero-title">
                문제를 찾고,
                <br />
                <span>수정 방향을 정리하세요.</span>
              </h1>
              <p className="hero__lead">
                무료 진단은 깨진 수식 표기, 외부 통합문서 참조, 숨김 시트 같은 구조 위험 신호를 찾습니다.
                중요한 파일을 사용하거나 공유하기 전에, 고칠 방법을 더 확인해야 하는 항목과 수정 여부를 판단할 근거를 먼저 보여드립니다.
              </p>
              <div className="hero__trust" aria-label="서비스 핵심 원칙">
                <span><Check size={16} /> 가입 없이 시작</span>
                <span><ShieldCheck size={16} /> 원본 파일 변경 없음</span>
                <span><FileSearch size={16} /> 규칙 기반 무료 진단</span>
              </div>
              <div className="hero__actions">
                <button className="button button--primary" type="button" onClick={startUpload}>
                  테스트용 파일 무료 진단 <ArrowRight size={18} />
                </button>
                <button className="button button--ghost" type="button" onClick={runDemo}>
                  샘플 결과 보기
                </button>
              </div>
              <p className="hero__fineprint">
                현재는 파일 구조를 정적으로 분석합니다. VBA, 외부 연결, 수식 계산은 실행하지 않으며 원본 파일도
                바꾸지 않습니다.
              </p>
              <p className="hero__beta-notice">
                Beta 안내: 결과는 참고 정보이며 원본 파일은 수정하지 않습니다.{' '}
                <a href="/privacy">파일 처리 안내</a> · <a href="/terms">이용 안내</a>
              </p>
            </div>
            <div ref={uploadRef} className="hero__upload">
              <UploadPanel
                busy={busy}
                stage={busy ? stages[stageIndex] : null}
                error={error}
                revalidationPending={previousResult !== null}
                onFile={runFileScan}
                onDemo={runDemo}
              />
            </div>
          </div>
        </section>

        {result && (
          <>
            {formulaAuditInternalBetaEnabled && (
              <FormulaAuditPanel
                baseResult={result}
                sourceFile={sourceFile}
                auditResult={formulaAuditResult}
                busy={formulaAuditBusy}
                error={formulaAuditError}
                statuses={formulaAuditStatuses}
                feedbackRepository={formulaAuditFeedbackRepository}
                onRun={runCurrentFormulaAudit}
                onStatusChange={updateFormulaAuditStatus}
              />
            )}
            <ResultsPanel
              result={result}
              isDemo={isDemo}
              statuses={findingStatuses}
              revalidationComparison={revalidationComparison}
              onStatusChange={updateFindingStatus}
              feedbackRepository={feedbackRepository}
              onPrepareRevalidation={prepareRevalidation}
              onReset={reset}
            />
          </>
        )}
        <StaticSections onStart={startUpload} onDemo={runDemo} />
      </main>
      <Footer />
    </div>
  );
}
