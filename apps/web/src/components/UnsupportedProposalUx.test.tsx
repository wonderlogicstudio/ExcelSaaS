import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { RepairProposalPicker } from './RepairProposalPicker';
import { demoResult } from '../data/demo';
import { noRepairIntent } from '../lib/repairProposals';
import type { Finding } from '../types';

const evidence = vi.hoisted(() => ({ readSourceCells: vi.fn(), readSourceSheets: vi.fn() }));
vi.mock('../lib/workbookEvidence', () => evidence);
const file = new File(['synthetic'], 'synthetic.xlsx');
const ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main';
const rel = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships';
const crcTable = Array.from({ length: 256 }, (_, value) => {
  for (let bit = 0; bit < 8; bit++) value = value & 1 ? (value >>> 1) ^ 0xedb88320 : value >>> 1;
  return value >>> 0;
});
const crc = (bytes: Buffer) => bytes.reduce((value, byte) => crcTable[(value ^ byte) & 255] ^ (value >>> 8), 0xffffffff) ^ 0xffffffff;
function mixedSourceFile() {
  const parts: [string, string][] = [
    ['xl/workbook.xml', `<workbook xmlns="${ns}" xmlns:r="${rel}"><sheets><sheet name="AR Aging" r:id="r1"/></sheets></workbook>`],
    ['xl/_rels/workbook.xml.rels', `<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="r1" Type="${rel}/worksheet" Target="worksheets/sheet1.xml"/></Relationships>`],
    ['xl/worksheets/sheet1.xml', `<worksheet xmlns="${ns}"><sheetData><row r="3"><c r="B3" t="inlineStr"><is><t>1,200</t></is></c></row></sheetData></worksheet>`],
  ];
  const locals: Buffer[] = [], centrals: Buffer[] = [];
  let offset = 0;
  for (const [name, text] of parts) {
    const nameBytes = Buffer.from(name), data = Buffer.from(text), local = Buffer.alloc(30), central = Buffer.alloc(46);
    local.writeUInt32LE(0x04034b50); central.writeUInt32LE(0x02014b50);
    for (const [header, position] of [[local, 14], [central, 16]] as const) {
      header.writeUInt32LE(crc(data) >>> 0, position); header.writeUInt32LE(data.length, position + 4); header.writeUInt32LE(data.length, position + 8);
    }
    local.writeUInt16LE(nameBytes.length, 26); central.writeUInt16LE(nameBytes.length, 28); central.writeUInt32LE(offset, 42);
    locals.push(local, nameBytes, data); centrals.push(central, nameBytes); offset += local.length + nameBytes.length + data.length;
  }
  const directory = Buffer.concat(centrals), end = Buffer.alloc(22);
  end.writeUInt32LE(0x06054b50); end.writeUInt16LE(parts.length, 8); end.writeUInt16LE(parts.length, 10);
  end.writeUInt32LE(directory.length, 12); end.writeUInt32LE(offset, 16);
  return new File([new Uint8Array(Buffer.concat([...locals, directory, end]))], 'synthetic.xlsx');
}
const selection = { findings: [] as Finding[], locked: false, toggle: vi.fn() };
const unsupported = (cell: string, refs: string[] = []): Finding => ({
  ...demoResult.findings[0], sheet: 'AR Aging', cell, rule_code: 'FORMULA_PATTERN_OUTLIER',
  title: '수식 패턴 차이', formula_pattern: {
    pattern_type: 'DOMINANT_NORMALIZED_PATTERN_OUTLIER', pattern_subtype: 'GENERIC_PATTERN_DRIFT',
    formula_region: 'H2:H8', dominant_pattern_id: 'synthetic-pattern', neighbor_count: refs.length, evidence_locations: refs,
    detection_basis: 'synthetic', current_limitations: [],
  },
});
const numeric = { ...demoResult.findings[0], sheet: 'AR Aging', cell: 'B3', rule_code: 'NUMBER_STORED_AS_TEXT', formula_pattern: null } as Finding;
const picker = (findings: Finding[], onPrepare = vi.fn(), sourceFile = file) => render(<RepairProposalPicker findings={findings} sheets={['AR Aging']} file={sourceFile} selection={selection} intent={noRepairIntent} available onPrepare={onPrepare} />);
afterEach(() => { cleanup(); vi.clearAllMocks(); });

