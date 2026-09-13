import { useEffect, useState } from 'react';
import type { Finding } from '../types';
import type { RepairIntent } from '../lib/repairProposals';
export function useSourceSheets(file?: File | null) {
  const [sheets, setSheets] = useState<string[]>([]), [unavailable, setUnavailable] = useState(false);
  useEffect(() => { setSheets([]); setUnavailable(false); if (!file) return; const c = new AbortController();
    import('../lib/workbookEvidence').then(m => m.readSourceSheets(file, c.signal)).then(v => { if (!c.signal.aborted) setSheets(v); }).catch(() => { if (!c.signal.aborted) setUnavailable(true); });
    return () => c.abort();
  }, [file]);
  return { sheets, unavailable };
}
export function RepairIntentEditor({ value, onChange, findings, sheets, locked }: { value: RepairIntent; onChange: (next: RepairIntent) => void; findings: Finding[]; sheets: string[]; locked: boolean }) {
  const options = [...new Set([...sheets, ...findings.flatMap(f => f.sheet ? [f.sheet] : [])])];
  const cells = [...new Set(findings.filter(f => f.sheet === value.sheet && f.cell).map(f => f.cell!))];
  const set = (change: Partial<RepairIntent>) => onChange({ ...value, ...change });
  return <section className="repair-intent" aria-label="원하는 결과 알려주기"><h3>원하는 결과가 있나요? <small>선택사항</small></h3>
    <label className="delivery-check"><input type="checkbox" checked={!value.enabled} disabled={locked} onChange={e => set({ enabled: !e.target.checked, sheet: value.sheet || options[0] || '' })}/>별도 의견 없이 규칙으로 확인할게요</label>
    {value.enabled && <fieldset disabled={locked}><legend>확인하고 싶은 결과</legend><p>무료 탐지 결과는 유지합니다. 아래 요청은 수정안을 계산한 뒤 일치 여부를 확인하는 조건입니다. 현재 브라우저에만 보관하고 AI나 피드백 저장소로 보내지 않습니다.</p>
      <div className="delivery-form-grid"><label>어떤 결과를 원하나요?<select value={value.kind} onChange={e => set({ kind: e.target.value as RepairIntent['kind'] })}><option value="number">이 칸의 숫자가 이렇게 나왔으면 해요</option><option value="same_formula">이 칸도 다른 칸과 같은 방식으로 계산하고 싶어요</option></select></label>
        <label>요청할 시트<select value={value.sheet} onChange={e => set({ sheet: e.target.value, cell: '', anchor: '' })}><option value="">시트를 선택하세요</option>{options.map(s => <option key={s}>{s}</option>)}</select></label>
        <label>확인할 위치<select value={cells.includes(value.cell) ? value.cell : ''} onChange={e => set({ cell: e.target.value })}><option value="">아래에서 직접 지정 또는 발견 위치 선택</option>{cells.map(c => <option key={c}>{c}</option>)}</select></label>
        <label>요청할 셀 주소<input value={value.cell} maxLength={10} placeholder="예: B2 또는 합계 J130" onChange={e => set({ cell: e.target.value.toUpperCase().trim() })}/><small>발견 목록에서 고르면 자동으로 채워집니다. 원하는 합계 위치를 이미 알면 직접 지정할 수 있습니다.</small></label>
        {value.kind === 'number' ? <label>원하는 숫자<input inputMode="decimal" maxLength={80} value={value.expected} placeholder="예: 12" onChange={e => set({ expected: e.target.value })}/></label>
          : <label>같은 계산 방식을 사용할 셀<input maxLength={10} value={value.anchor} placeholder="예: A1" onChange={e => set({ anchor: e.target.value.toUpperCase().trim() })}/><small>그 셀의 숫자를 복사하지 않습니다. 실제 빈 셀에 수식을 적용하는 지원 범위에서 검토합니다.</small></label>}
      </div><p>현재 SUM 범위 변경·기존 값 덮어쓰기는 제안하지 않습니다. 지원하지 않거나 계산값이 요청과 다르면 승인 전에 알려드립니다.</p>
    </fieldset>}
    {locked && <p>현재 제안에 연결된 요청입니다. 바꾸려면2단계에서 ‘다른 제안으로 다시 선택’을 누르세요.</p>}
  </section>;
}
