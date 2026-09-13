import { useProductNavigation, routeTitles } from './lib/navigation';
import { reviewKey, type RepairDraft } from './lib/repairReview';
import { RepairReview } from './components/RepairReview';
import { CoreJourney, ServiceIntro } from './components/ProductPages';
import { useEffect, useRef, useState } from 'react';
import { ArrowRight, Check, FileSearch, ShieldCheck, Sparkles } from 'lucide-react';
import {DeliveryOperations} from './components/DeliveryOperations';
import { OrderHistory } from './components/OrderHistory';
import { ComparisonWorkspace } from './components/ComparisonWorkspace';
import './comparison.css';
import { DeliveryWorkspace } from './components/DeliveryWorkspace';
import './delivery.css';
import { Header } from './components/Header';
import { UploadPanel, type ScanStage } from './components/UploadPanel';
import { M25ResultsPanel as ResultsPanel } from './components/M25ResultsPanel';
import { FormulaAuditPanel, formulaAuditBlockedReason } from './components/FormulaAuditPanel';
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
import type { Finding, FindingUserStatus, FormulaAuditResult, ScanResult } from './types';

const formulaAuditInternalBetaEnabled =
  import.meta.env.VITE_FORMULA_AUDIT_INTERNAL_BETA_ENABLED === 'true';
const formulaAuditHostedBetaEnabled =
  import.meta.env.VITE_PRODUCT_ENV === 'hosted_beta'
  && import.meta.env.VITE_FORMULA_AUDIT_HOSTED_BETA_ENABLED === 'true';

const deliveryBetaEnabled = ['internal_beta', 'hosted_beta'].includes(import.meta.env.VITE_PRODUCT_ENV)
  && import.meta.env.VITE_DELIVERY_BETA_ENABLED === 'true';

const stages: ScanStage[] = [
  '파일 형식 확인',
  '워크북 구조 분석',
  '수식 문자열·참조 검사',
  '위험도와 수정 가능 여부 계산',
];

function wait(milliseconds: number) {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
}

