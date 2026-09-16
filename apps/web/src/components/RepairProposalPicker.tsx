import { useEffect, useState } from 'react';
import type { Finding } from '../types';
import type { OriginalCell } from '../lib/workbookEvidence';
import type { RepairDraft, ReviewSelection } from '../lib/repairReview';
import { proposalGroups, RP01, RP02, type RepairIntent, type RepairProposal } from '../lib/repairProposals';
const COMBINED='COMBINED_RP01_RP02_REPAIR_V1';

function ProposalDetail({ proposal, file, intent, onPrepare, onAdd, listActive }: { proposal: RepairProposal; file: File; intent: RepairIntent; onPrepare: (draft: RepairDraft) => void; onAdd: (draft: RepairDraft) => void; listActive: boolean }) {
  const [targets, setTargets] = useState(proposal.findings.slice(0, 50).map(f => f.cell!).filter(Boolean));
  const [role, setRole] = useState(''), [confirmed, setConfirmed] = useState(false), [anchor, setAnchor] = useState('');
  const [cells, setCells] = useState<OriginalCell[]>([]), [loading, setLoading] = useState(true), [error, setError] = useState(false);
  const first = proposal.findings.find(f => f.cell === targets[0]) ?? proposal.findings[0];
  const requestedAnchor = intent.enabled && intent.kind === 'same_formula' && intent.sheet === proposal.sheet ? intent.anchor : '';
  const refs = [...new Set([requestedAnchor, ...(first.formula_pattern?.comparison_locations ?? []), ...(first.formula_pattern?.evidence_locations ?? [])])]
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
  const anchorChoices = cells.filter(c => refs.includes(c.cell) && c.type === 'formula' && c.cell !== first.cell);
  const columnText = cells.filter(c => topCells.includes(c.cell) && c.type === 'text' && c.text.trim() && !/^[\d\s,.-]+$/.test(c.text)).at(-1);
  const canPrepare = targets.length > 0 && confirmed && !loading && !error && (proposal.profile === RP01 ? ['AMOUNT', 'QUANTITY'].includes(role) : !!formula);
  return <section className="proposal-details" aria-label={`${proposal.sheet} ${proposal.column}열 제안`}>
    <h3>{proposal.title}</h3><p>{proposal.explanation}</p>
    <p><strong>{proposal.sheet} · {proposal.column}열 · 제안 위치 {proposal.findings.length}곳</strong></p>
    {columnText && <p className="proposal-column-name">{proposal.column}열 위쪽의 설명: <strong>{columnText.text}</strong></p>}
    {loading ? <p role="status">이 위치의 실제 원본을 확인하고 있습니다…</p> : error ? <p role="status">원본 예시를 읽지 못했습니다. 무료 진단 근거는 유지됩니다. 파일 또는 브라우저를 확인한 뒤 다시 검사하세요.</p> : source && <div className="proposal-source"><span>원본 예시 · {proposal.sheet} {source.cell}</span><strong>{source.type === 'text' ? `문자 “${source.text}”` : source.type === 'blank' ? '비어 있는 칸' : source.text}</strong><small>아직 수정안의 계산 결과가 아닙니다.</small></div>}
    <details className="proposal-targets"><summary>제안된 위치 선택·제외 ({targets.length}곳 선택)</summary>
      <p>선택한 위치만 검사합니다. 시트 전체나 사이의 셀을 자동으로 포함하지 않습니다.</p>
      <div className="proposal-cell-list">{proposal.findings.slice(0, 50).map(f => <label key={f.cell}><input type="checkbox" checked={targets.includes(f.cell!)} onChange={e => { setConfirmed(false); setTargets(t => e.target.checked ? [...t, f.cell!].sort((a,b)=>a.localeCompare(b,'en',{numeric:true})) : t.filter(c => c !== f.cell)); }}/>{f.cell}</label>)}</div>
      {proposal.findings.length > 50 && <p>한 번에 표시한50곳까지 제안합니다. 나머지 위치는 다음 검사에서 선택하세요. 수정 엔진의 최종 한도는 별도 검사합니다.</p>}
    </details>
    {proposal.profile === RP01 ? <fieldset className="proposal-purpose"><legend>이 숫자는 어떤 용도인가요?</legend>
      <p>계산에 쓸 숫자만 바꿉니다. 고객번호처럼 구분하는 번호는 문자로 남겨야 합니다.</p>
      {[['AMOUNT', '금액', '매출·비용·정산액처럼 더하거나 뺄 돈'], ['QUANTITY', '개수·수량', '상품 수·인원처럼 계산할 개수'], ['ID', '구분하는 번호', '고객번호·계좌·전화번호·우편번호']].map(([value,label,help]) => <label key={value}><input type="radio" name={`purpose-${proposal.id}`} value={value} checked={role === value} onChange={() => { setRole(value); setConfirmed(false); }}/><span><strong>{label}</strong><small>{help}</small></span></label>)}
      {role === 'ID' && <p role="status">구분하는 번호는 수정하지 않습니다. 앞자리0이나 원래 표기를 보존하세요.</p>}
    </fieldset> : <div className="proposal-anchor"><label>어느 칸과 같은 방식으로 계산할까요?<select value={anchor} onChange={e => { setAnchor(e.target.value); setConfirmed(false); }}><option value="">기준을 선택하세요</option>{anchorChoices.map(c => <option key={c.cell} value={c.cell}>{c.cell} · 원본의 계산 칸{c.cached ? ` (저장값 ${c.cached})` : ''}</option>)}</select></label>
      <p>주변 수식은 기준 후보입니다. 같은 계산을 해야 하는 행인지 확인하세요. 저장값을 그대로 복사하지 않고 대상 행에 맞게 참조를 옮깁니다.</p>
      {formula && <details><summary>선택한 기준의 원본 수식 확인</summary><code>{formula.text}</code><p>저장된 결과는 재계산한 값이 아닙니다.</p></details>}
      {!loading && !formula && <p>유효한 기준 수식이 없어 아직 수정안을 제안할 수 없습니다. 요청한 셀에 실제 수식이 있는지 확인하세요.</p>}
    </div>}
    <label className="delivery-check"><input type="checkbox" checked={confirmed} disabled={loading || error || !targets.length || (proposal.profile === RP01 ? !['AMOUNT','QUANTITY'].includes(role) : !formula)} onChange={e => setConfirmed(e.target.checked)}/>{proposal.profile === RP01 ? '선택한 칸은 계산할 금액·개수입니다. 문자 숫자를 계산에 포함하는 제안을 확인하겠습니다.' : '선택한 빈 칸도 이 기준 칸과 같은 업무 계산을 해야 합니다.'}</label>
    <button className="button button--outline" type="button" disabled={!canPrepare} onClick={() => onAdd({ profile: proposal.profile!, sheet: proposal.sheet, targets, role, anchor, anchor_formula: formula?.text ?? '', confirmed: true, proposal: true })}>수정 목록에 이 묶음 추가</button>
    <button className={listActive ? 'button button--outline' : 'button button--primary'} type="button" disabled={!canPrepare} onClick={() => onPrepare({ profile: proposal.profile!, sheet: proposal.sheet, targets, role, anchor, anchor_formula: formula?.text ?? '', confirmed: true, proposal: true })}>{listActive ? '이 묶음만 따로 수정 예시 확인' : '이 제안으로 수정 예시 확인'}</button>
    <p className="proposal-footnote">제안 선택은 변경 승인이 아닙니다. 파일 보존·수정 범위·계산이 검증된 경우에만 실제 변경 예시를 보여드립니다.</p>
  </section>;
}
export function RepairProposalPicker({ findings, sheets, file, selection, intent, available, onPrepare }: { findings: Finding[]; sheets: string[]; file: File | null; selection: ReviewSelection; intent: RepairIntent; available: boolean; onPrepare: (draft: RepairDraft) => void }) {
  const [selectedOnly, setSelectedOnly] = useState(selection.findings.length > 0), [chosenSheet, setChosenSheet] = useState(''), [active, setActive] = useState('');
  const [basket,setBasket]=useState<RepairDraft[]>([]);
  const selectionKey = selection.findings.map(f => JSON.stringify([f.rule_code,f.sheet,f.cell])).join('|');
  useEffect(() => { setSelectedOnly(selection.findings.length > 0); setActive(''); }, [selectionKey]);
  const addToBasket=(draft:RepairDraft)=>setBasket(old=>{const key=JSON.stringify([draft.profile,draft.sheet,draft.targets,draft.role,draft.anchor]);return [...old.filter(item=>JSON.stringify([item.profile,item.sheet,item.targets,item.role,item.anchor])!==key),draft];});
  const prepareBasket=()=>{if(!basket.length)return;onPrepare(basket.length===1?basket[0]:{profile:COMBINED,sheet:basket[0].sheet,targets:basket.flatMap(item=>item.targets),confirmed:true,proposal:true,items:basket});};
  const chosen = selectedOnly && selection.findings.length ? selection.findings : findings;
  const groups = proposalGroups(chosen), names = [...new Set([...sheets, ...groups.map(g => g.sheet)])];
  const sheet = names.includes(chosenSheet) ? chosenSheet : groups.find(g => g.profile)?.sheet ?? names[0] ?? '';
  const visible = groups.filter(g => g.sheet === sheet), selected = visible.find(g => g.id === active && g.profile) ?? visible.find(g => g.profile);
  const sheetLabel = (name: string) => { const g = groups.filter(x => x.sheet === name), candidates = g.filter(x => x.profile).reduce((n,x)=>n+x.findings.length,0); return `${name} · ${candidates ? `수정 제안 후보 ${candidates}곳` : g.length ? '현재 수정 제안 미지원' : '발견된 수정 후보 없음'}`; };
  return <section id="repair-review" className="repair-review proposal-picker shell" aria-labelledby="proposal-title"><h2 id="proposal-title">어떤 시트의 수정 제안을 볼까요?</h2>
    <p>셀 주소를 몰라도 됩니다. 발견된 위치를 묶어 제안하고, 선택한 규칙으로 실제 변경 예시를 확인합니다.</p>
    {selection.findings.length > 0 && <label className="delivery-check"><input type="checkbox" checked={selectedOnly} disabled={selection.locked} onChange={e => { setSelectedOnly(e.target.checked); setActive(''); }}/>1단계에서 고른 {selection.findings.length}개만 제안받기</label>}
    <label className="proposal-sheet">제안을 확인할 시트<select value={sheet} onChange={e => { setChosenSheet(e.target.value); setActive(''); }}>{names.map(name => <option key={name} value={name}>{sheetLabel(name)}</option>)}</select></label>
    <p>‘후보’는 수정 가능 확정이 아닙니다. 선택 후 파일 전체의 보존 조건과 지원 범위를 검사합니다.</p>
    {!visible.length && <p role="status">이 시트에서 발견된 수정 후보가 없습니다. 모든 계산이 맞거나 수정 가능한 시트라는 뜻은 아닙니다.</p>}
    {basket.length>0&&<details className="proposal-basket" open><summary>수정 목록 {basket.length}개 묶음</summary><ul>{basket.map(item=><li key={JSON.stringify([item.profile,item.sheet,item.targets,item.anchor])}><span>{item.sheet} · {item.profile===RP01?'숫자 텍스트':'빈 셀'} {item.targets.length}곳</span><button type="button" className="text-link" onClick={()=>setBasket(old=>old.filter(x=>x!==item))}>제외</button></li>)}</ul><button type="button" className="button button--primary" disabled={!file||!available} onClick={prepareBasket}>수정 목록의 전체 변경 예시 확인</button></details>}
    <div className="proposal-options">{visible.map(g => <article key={g.id} className={g.id === selected?.id ? 'proposal-option is-selected' : 'proposal-option'}><h3>{g.column ? `${g.column}열 · ` : ''}{g.title}</h3><p>{g.findings.length}곳 · {g.profile ? '수정 예시를 검증할 후보' : '현재 자동 수정 미지원'}</p>{g.profile ? <button type="button" className="button button--outline" disabled={g.id === selected?.id || !file || !available} onClick={() => setActive(g.id)}>이 수정 제안 보기</button> : <p>{g.explanation}</p>}</article>)}</div>
    {selected && file && available ? <ProposalDetail key={selected.id+selected.findings.map(f=>f.cell).join(',')} proposal={selected} file={file} intent={intent} onPrepare={onPrepare} onAdd={addToBasket} listActive={basket.length>0}/> : !file || !available ? <p>직접 업로드한 등록 합성 파일로 보호 베타에서 제안을 검증할 수 있습니다. 일반 구매는 준비 중입니다.</p> : <p>현재 지원하는 제안은 계산용 숫자 텍스트 정리와 실제 빈 셀의 수식 복원입니다. 다른 유형의 예상값은 생성하지 않습니다.</p>}
  </section>;
}
