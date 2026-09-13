// Read-only, on-demand source evidence. This is not a scanner or calculation engine.
// Previews stay local. A user-selected, confirmed anchor is passed through the existing private preflight policy.
import type { Finding } from '../types';

export type OriginalCell = { cell: string; type: 'formula' | 'text' | 'number' | 'blank' | 'boolean' | 'error' | 'unsupported'; text: string; cached?: string };
export type FormulaContext = { sheet: string; target: OriginalCell; comparisons: OriginalCell[] };
type Entry = { name: string; flags: number; method: number; crc: number; size: number; compressed: number; offset: number; data: number };
const MiB = 1024 * 1024;
const limits = { input: 10 * MiB, entries: 2048, total: 64 * MiB, xml: 8 * MiB, metadata: MiB, text: 2048 };
const mainNS = ['http://schemas.openxmlformats.org/spreadsheetml/2006/main', 'http://purl.oclc.org/ooxml/spreadsheetml/main'];
const relNS = 'http://schemas.openxmlformats.org/package/2006/relationships';
const relationshipNS = ['http://schemas.openxmlformats.org/officeDocument/2006/relationships', 'http://purl.oclc.org/ooxml/officeDocument/relationships'];
const decoder = () => new TextDecoder('utf-8', { fatal: true });
function requireSafe(ok: unknown): asserts ok { if (!ok) throw new Error('ORIGINAL_EVIDENCE_UNAVAILABLE'); }
function checkSignal(signal?: AbortSignal) { if (signal?.aborted) throw new DOMException('Aborted', 'AbortError'); }
function validCell(cell: string) {
  const m = /^([A-Z]{1,3})([1-9][0-9]{0,6})$/.exec(cell);
  return !!m && [...m[1]].reduce((n, c) => n * 26 + c.charCodeAt(0) - 64, 0) <= 16384 && Number(m[2]) <= 1048576;
}
function validPath(name: string) { return !!name && !/[\\:\x00-\x1f%]/.test(name) && !name.startsWith('/') && name.replace(/\/$/, '').split('/').every(p => p && p !== '.' && p !== '..'); }
function crc32(bytes: Uint8Array) {
  let crc = 0xffffffff;
  for (const byte of bytes) { crc ^= byte; for (let i = 0; i < 8; i++) crc = (crc >>> 1) ^ (crc & 1 ? 0xedb88320 : 0); }
  return (crc ^ 0xffffffff) >>> 0;
}
async function fileBytes(file: File): Promise<Uint8Array> {
  requireSafe(file.size > 0 && file.size <= limits.input);
  const buffer = typeof file.arrayBuffer === 'function' ? await file.arrayBuffer() : await new Promise<ArrayBuffer>((resolve, reject) => {
    const reader = new FileReader(); reader.onload = () => resolve(reader.result as ArrayBuffer); reader.onerror = () => reject(new Error('ORIGINAL_EVIDENCE_UNAVAILABLE')); reader.readAsArrayBuffer(file);
  });
  requireSafe(buffer.byteLength === file.size); return new Uint8Array(buffer);
}
function directory(bytes: Uint8Array): Map<string, Entry> {
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const u16 = (at: number) => view.getUint16(at, true), u32 = (at: number) => view.getUint32(at, true);
  let end = bytes.length - 22;
  for (; end >= Math.max(0, bytes.length - 65557); end--) if (u32(end) === 0x06054b50 && end + 22 + u16(end + 20) === bytes.length) break;
  requireSafe(end >= Math.max(0, bytes.length - 65557) && u32(end) === 0x06054b50 && u16(end + 4) === 0 && u16(end + 6) === 0);
  const count = u16(end + 10), start = u32(end + 16), length = u32(end + 12);
  requireSafe(count > 0 && count <= limits.entries && count === u16(end + 8) && start + length === end);
  const entries = new Map<string, Entry>(); let at = start, total = 0;
  for (let i = 0; i < count; i++) {
    requireSafe(at + 46 <= end && u32(at) === 0x02014b50);
    const nameLength = u16(at + 28), extra = u16(at + 30), comment = u16(at + 32);
    requireSafe(at + 46 + nameLength + extra + comment <= end && u16(at + 34) === 0);
    const name = decoder().decode(bytes.subarray(at + 46, at + 46 + nameLength));
    const entry: Entry = { name, flags: u16(at + 8), method: u16(at + 10), crc: u32(at + 16), compressed: u32(at + 20), size: u32(at + 24), offset: u32(at + 42), data: 0 };
    requireSafe(validPath(name) && !entries.has(name) && !(entry.flags & ~0x808) && [0, 8].includes(entry.method));
    total += entry.size; requireSafe(total <= limits.total && entry.offset + 30 <= start && entry.compressed <= bytes.length);
    const local = entry.offset;
    requireSafe(u32(local) === 0x04034b50 && u16(local + 6) === entry.flags && u16(local + 8) === entry.method && u16(local + 26) === nameLength);
    entry.data = local + 30 + nameLength + u16(local + 28);
    requireSafe(entry.data + entry.compressed <= start && decoder().decode(bytes.subarray(local + 30, local + 30 + nameLength)) === name);
    if (!(entry.flags & 8)) requireSafe(u32(local + 14) === entry.crc && u32(local + 18) === entry.compressed && u32(local + 22) === entry.size);
    entries.set(name, entry); at += 46 + nameLength + extra + comment;
  }
  requireSafe(at === end);
  const ranges = [...entries.values()].sort((a, b) => a.offset - b.offset);
  for (let i = 1; i < ranges.length; i++) requireSafe(ranges[i - 1].data + ranges[i - 1].compressed <= ranges[i].offset);
  return entries;
}
async function inflate(bytes: Uint8Array, entry: Entry, max: number, signal?: AbortSignal) {
  checkSignal(signal); requireSafe(entry.size <= max);
  const input = bytes.subarray(entry.data, entry.data + entry.compressed);
  if (entry.method === 0) { requireSafe(input.length === entry.size && crc32(input) === entry.crc); return input; }
  // Enforce the declared size on each output chunk, not after an unbounded inflate.
  const stream = new ReadableStream<BufferSource>({ start(controller) { controller.enqueue(new Uint8Array(input)); controller.close(); } });
  const reader = stream.pipeThrough(new DecompressionStream('deflate-raw')).getReader();
  let expired = false, size = 0; const chunks: Uint8Array[] = [];
  const cancel = () => { void reader.cancel().catch(() => undefined); };
  const timer = setTimeout(() => { expired = true; cancel(); }, 3000); signal?.addEventListener('abort', cancel, { once: true });
  try {
    for (;;) {
      const chunk = await reader.read(); checkSignal(signal); requireSafe(!expired);
      if (chunk.done) break;
      size += chunk.value.length; requireSafe(size <= entry.size && size <= max); chunks.push(chunk.value);
    }
    requireSafe(size === entry.size); const output = new Uint8Array(size); let offset = 0;
    for (const chunk of chunks) { output.set(chunk, offset); offset += chunk.length; }
    requireSafe(crc32(output) === entry.crc); return output;
  } finally { clearTimeout(timer); signal?.removeEventListener('abort', cancel); cancel(); }
}
function xml(bytes: Uint8Array, root: string, namespaces: string[]) {
  const text = decoder().decode(bytes);
  requireSafe(!/<!DOCTYPE|<!ENTITY/i.test(text));
  const document = new DOMParser().parseFromString(text, 'application/xml');
  requireSafe(!document.getElementsByTagName('parsererror').length && document.documentElement.localName === root && namespaces.includes(document.documentElement.namespaceURI ?? ''));
  return document.documentElement;
}
function children(element: Element, name: string) { return Array.from(element.children).filter(c => c.localName === name && c.namespaceURI === element.namespaceURI); }
function only(element: Element, name: string) { const result = children(element, name); requireSafe(result.length <= 1); return result[0]; }
function bounded(text: string | null | undefined) { const value = text ?? ''; requireSafe(value.length <= limits.text); return value; }