describe('unsupported proposal evidence', () => {
  it('shows each original formula and real comparison formulas without a repair action', async () => {
    evidence.readSourceCells.mockResolvedValue([
      { cell: 'H3', type: 'formula', text: '=F3+G2' }, { cell: 'H4', type: 'formula', text: '=F4+G3' },
      { cell: 'H2', type: 'formula', text: '=F2+G2' }, { cell: 'H5', type: 'formula', text: '=F5+G5' },
    ]);
    const prepare = vi.fn(); picker([unsupported('H3', ['H2', 'H4']), unsupported('H4', ['H3', 'H5'])], prepare);
    await waitFor(() => expect(evidence.readSourceCells).toHaveBeenCalled());
    fireEvent.click(screen.getByText('AR Aging H3 · 원본 수식과 비교 위치'));
    fireEvent.click(screen.getByText('AR Aging H4 · 원본 수식과 비교 위치'));
    await waitFor(() => expect(screen.getAllByText('=F3+G2').length).toBeGreaterThan(0));
    expect(screen.getAllByText('=F4+G3').length).toBeGreaterThan(0);
    expect(screen.getByText('=F2+G2')).toBeInTheDocument();
    expect(screen.getByText('=F5+G5')).toBeInTheDocument();
    expect(screen.getByText(/어느 계산이 업무상 맞는지 확정할 수 없어/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /변경 예시 확인/ })).not.toBeInTheDocument();
    expect(prepare).not.toHaveBeenCalled();
    expect(evidence.readSourceCells).toHaveBeenCalledWith(file, 'AR Aging', ['H3', 'H2', 'H4', 'H5'], expect.any(AbortSignal));
  });

  it('keeps a mixed supported proposal selectable and passes only its selected addresses', async () => {
    evidence.readSourceCells.mockResolvedValue([{ cell: 'H3', type: 'formula', text: '=F3+G2' }, { cell: 'H2', type: 'formula', text: '=F2+G2' }]);
    const prepare = vi.fn(); picker([unsupported('H3', ['H2']), numeric], prepare, mixedSourceFile());
    await waitFor(() => expect(evidence.readSourceCells).toHaveBeenCalled());
    fireEvent.click(screen.getByText('AR Aging H3 · 원본 수식과 비교 위치'));
    await waitFor(() => expect(screen.getByText('=F3+G2')).toBeInTheDocument());
    await screen.findByText('문자 “1,200”');
    fireEvent.click(screen.getByRole('radio', { name: /^금액/ }));
    const confirm = screen.getByRole('checkbox', { name: /선택한 칸은 계산할/ });
    await waitFor(() => expect(confirm).toBeEnabled());
    fireEvent.click(confirm);
    fireEvent.click(screen.getByRole('button', { name: '이 묶음만 변경 예시 확인' }));
    expect(prepare).toHaveBeenCalledWith(expect.objectContaining({ sheet: 'AR Aging', targets: ['B3'], role: 'AMOUNT', proposal: true }));
    expect(JSON.stringify(prepare.mock.calls)).not.toContain('H3');
  });

  it('states missing source and comparison evidence without creating a formula or expected result', async () => {
    evidence.readSourceCells.mockResolvedValue([]);
    picker([unsupported('H3')]);
    fireEvent.click(screen.getByText('AR Aging H3 · 원본 수식과 비교 위치'));
    await waitFor(() => expect(screen.queryByText('원본 수식을 읽고 있습니다.')).not.toBeInTheDocument());
    expect(screen.getByText(/현재 수식: 원본 수식 확인 불가/)).toBeInTheDocument();
    expect(screen.getByText(/진단의 비교 위치: 기록된 비교 위치 없음/)).toBeInTheDocument();
    expect(screen.queryByText(/정답 수식:|예상 결과:/)).not.toBeInTheDocument();
  });

  it('does not label nonformula source cells as formula evidence', async () => {
    evidence.readSourceCells.mockResolvedValue([
      { cell: 'H3', type: 'text', text: '123' }, { cell: 'H2', type: 'text', text: '456' },
    ]);
    picker([unsupported('H3', ['H2'])]);
    fireEvent.click(screen.getByText('AR Aging H3 · 원본 수식과 비교 위치'));
    await waitFor(() => expect(screen.queryByText('원본 수식을 읽고 있습니다.')).not.toBeInTheDocument());
    expect(screen.getByText(/현재 수식: 원본 수식 확인 불가 \(현재 셀 유형: text\)/)).toBeInTheDocument();
    expect(screen.getByText(/H2 · 비교 수식 확인 불가/)).toBeInTheDocument();
    expect(screen.queryByText('123')).not.toBeInTheDocument();
    expect(screen.queryByText('456')).not.toBeInTheDocument();
  });
});
