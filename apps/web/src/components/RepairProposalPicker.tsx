import { useEffect, useRef, useState } from 'react';
import type { Finding } from '../types';
import type { OriginalCell } from '../lib/workbookEvidence';
import { monthlyFormulaFromText, type RepairDraft, type ReviewSelection } from '../lib/repairReview';
import { proposalGroups, RP01, RP02, RP03, type RepairIntent, type RepairProposal } from '../lib/repairProposals';
const COMBINED='COMBINED_RP01_RP02_REPAIR_V1';

type BasketItem = { id:string; title:string; draft:RepairDraft; draftKey:string; kindLabel:string; cellCount:number };
const draftKey=(draft:RepairDraft)=>JSON.stringify([draft.profile,draft.sheet,draft.targets,draft.role??'',draft.anchor??'',draft.anchor_formula??'',draft.before_formula??'']);
const basketId=(proposal:RepairProposal)=>proposal.id;
const kindLabel=(profile:string)=>profile===RP01?'숫자 텍스트 정리':profile===RP03?'월별 수식 검증':'빈 셀 수식 복원';
const basketRemoveLabel=(item:BasketItem)=>`${item.draft.sheet} ${item.draft.targets[0]?.replace(/[0-9].*$/,'') || ''}열 ${item.kindLabel} ${item.cellCount}곳 제외`;
const isMonthlyItem=(item:BasketItem)=>item.draft.profile===RP03;