export async function readSourceCells(file: File, sheetName: string, requested: string[], signal?: AbortSignal): Promise<OriginalCell[]> {
  checkSignal(signal); requireSafe(sheetName && requested.length > 0 && requested.length <= 64 && requested.every(validCell));
  const wanted = [...new Set(requested)]; const bytes = await fileBytes(file); checkSignal(signal); const entries = directory(bytes);
  const part = async (name: string, max = limits.xml) => { const entry = entries.get(name); requireSafe(entry); return inflate(bytes, entry, max, signal); };
  const workbook = xml(await part('xl/workbook.xml', limits.metadata), 'workbook', mainNS);
  const sheets = only(workbook, 'sheets'); requireSafe(sheets);
  const matches = children(sheets, 'sheet').filter(s => s.getAttribute('name') === sheetName); requireSafe(matches.length === 1);
  const rid = relationshipNS.map(ns => matches[0].getAttributeNS(ns, 'id')).find(Boolean); requireSafe(rid);
  const relations = xml(await part('xl/_rels/workbook.xml.rels', limits.metadata), 'Relationships', [relNS]);
  const links = children(relations, 'Relationship').filter(r => r.getAttribute('Id') === rid); requireSafe(links.length === 1);
  const link = links[0]; requireSafe(!link.getAttribute('TargetMode') || link.getAttribute('TargetMode') === 'Internal');
  requireSafe(relationshipNS.some(ns => link.getAttribute('Type') === ns + '/worksheet'));
  const destination = link.getAttribute('Target') ?? ''; const name = destination.startsWith('/xl/') ? destination.slice(1) : 'xl/' + destination;
  requireSafe(validPath(name) && name.startsWith('xl/worksheets/') && name.endsWith('.xml'));
  const worksheet = xml(await part(name), 'worksheet', mainNS); checkSignal(signal);
  const data = only(worksheet, 'sheetData'); requireSafe(data);
  const cells = new Map<string, Element>(); const seen = new Set<string>(); let count = 0;
  for (const row of children(data, 'row')) for (const cell of children(row, 'c')) {
    const coordinate = cell.getAttribute('r') ?? ''; requireSafe(validCell(coordinate) && !seen.has(coordinate) && ++count <= 100000); seen.add(coordinate);
    if (wanted.includes(coordinate)) cells.set(coordinate, cell);
  }
  const sharedIndexes = [...cells.values()].filter(c => c.getAttribute('t') === 's' && !only(c, 'f')).map(c => { const value = only(c, 'v')?.textContent ?? ''; requireSafe(/^\d+$/.test(value)); return Number(value); });
  const shared = new Map<number, string>();
  if (sharedIndexes.length) {
    requireSafe(sharedIndexes.every(n => Number.isSafeInteger(n) && n >= 0 && n < 100000));
    const strings = children(xml(await part('xl/sharedStrings.xml'), 'sst', mainNS), 'si'); requireSafe(strings.length <= 100000);
    for (const index of sharedIndexes) { requireSafe(strings[index]); shared.set(index, bounded(Array.from(strings[index].getElementsByTagNameNS(strings[index].namespaceURI, 't')).map(t => t.textContent).join(''))); }
  }
  const read = (coordinate: string): OriginalCell => {
    const cell = cells.get(coordinate); if (!cell) return { cell: coordinate, type: 'blank', text: '빈 셀' };
    const formula = only(cell, 'f'), value = only(cell, 'v'); const type = cell.getAttribute('t');
    if (formula) {
      if ((formula.getAttribute('t') && formula.getAttribute('t') !== 'normal') || formula.hasAttribute('ref') || formula.hasAttribute('si')) return { cell: coordinate, type: 'unsupported', text: '공유·배열 수식의 원문 표시는 지원하지 않습니다.' };
      const text = bounded(formula.textContent); requireSafe(text.length > 0);
      return { cell: coordinate, type: 'formula', text: '=' + text, ...(value?.textContent ? { cached: bounded(value.textContent) } : {}) };
    }
    if (type === 'inlineStr') { const inline = only(cell, 'is'); requireSafe(inline); return { cell: coordinate, type: 'text', text: bounded(Array.from(inline.getElementsByTagNameNS(inline.namespaceURI, 't')).map(t => t.textContent).join('')) }; }
    if (type === 's') { const text = shared.get(Number(value?.textContent)); requireSafe(text !== undefined); return { cell: coordinate, type: 'text', text }; }
    if (!value) return { cell: coordinate, type: 'blank', text: '빈 셀' };
    requireSafe(!type || ['n', 'b', 'e', 'str'].includes(type));
    return { cell: coordinate, type: type === 'b' ? 'boolean' : type === 'e' ? 'error' : type === 'str' ? 'text' : 'number', text: bounded(value.textContent) };
  };
  checkSignal(signal); return wanted.map(read);
}