export default function App() {
  const { path, navigate, onLink } = useProductNavigation();
  const diagnosisPage = path === '/' || path === '/diagnosis';
  const visited = useRef(new Set<string>());
  visited.current.add(path);
  const [reviewFindings, setReviewFindings] = useState<Finding[]>([]);
  const [reviewLocked, setReviewLocked] = useState(false);
  const [reviewDraft, setReviewDraft] = useState<RepairDraft>();
  const reviewSelection = { findings: reviewFindings, locked: reviewLocked, toggle: (finding: Finding) => {
    if (!reviewLocked) { setReviewDraft(undefined); setReviewFindings(current => current.some(f => reviewKey(f) === reviewKey(finding))
      ? current.filter(f => reviewKey(f) !== reviewKey(finding)) : [...current, finding]); }
  }};
  const clearReview = () => { setReviewFindings([]); setReviewLocked(false); setReviewDraft(undefined); };
  const uploadRef = useRef<HTMLDivElement>(null);
  const activeRequest = useRef(0);
  const activeController = useRef<AbortController | null>(null);
  useEffect(() => () => { activeController.current?.abort(); }, []);
  const [comparisonOpen, setComparisonOpen] = useState(false);
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
    !formulaAuditHostedBetaEnabled && formulaAuditInternalBetaEnabled
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
    if (result && diagnosisPage) {
      window.requestAnimationFrame(() => {
        const resultAnchor = formulaAuditInternalBetaEnabled && !formulaAuditHostedBetaEnabled && sourceFile
          ? '#formula-audit'
          : '#results';
        document.querySelector(resultAnchor)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    }
  }, [result, sourceFile]);

  const cancelActiveRequest = () => {
    activeRequest.current += 1;
    activeController.current?.abort();
    activeController.current = null;
    setBusy(false);
    setFormulaAuditBusy(false);
  };

  const executeFormulaAudit = async (file: File, requestId: number) => {
    if (requestId !== activeRequest.current) return;
    setFormulaAuditBusy(true);
    setFormulaAuditError(null);
    setFormulaAuditResult(null);
    setFormulaAuditStatuses({});
    try {
      const audit = await runFormulaAudit(file, activeController.current?.signal);
      if (requestId === activeRequest.current) setFormulaAuditResult(audit);
    } catch (auditError) {
      if (requestId !== activeRequest.current) return;
      const message = auditError instanceof ScanApiError
        ? auditError.message
        : '수식 패턴 정밀검사를 완료하지 못했습니다. 기본 무료 진단 결과는 유지됩니다.';
      setFormulaAuditError(message);
    } finally {
      if (requestId === activeRequest.current) setFormulaAuditBusy(false);
    }
  };

  const startUpload = () => {
    if (!diagnosisPage) navigate('/');
    const reveal = () => {
      uploadRef.current?.scrollIntoView({ behavior: window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'center' });
      uploadRef.current?.querySelector<HTMLButtonElement>('button')?.focus({ preventScroll: true });
    };
    if (diagnosisPage) reveal(); else requestAnimationFrame(reveal);
  };

  const runDemo = async () => {
    if (!diagnosisPage) navigate('/');
    clearReview();
    cancelActiveRequest();
    const requestId = activeRequest.current;
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
    if (requestId !== activeRequest.current) return;
    const scan = { ...demoResult, scanned_at: new Date().toISOString() };
    setResult(scan);
    setRevalidationComparison(previousResult ? compareScanResults(previousResult, scan) : null);
    setPreviousResult(null);
    setBusy(false);
  };

  const runFileScan = async (file: File) => {
    clearReview();
    cancelActiveRequest();
    const requestId = activeRequest.current;
    activeController.current = new AbortController();
    setFindingStatuses({});
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
      const scan = await scanWorkbook(file, activeController.current.signal);
      if (requestId !== activeRequest.current) return;
      setStageIndex(stages.length - 1);
      setResult(scan);
      setSourceFile(file);
      setRevalidationComparison(previousResult ? compareScanResults(previousResult, scan) : null);
      setPreviousResult(null);
      setBusy(false);
      if (formulaAuditHostedBetaEnabled && !formulaAuditBlockedReason(scan, file)) {
        await executeFormulaAudit(file, requestId);
      }
    } catch (scanError) {
      if (requestId !== activeRequest.current) return;
      const message =
        scanError instanceof ScanApiError
          ? scanError.message
          : '파일을 분석하지 못했습니다. 잠시 후 다시 시도해 주세요.';
      setError(message);
    } finally {
      if (requestId === activeRequest.current) setBusy(false);
    }
  };

  const reset = () => {
    clearReview();
    cancelActiveRequest();
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
    clearReview();
    cancelActiveRequest();
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
    if (!sourceFile || !result || formulaAuditBusy || formulaAuditBlockedReason(result, sourceFile)) return;
    activeController.current?.abort();
    activeController.current = new AbortController();
    const requestId = ++activeRequest.current;
    await executeFormulaAudit(sourceFile, requestId);
  };

  const updateFormulaAuditStatus = (findingKey: string, status: FindingUserStatus) => {
    setFormulaAuditStatuses((current) => ({ ...current, [findingKey]: status }));
  };

  return (
    <div id="top" onClick={onLink}>
      <Header onStart={startUpload} path={path}/>
      <main id="main-content" tabIndex={-1}>
        <div data-product-page="diagnosis" hidden={!diagnosisPage}>
        <section className="hero" id="free-diagnosis" aria-labelledby="hero-title">
          <div className="hero__glow hero__glow--one" aria-hidden="true" />
          <div className="hero__glow hero__glow--two" aria-hidden="true" />
          <div className="shell hero__layout">
            <div className="hero__copy">
              <div className="hero__eyebrow">
                <Sparkles size={16} />
                Excel 진단에서 승인 기반 수정까지
              </div>
              <h1 id="hero-title" tabIndex={-1}>
                Excel 문제를 확인하고,
                <br />
                <span>승인한 변경만 반영하세요.</span>
              </h1>
              <p className="hero__lead">
                파일을 올려 위치와 근거를 확인하고, 수정 검토할 항목을 선택하세요.
                {deliveryBetaEnabled ? ' 지원 범위와 정확한 변경계획을 별도로 승인하면 원본과 분리된 수정본·변경내역·재검증 보고서를 받습니다.' : ' 승인 기반 수정과 세 파일 납품은 준비 중입니다.'}
              </p>
              <div className="hero__trust" aria-label="서비스 핵심 원칙">
                <span><Check size={16} /> 무료 진단</span>
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
                {formulaAuditHostedBetaEnabled
                  ? '파일을 한 번 올리면 구조 위험과 수식 패턴을 검사하고, 확인할 항목을 한 목록으로 보여드립니다. '
                  : '현재는 파일 구조를 정적으로 분석합니다. 수식 패턴 이탈·누락 검사는 무료 진단에 포함되지 않습니다.'}
                VBA, 외부 연결, 수식 계산은 실행하지 않으며 원본 파일도 바꾸지 않습니다.
              </p>
              <p className="hero__beta-notice">
                {deliveryBetaEnabled ? '보호 베타 · 등록된 합성 파일의 수정 시험만 제공 · 일반 구매·실제 결제 준비 중. ' : '테스트용 파일만 사용하세요. '}
                <a href="/help#file-handling-principles">파일 처리 원칙</a>
              </p>
            </div>
            <div ref={uploadRef} className="hero__upload">
              <UploadPanel
                busy={busy || (formulaAuditHostedBetaEnabled && formulaAuditBusy)}
                stage={formulaAuditHostedBetaEnabled && formulaAuditBusy ? '수식 패턴 확인' : busy ? stages[stageIndex] : null}
                error={error}
                revalidationPending={previousResult !== null}
                onFile={runFileScan}
                onDemo={runDemo}
              />
            </div>
          </div>
        </section>

        <CoreJourney/>
        {result && (
          <>
            {formulaAuditInternalBetaEnabled && !formulaAuditHostedBetaEnabled && (
              <FormulaAuditPanel
                automatic={formulaAuditHostedBetaEnabled}
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
              reviewSelection={reviewSelection}
              formulaAudit={formulaAuditHostedBetaEnabled ? {
                result: formulaAuditResult, busy: formulaAuditBusy, error: formulaAuditError,
                blockedReason: formulaAuditBlockedReason(result, sourceFile),
                statuses: formulaAuditStatuses, onRetry: runCurrentFormulaAudit,
                onStatusChange: updateFormulaAuditStatus,
              } : undefined}
              isDemo={isDemo}
              statuses={findingStatuses}
              revalidationComparison={revalidationComparison}
              onStatusChange={updateFindingStatus}
              feedbackRepository={feedbackRepository}
              onPrepareRevalidation={prepareRevalidation}
              onReset={reset}
            />
            <RepairReview selection={reviewSelection} available={deliveryBetaEnabled} hasFile={Boolean(sourceFile)} onPrepare={draft => setReviewDraft(draft)}/>
            {deliveryBetaEnabled && sourceFile && <DeliveryWorkspace key={`${result.analysis_id}:${reviewDraft ? JSON.stringify(reviewDraft) : 'manual'}`} file={sourceFile} compactEntry reviewDraft={reviewDraft} onSourceFixed={setReviewLocked}/> }
          </>
        )}
        {!result && <div className="core-next shell"><p>먼저 무료 진단으로 확인할 항목을 찾으세요. 두 자료 비교와 추가 검증은 별도 서비스에서 확인할 수 있습니다.</p><a href="/help">검사 범위와 이용 방법</a></div>}
        </div>
        <div data-product-page="precision" hidden={path !== '/precision-verification'}>{path === '/precision-verification' && <ServiceIntro kind="precision" patterns={formulaAuditHostedBetaEnabled} delivery={deliveryBetaEnabled} onStart={startUpload}/>}</div>
        <div data-product-page="compare" hidden={path !== '/compare'}>{path === '/compare' && <ServiceIntro kind="compare" patterns={formulaAuditHostedBetaEnabled} delivery={deliveryBetaEnabled} onStart={startUpload}/>}
          {deliveryBetaEnabled && visited.current.has('/compare') && <ComparisonWorkspace open={comparisonOpen} onOpen={() => setComparisonOpen(true)} />}
        </div>
        <div data-product-page="automation" hidden={path !== '/automation'}>{path === '/automation' && <ServiceIntro kind="automation" patterns={formulaAuditHostedBetaEnabled} delivery={deliveryBetaEnabled} onStart={startUpload}/>}</div>
        <div data-product-page="repair" hidden={path !== '/repair'}>{path === '/repair' && <ServiceIntro kind="repair" patterns={formulaAuditHostedBetaEnabled} delivery={deliveryBetaEnabled} onStart={startUpload}/>}</div>
        <div data-product-page="help" hidden={path !== '/help'}>{path === '/help' && <><div className="service-intro shell"><span className="section-kicker">도움말</span><h1 tabIndex={-1}>검사 범위와 이용 방법</h1><p>무료 결과를 이해하고, 수정·비교의 제공 범위와 파일 처리 원칙을 확인하세요.</p><div className="help-links"><a href="/help#service-scope">서비스 범위</a><a href="/help#file-handling-principles">파일 처리 원칙</a><a href="/help#faq">자주 묻는 질문</a>{deliveryBetaEnabled && <a href="/orders">베타 주문 확인</a>}</div></div>
          <StaticSections products={result?.products} onStart={startUpload} onDemo={runDemo} onCompare={deliveryBetaEnabled ? () => navigate('/compare') : undefined}/>
          {deliveryBetaEnabled && <DeliveryOperations onNewInput={startUpload}/>}</>}
        </div>
        <div data-product-page="orders" hidden={path !== '/orders'}><div className="service-intro shell"><h1 tabIndex={-1}>베타 주문 확인</h1><p>이 브라우저 소유자로 확인되는 기존 시험 주문만 조회합니다. 파일·계획·결과는 임시 보관이며, 현재 일반 구매나 영속적인 내 작업 보관함은 제공하지 않습니다.</p></div>{deliveryBetaEnabled && visited.current.has('/orders') ? <OrderHistory/> : <p className="shell">주문 기능 준비 중</p>}</div>
        <div data-product-page="privacy" hidden={path !== '/privacy'}>{path === '/privacy' && <LegalPage kind="privacy" embedded/>}</div>
        <div data-product-page="terms" hidden={path !== '/terms'}>{path === '/terms' && <LegalPage kind="terms" embedded/>}</div>
        {!routeTitles[path] && <div data-product-page="missing" className="service-intro shell"><h1 tabIndex={-1}>페이지를 찾을 수 없습니다</h1><p>주소를 확인하거나 무료 진단으로 돌아가세요.</p><a href="/" className="button button--primary">무료 진단으로 돌아가기</a></div>}
      </main>
      <Footer deliveryEnabled={deliveryBetaEnabled} />
    </div>
  );
}
