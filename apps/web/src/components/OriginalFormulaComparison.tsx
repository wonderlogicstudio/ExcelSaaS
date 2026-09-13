import { useEffect, useState } from 'react';
import type { Finding } from '../types';
import type { FormulaContext, OriginalCell } from '../lib/workbookEvidence';

export function OriginalFormulaComparison({ file, finding, active }: { file?: File | null; finding: Finding; active: boolean }) {
  const [context, setContext] = useState<FormulaContext | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    setContext(null); setFailed(false);
    if (!active || !file || !finding.formula_pattern) return;
    const controller = new AbortController();
    import('../lib/workbookEvidence').then(({ readFormulaContext }) => readFormulaContext(file, finding, controller.signal))
      .then(value => { if (!controller.signal.aborted) setContext(value); })
      .catch(() => { if (!controller.signal.aborted) setFailed(true); });
    return () => controller.abort();
  }, [active, file, finding.sheet, finding.cell, finding.formula_pattern]);
  if (!finding.formula_pattern || !active) return null;
  const cell = (item: OriginalCell, target: boolean) => <article className={`original-formula ${target ? 'original-formula--target' : ''}`} key={item.cell}>
    <h6>{target ? '확인할 셀' : '주변 반복 수식'} · {context?.sheet} {item.cell}</h6>
    <code data-original-cell={item.cell}>{item.type === 'text' ? `문자 “${item.text}”` : item.text}</code>
    {item.cached !== undefined && <p>파일에 저장된 결과 <span>{item.cached}</span> <small>재계산하지 않은 값</small></p>}
  </article>;
  return <section className="original-comparison" aria-label={`${finding.sheet} ${finding.cell} 원본 수식 비교`}>
    <h5>원본 수식 비교</h5>
    {!file ? <p>샘플 화면에는 원본 파일이 연결되어 있지 않습니다. 파일을 직접 검사하면 해당 셀과 비교 위치의 원문을 볼 수 있습니다.</p>
      : failed ? <p role="status">이 파일·브라우저에서는 원본 수식을 표시하지 못했습니다. 아래 비교 위치를 Excel에서 확인하세요. 검사 결과와 지원 판정은 바꾸지 않았습니다.</p>
        : !context ? <p role="status">선택한 파일에서 이 위치의 원문을 읽고 있습니다…</p>
          : <><div className="original-comparison__grid">{cell(context.target, true)}{context.comparisons.map(item => cell(item, false))}</div></>}
    <p className="original-comparison__difference"><strong>탐지한 차이</strong> {finding.formula_pattern.evidence_summary ?? finding.description}</p>
  </section>;
}