export async function readFormulaContext(file: File, finding: Finding, signal?: AbortSignal): Promise<FormulaContext> {
  checkSignal(signal);
  requireSafe(finding.sheet && finding.cell && validCell(finding.cell) && finding.formula_pattern);
  const targetRow = Number(finding.cell.replace(/^[A-Z]+/, ''));
  const refs = [...new Set(finding.formula_pattern.comparison_locations?.length ? finding.formula_pattern.comparison_locations : finding.formula_pattern.evidence_locations)]
    .filter(c => validCell(c) && c !== finding.cell).slice(0, 4)
    .sort((a, b) => Math.abs(Number(a.replace(/^[A-Z]+/, '')) - targetRow) - Math.abs(Number(b.replace(/^[A-Z]+/, '')) - targetRow)).slice(0, 2);
  const cells = await readSourceCells(file, finding.sheet, [finding.cell, ...refs], signal);
  return { sheet: finding.sheet, target: cells[0], comparisons: cells.slice(1) };
}

export async function readSourceSheets(file: File, signal?: AbortSignal): Promise<string[]> {
  checkSignal(signal); const bytes = await fileBytes(file); const entries = directory(bytes), entry = entries.get('xl/workbook.xml'); requireSafe(entry);
  const root = xml(await inflate(bytes, entry, limits.metadata, signal), 'workbook', mainNS), sheets = only(root, 'sheets'); requireSafe(sheets);
  const names = children(sheets, 'sheet').map(s => bounded(s.getAttribute('name')));
  requireSafe(names.length > 0 && names.length <= 128 && names.every(n => n.length > 0) && new Set(names).size === names.length);
  checkSignal(signal); return names;
}
