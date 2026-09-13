import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ProductCards } from './ProductCards';
import { productCatalog, diagnosisCsvArtifact } from '../lib/products';
import { downloadDiagnosisCsv } from '../lib/diagnosisCsv';
import { demoResult } from '../data/demo';

describe('D01 product and output boundaries', () => {
  afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals(); });

  it('uses the API-generated output names and permits only the existing free diagnosis action', () => {
    const start = vi.fn();
    render(<ProductCards products={demoResult.products} onStart={start} />);
    for (const product of productCatalog) {
      const card = screen.getByRole('article', { name: product.title });
      for (const artifact of product.deliverables) {
        expect(within(card).getByText(artifact.label)).toBeVisible();
        expect(within(card).getByText(artifact.filename)).toBeVisible();
      }
      if (product.product_id !== 'FREE_DIAGNOSIS') {
        const button = within(card).getByRole('button');
        expect(button).toBeDisabled();
        fireEvent.click(button);
      }
    }
    expect(start).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: '무료 진단 시작' }));
    expect(start).toHaveBeenCalledOnce();
    expect(screen.getByText('비교 보고서 전용 · 수정본 미포함')).toBeVisible();
    expect(screen.getByText(/비교 자료 B는 정답이 아닙니다/)).toBeVisible();
    expect(screen.getByText('결제 ≠ 변경승인 · 확인함 ≠ 변경승인')).toBeVisible();
  });

  it('labels protected synthetic trials without offering general purchase',()=>{
    const start=vi.fn();const compare=vi.fn();
    render(<ProductCards onStart={start} onCompare={compare}/>);
    expect(screen.getAllByText('합성 샘플 시험')).toHaveLength(2);
    fireEvent.click(screen.getByRole('button',{name:'합성 파일 검사 후 수정 범위 확인'}));
    expect(start).toHaveBeenCalledOnce();
    fireEvent.click(screen.getByRole('button',{name:'비교 범위 사전 확인'}));
    expect(compare).toHaveBeenCalledOnce();
    expect(screen.queryByRole('button',{name:/구매|결제/})).not.toBeInTheDocument();
  });

  it('fails closed even when a remote catalog marks absent repair and comparison engines purchasable', () => {
    render(<ProductCards products={productCatalog.map((item) => ({ ...item, capability_status: 'AVAILABLE', purchase_enabled: true }))} onStart={() => undefined} />);
    expect(screen.getByRole('button', { name: '수정 범위 확인 · 준비 중' })).toBeDisabled();
    expect(screen.getByRole('button', { name: '두 자료 비교 시작 · 준비 중' })).toBeDisabled();
  });

  it('uses the same real CSV download filename as the catalog and keeps unsupported distinct', () => {
    const create = vi.fn(() => 'blob:synthetic-csv');
    const revoke = vi.fn();
    vi.stubGlobal('URL', { createObjectURL: create, revokeObjectURL: revoke });
    let downloadedName = '';
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (this: HTMLAnchorElement) { downloadedName = this.download; });
    downloadDiagnosisCsv(demoResult, {});
    expect(downloadedName).toBe(diagnosisCsvArtifact.filename);
    expect(create.mock.calls).toHaveLength(1);
    expect(revoke).toHaveBeenCalledWith('blob:synthetic-csv');
    render(<ProductCards products={productCatalog.map((item) => ({ ...item, capability_status: 'UNSUPPORTED' }))} onStart={() => undefined} />);
    expect(screen.getByRole('button', { name: '수정 범위 확인 · 지원 불가' })).toBeDisabled();
    expect(screen.getByRole('button', { name: '무료 진단 시작' })).toBeDisabled();
  });
});
