import { cleanup, render, screen, waitFor } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import { OriginalFormulaComparison } from './OriginalFormulaComparison';
import { demoResult } from '../data/demo';
import type { Finding } from '../types';
import type { FormulaContext } from '../lib/workbookEvidence';
const {read}=vi.hoisted(()=>({read:vi.fn()}));
vi.mock('../lib/workbookEvidence',()=>({readFormulaContext:read}));
const finding={...demoResult.findings[0],sheet:'Synthetic',cell:'F22',formula_pattern:{evidence_summary:'현재 셀은 이전 행의 단가를 참조합니다.'}} as Finding;
afterEach(()=>{cleanup();read.mockReset();});
it('reads on demand, discards a previous File response, and renders only escaped text',async()=>{
 let old!:(v:FormulaContext)=>void;read.mockImplementationOnce(()=>new Promise<FormulaContext>(resolve=>old=resolve)).mockResolvedValueOnce({sheet:'Synthetic',target:{cell:'F22',type:'formula',text:'=<img onerror="unsafe">'},comparisons:[]});
 const file=new File(['old'],'old.xlsx'),next=new File(['new'],'new.xlsx');
 const view=render(<OriginalFormulaComparison file={file} finding={finding} active={false}/>);expect(read).not.toHaveBeenCalled();
 view.rerender(<OriginalFormulaComparison file={file} finding={finding} active/>);await waitFor(()=>expect(read).toHaveBeenCalledTimes(1));
 const signal=read.mock.calls[0][2] as AbortSignal;
 view.rerender(<OriginalFormulaComparison file={next} finding={finding} active/>);await waitFor(()=>expect(screen.getByText('=<img onerror="unsafe">')).toBeVisible());
 expect(signal.aborted).toBe(true);old({sheet:'Synthetic',target:{cell:'F22',type:'formula',text:'=OLD()'},comparisons:[]});
 await waitFor(()=>expect(screen.queryByText('=OLD()')).not.toBeInTheDocument());expect(document.querySelector('img')).toBeNull();
});
it('keeps the actual detection reason when source display is unavailable',async()=>{
 read.mockRejectedValue(new Error('synthetic unsupported'));render(<OriginalFormulaComparison file={new File(['x'],'synthetic.xlsx')} finding={finding} active/>);
 await waitFor(()=>expect(screen.getByRole('status')).toHaveTextContent('원본 수식을 표시하지 못했습니다'));
 expect(screen.getByText('현재 셀은 이전 행의 단가를 참조합니다.')).toBeVisible();expect(screen.queryByText('빈 셀')).not.toBeInTheDocument();
});