function ProposalDetail({ proposal, file, intent, onPrepare, basketItem, onBasketChange, onBasketRemove }: { proposal: RepairProposal; file: File; intent: RepairIntent; onPrepare: (draft: RepairDraft) => void; basketItem?: BasketItem; onBasketChange: (item: BasketItem) => void; onBasketRemove: (id: string) => void }) {
  const [targets, setTargets] = useState(proposal.findings.slice(0, 50).map(f => f.cell!).filter(Boolean));
  const [role, setRole] = useState(''), [confirmed, setConfirmed] = useState(false), [anchor, setAnchor] = useState('');
  const [cells, setCells] = useState<OriginalCell[]>([]), [loading, setLoading] = useState(true), [error, setError] = useState(false);
  const first = proposal.findings.find(f => f.cell === targets[0]) ?? proposal.findings[0];
  const requestedAnchor = intent.enabled && intent.kind === 'same_formula' && intent.sheet === proposal.sheet ? intent.anchor : '';
  const refs = proposal.profile === RP03 ? [] : [...new Set([requestedAnchor, ...(first.formula_pattern?.comparison_locations ?? []), ...(first.formula_pattern?.evidence_locations ?? [])])]
    .filter(c => /^[A-Z]{1,3}[1-9][0-9]{0,6}$/.test(c) && !targets.includes(c)).slice(0, 6);
  const topCells = Array.from({length: Math.min(8,Math.max(0,Number(first.cell?.replace(/^[A-Z]+/,''))-1))},(_,i)=>proposal.column+(i+1));
  const requestedCells = [...new Set([first.cell!, ...refs, ...topCells])]; const evidenceKey = requestedCells.join(',');
  useEffect(() => {
    const c = new AbortController(); setCells([]); setLoading(true); setError(false); setAnchor(''); setConfirmed(false);
    import('../lib/workbookEvidence').then(m => m.readSourceCells(file, proposal.sheet, requestedCells, c.signal)).then(v => {
      if (!c.signal.aborted) { setCells(v); const recommended = v.find(x => refs.includes(x.cell) && x.type === 'formula' && x.cell !== first.cell && (!requestedAnchor || x.cell === requestedAnchor)); setAnchor(recommended?.cell ?? ''); }
    }).catch(() => { if (!c.signal.aborted) setError(true); }).finally(() => { if (!c.signal.aborted) setLoading(false); });
    return () => c.abort();
  }, [file, proposal.id, evidenceKey]);
  const source = cells.find(c => c.cell === first.cell), formula = cells.find(c => c.cell === anchor && c.type === 'formula');
  const beforeFormula = proposal.profile === RP03 && source?.type === 'formula' ? monthlyFormulaFromText(source.text) : undefined;
  const anchorChoices = cells.filter(c => refs.includes(c.cell) && c.type === 'formula' && c.cell !== first.cell);
  const columnText = cells.filter(c => topCells.includes(c.cell) && c.type === 'text' && c.text.trim() && !/^[\d\s,.-]+$/.test(c.text)).at(-1);
  const canPrepare = targets.length > 0 && !loading && !error && (proposal.profile === RP01 ? confirmed && ['AMOUNT', 'QUANTITY'].includes(role) : proposal.profile === RP03 ? targets.length === 1 && !!beforeFormula : confirmed && !!formula);
  const draft:RepairDraft={ profile: proposal.profile!, sheet: proposal.sheet, targets, confirmed: true, proposal: true };
  if (proposal.profile === RP01) draft.role = role;
  if (proposal.profile === RP02) { draft.anchor = anchor; draft.anchor_formula = formula?.text ?? ''; }
  if (proposal.profile === RP03 && beforeFormula) draft.before_formula = beforeFormula;
  const currentKey=draftKey(draft), isAdded=basketItem?.draftKey===currentKey, needsUpdate=!!basketItem && !isAdded;
  const addLabel=isAdded?'✓ 추가됨':needsUpdate?'목록 업데이트':'변경 목록에 추가';
  const saveToBasket=()=>onBasketChange({id:basketId(proposal),title:proposal.title,draft,draftKey:currentKey,kindLabel:kindLabel(proposal.profile!),cellCount:targets.length});
  return <section className="proposal-details" aria-label={`${proposal.sheet} ${proposal.column}의 제안`}>
    <h3>{proposal.title}</h3><p>{proposal.explanation}</p>
    <p><strong>{proposal.sheet} · {proposal.column}열 · 제안 위치 {proposal.findings.length}곳</strong></p>
    {columnText && <p className="proposal-column-name">{proposal.column}열의 왼쪽 설명: <strong>{columnText.text}</strong></p>}
    {loading ? <p role="status">이 위치의 실제 원본을 확인하고 있습니다.</p> : error ? <p role="status">원본 예시를 읽지 못했습니다. 무료 진단 근거는 유지합니다. 파일 또는 브라우저를 확인한 뒤 다시 검사하세요.</p> : source && <div className="proposal-source"><span>원본 예시 · {proposal.sheet} {source.cell}</span><strong>{source.type === 'text' ? `문자 “${source.text}”` : source.type === 'blank' ? '비어 있는 칸' : source.text}</strong><small>아직 수정안의 계산 결과가 아닙니다.</small></div>}
    <details className="proposal-targets"><summary>제안할 위치 선택·제외 ({targets.length}곳 선택)</summary>
      <p>{proposal.profile===RP03?'월별 수식 후보는 서버 검증을 위해 한 번에 한 칸만 보낼 수 있습니다.':'선택한 위치만 검토합니다. 시트 전체의 사이즈 때문에 자동으로 포함하지 않습니다.'}</p>
      <div className="proposal-cell-list">{proposal.findings.slice(0, 50).map(f => <label key={f.cell}><input type="checkbox" checked={targets.includes(f.cell!)} disabled={proposal.profile===RP03 && targets.includes(f.cell!)} onChange={e => { setConfirmed(false); setTargets(t => proposal.profile===RP03 ? (e.target.checked ? [f.cell!] : []) : e.target.checked ? [...t, f.cell!].sort((a,b)=>a.localeCompare(b,'en',{numeric:true})) : t.filter(c => c !== f.cell)); }}/>{f.cell}</label>)}</div>
      {proposal.findings.length > 50 && <p>한 번에 표시할 50곳까지만 제안합니다. 나머지 위치는 다음 검사에서 선택하세요. 수정 엔진은 최종 한도를 별도 검토합니다.</p>}
    </details>
    {proposal.profile === RP01 ? <fieldset className="proposal-purpose"><legend>이 숫자는 어떤 용도인가요?</legend>
      <p>계산해야 할 숫자만 바꿉니다. 고객번호처럼 구분하는 번호는 문자로 남겨야 합니다.</p>
      {[["AMOUNT", "금액", "매출·비용·정산액처럼 더하거나 뺄 값"], ["QUANTITY", "개수·수량", "상품 수나 인원처럼 계산할 개수"], ["ID", "구분하는 번호", "고객번호·계좌·전화번호·우편번호"]].map(([value,label,help]) => <label key={value}><input type="radio" name={`purpose-${proposal.id}`} value={value} checked={role === value} onChange={() => { setRole(value); setConfirmed(false); }}/><span><strong>{label}</strong><small>{help}</small></span></label>)}
      {role === 'ID' && <p role="status">구분하는 번호는 수정하지 않습니다. 앞자리나 원래 표기를 보존하세요.</p>}
    </fieldset> : proposal.profile === RP03 ? <div className="proposal-anchor">
      <p><strong>검증 필요 후보입니다.</strong> 서버가 같은 원본에서 실제 #VALUE! 오류와 앞뒤 월 값을 다시 계산한 뒤에만 계획을 만듭니다.</p>
      {beforeFormula ? <details open><summary>진단 근거의 원본 수식</summary><code>{beforeFormula}</code><p>이 수식은 사용자가 입력하지 않고 업로드한 원본에서 읽은 수식입니다.</p></details> : <p role="status">진단 결과에 원본 수식 증거가 없어 아직 제안할 수 없습니다.</p>}
    </div> : <div className="proposal-anchor"><label>어느 칸과 같은 방식으로 계산할까요?<select value={anchor} onChange={e => { setAnchor(e.target.value); setConfirmed(false); }}><option value="">기준 셀을 선택하세요</option>{anchorChoices.map(c => <option key={c.cell} value={c.cell}>{c.cell} · 원본의 계산 칸{c.cached ? ` (저장값 ${c.cached})` : ''}</option>)}</select></label>
      <p>주변 수식은 기준 후보입니다. 같은 계산이어야 하는 대상인지 확인하세요. 저장값을 그대로 복사하지 않고 대상 행에 맞게 참조를 옮깁니다.</p>
      {formula && <details><summary>선택한 기준의 원본 수식 확인</summary><code>{formula.text}</code><p>저장된 결과를 재계산한 값이 아닙니다.</p></details>}
      {!loading && !formula && <p>유효한 기준 수식이 없어 아직 수정안을 제안할 수 없습니다. 요청한 대상에 실제 수식이 있는지 확인하세요.</p>}
    </div>}
    {proposal.profile !== RP03 && <label className="delivery-check"><input type="checkbox" checked={confirmed} disabled={loading || error || !targets.length || (proposal.profile === RP01 ? !['AMOUNT','QUANTITY'].includes(role) : !formula)} onChange={e => setConfirmed(e.target.checked)}/>{proposal.profile === RP01 ? '선택한 칸은 계산할 금액·개수입니다. 문자 숫자를 계산에 포함하는 제안을 확인하겠습니다.' : '선택한 빈 칸도 이 기준 칸과 같은 업무 계산이어야 합니다.'}</label>}
    {needsUpdate && <p className="proposal-basket-warning" role="status">기준이나 대상이 바뀌었습니다. 목록은 아직 이전 선택을 보관하고 있습니다.</p>}
    <div className="proposal-action-row">
      <button className={isAdded ? 'button proposal-added-button' : 'button button--primary'} type="button" disabled={!canPrepare || isAdded} onClick={saveToBasket}>{addLabel}</button>
      {(isAdded||needsUpdate) && <button className="button button--outline" type="button" onClick={() => onBasketRemove(basketId(proposal))}>되돌리기</button>}
      <button className="button button--outline proposal-secondary-preview" type="button" disabled={!canPrepare} onClick={() => onPrepare(draft)}>{proposal.profile === RP03 ? '선택한 월별 수식 서버 검증으로 변경 예시 확인' : '이 묶음만 변경 예시 확인'}</button>
    </div>
    <p className="proposal-footnote">제안 선택은 변경 승인이 아닙니다. 파일 보존·수정 범위·계산이 검증된 경우에만 실제 변경 예시를 보여드립니다.</p>
  </section>;
}
export function RepairProposalPicker({ findings, sheets, file, selection, intent, available, onPrepare }: { findings: Finding[]; sheets: string[]; file: File | null; selection: ReviewSelection; intent: RepairIntent; available: boolean; onPrepare: (draft: RepairDraft) => void }) {
  const [selectedOnly, setSelectedOnly] = useState(selection.findings.length > 0), [chosenSheet, setChosenSheet] = useState(''), [active, setActive] = useState('');
  const [basket,setBasket]=useState<BasketItem[]>([]), [notice,setNotice]=useState('');
  const selectionKey = selection.findings.map(f => JSON.stringify([f.rule_code,f.sheet,f.cell])).join('|');
  const previousSelectionKey = useRef(selectionKey);
  useEffect(() => {
    setSelectedOnly(selection.findings.length > 0); setActive('');
    if (previousSelectionKey.current !== selectionKey) {
      setBasket([]);
      if (previousSelectionKey.current) setNotice('1단계 선택이 바뀌어 기존 수정 목록을 비웠습니다.');
      previousSelectionKey.current = selectionKey;
    }
  }, [selectionKey, selection.findings.length]);
  const addToBasket=(item:BasketItem)=>setBasket(old=>{
    if (isMonthlyItem(item) && old.some(existing=>existing.id!==item.id)) { setNotice('월별 수식 후보는 다른 수정 묶음과 함께 보낼 수 없습니다. 기존 목록은 유지했습니다.'); return old; }
    if (!isMonthlyItem(item) && old.some(isMonthlyItem)) { setNotice('월별 수식 후보가 목록에 있어 다른 수정 묶음을 함께 보낼 수 없습니다. 기존 목록은 유지했습니다.'); return old; }
    setNotice(`${item.title} ${item.cellCount}곳이 목록에 추가됐습니다.`);return [...old.filter(existing=>existing.id!==item.id),item];});
  const removeFromBasket=(id:string)=>setBasket(old=>{const removed=old.find(item=>item.id===id); if(removed)setNotice(`${removed.title} 묶음을 목록에서 제외했습니다.`); return old.filter(item=>item.id!==id);});
  const clearBasket=()=>{setBasket([]);setNotice('수정 목록을 비웠습니다.');};
  const prepareBasket=()=>{if(!basket.length)return; if(basket.length>1&&basket.some(isMonthlyItem)){setNotice('월별 수식 후보는 단일 대상만 검증할 수 있습니다. 기존 목록은 유지했습니다.');return;} const items=basket.map(item=>item.draft);onPrepare(items.length===1?items[0]:{profile:COMBINED,sheet:items[0].sheet,targets:items.flatMap(item=>item.targets),confirmed:true,proposal:true,items});};
  const chosen = selectedOnly && selection.findings.length ? selection.findings : findings;
  const groups = proposalGroups(chosen), names = [...new Set([...sheets, ...groups.map(g => g.sheet)])];
  const sheet = names.includes(chosenSheet) ? chosenSheet : groups.find(g => g.profile)?.sheet ?? names[0] ?? '';
  const visible = groups.filter(g => g.sheet === sheet), selected = visible.find(g => g.id === active && g.profile) ?? visible.find(g => g.profile);
  const basketCells=basket.reduce((n,item)=>n+item.cellCount,0);
  const sheetLabel = (name: string) => { const g = groups.filter(x => x.sheet === name), candidates = g.filter(x => x.profile).reduce((n,x)=>n+x.findings.length,0); return `${name} · ${candidates ? `수정 제안 후보 ${candidates}곳` : g.length ? '현재 수정 제안 미지원' : '발견된 수정 후보 없음'}`; };
  return <section id="repair-review" className={`repair-review proposal-picker shell ${basket.length?'has-proposal-basket':''}`} aria-labelledby="proposal-title"><h2 id="proposal-title">어떤 시트의 수정 제안을 볼까요?</h2>
    <p>셀 주소를 몰라도 됩니다. 발견된 위치를 묶어 제안하고, 선택한 규칙으로 실제 변경 예시를 확인합니다.</p>
    <p className="sr-only" aria-live="polite" aria-atomic="true">{notice}</p>
    {notice.includes('월별') && <p className="proposal-basket-warning" role="status">{notice}</p>}
    {selection.findings.length > 0 && <label className="delivery-check"><input type="checkbox" checked={selectedOnly} disabled={selection.locked} onChange={e => { setSelectedOnly(e.target.checked); setActive(''); }}/>1단계에서 고른 {selection.findings.length}개만 제안받기</label>}
    <label className="proposal-sheet">제안을 확인할 시트<select value={sheet} onChange={e => { setChosenSheet(e.target.value); setActive(''); }}>{names.map(name => <option key={name} value={name}>{sheetLabel(name)}</option>)}</select></label>
    <p>후보는 수정 가능 확정이 아닙니다. 선택 후 파일 전체의 보존 조건과 지원 범위를 검토합니다.</p>
    <div className="proposal-picker-layout">
      <div className="proposal-picker-main">
        {!visible.length && <p role="status">이 시트에서 발견된 수정 후보가 없습니다. 모든 계산이 맞거나 수정 가능한 시트라는 뜻은 아닙니다.</p>}
        <div className="proposal-options">{visible.map(g => <article key={g.id} className={g.id === selected?.id ? 'proposal-option is-selected' : 'proposal-option'}><h3>{g.column ? `${g.column}열 · ` : ''}{g.title}</h3><p>{g.findings.length}곳 · {g.profile ? (g.profile===RP03?'검증 필요 후보':'수정 예시를 검증할 후보') : '현재 자동 수정 미지원'}</p>{g.profile ? <button type="button" className="button button--outline" disabled={g.id === selected?.id || !file || !available} onClick={() => setActive(g.id)}>이 수정 제안 보기</button> : <p>{g.explanation}</p>}</article>)}</div>
        {selected && file && available ? <ProposalDetail key={selected.id+selected.findings.map(f=>f.cell).join(',')} proposal={selected} file={file} intent={intent} onPrepare={onPrepare} basketItem={basket.find(item=>item.id===basketId(selected))} onBasketChange={addToBasket} onBasketRemove={removeFromBasket}/> : !file || !available ? <p>직접 업로드한 원본 파일로 보호 베타에서 제안을 검증할 수 있습니다. 일반 구매는 준비 중입니다.</p> : <p>현재 지원하는 제안은 계산용 숫자 텍스트 정리와 실제 빈 칸 수식 복원, 단일 월별 수식 후보 검증입니다. 다른 유형은 예상값을 생성하지 않습니다.</p>}
      </div>
      {basket.length>0&&<aside className="proposal-basket-summary" role="region" aria-label="선택한 수정 목록" aria-live="polite"><div className="proposal-basket-card"><p className="proposal-basket-kicker">1 선택 → 2 검토 → 3 예시 확인</p><h3>선택한 {basketCells}곳</h3><p>{basket.length}개 묶음을 목록에 담았습니다. 다른 묶음을 더 추가하거나 변경 예시를 확인하세요.</p><details className="proposal-basket-list"><summary>담은 묶음 {basket.length}개 보기</summary><ul>{basket.map(item=><li key={item.id}><span><strong>{item.title}</strong><small>{item.draft.sheet} · {item.kindLabel} · {item.cellCount}곳</small></span><button type="button" className="text-link" aria-label={basketRemoveLabel(item)} onClick={()=>removeFromBasket(item.id)}>제외</button></li>)}</ul></details><div className="proposal-basket-actions"><button type="button" className="button button--primary" disabled={!file||!available} onClick={prepareBasket}>선택한 {basketCells}곳의 변경 예시 확인</button><button type="button" className="button button--ghost" onClick={clearBasket}>목록 비우기</button></div></div></aside>}
    </div>
  </section>;
}
