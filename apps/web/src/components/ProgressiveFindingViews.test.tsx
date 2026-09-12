import { render, fireEvent, within, cleanup } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { demoResult } from '../data/demo';
import { ProgressiveFindingViews } from './ProgressiveFindingViews';

const first = {...demoResult.findings[0],id:'one',finding_key:'one',sheet:'합성',cell:'A1',description:'이 셀은 깊이 7',
  guidance:{...demoResult.findings[0].guidance!,detected_fact:'중첩 조건이 깊습니다',possible_impact:'공통 유지보수 영향'}};
const second = {...first,id:'two',finding_key:'two',cell:'A2',description:'이 셀은 깊이 8'};
const props = { findings:[first,second],allFindings:[first,second],mode:'groups' as const,statuses:{},categoryLabel:()=> '구조 위험',onStatusChange:vi.fn(),onReviewGroup:vi.fn() };
describe('progressive finding evidence',()=>{
 afterEach(cleanup);
 it('starts at type summaries and shows common guidance once with each cell difference retained',()=>{
  const {container,getByText,getAllByText}=render(<ProgressiveFindingViews {...props}/>);
  const group=container.querySelector('.diagnosis-type__disclosure')!;
  expect(group).not.toHaveAttribute('open');
  expect(container.querySelectorAll('.diagnosis-cell[open]')).toHaveLength(0);
  fireEvent.click(group.querySelector('summary')!);
  expect(group).toHaveAttribute('open');
  expect(getAllByText('공통 유지보수 영향')).toHaveLength(1);
  const cell=container.querySelector('.diagnosis-cell')!;
  expect(within(cell as HTMLElement).queryByText('공통 유지보수 영향')).toBeNull();
  expect(within(cell as HTMLElement).getByText('이 셀은 깊이 7')).toBeInTheDocument();
  expect(getByText('이 셀은 깊이 8')).toBeInTheDocument();
  expect(container.querySelectorAll('h4')).toHaveLength(1);
 });
 it('does not promote one filtered cell\'s distinct evidence to common explanation',()=>{
  const variant={...second,guidance:{...second.guidance,possible_impact:'다른 셀의 영향'}};
  const {container}=render(<ProgressiveFindingViews {...props} findings={[first]} allFindings={[first,variant]}/>);
  const cell=container.querySelector('.diagnosis-cell')!;
  expect(within(cell as HTMLElement).getByText('공통 유지보수 영향')).toBeInTheDocument();
  expect(container.querySelector('.diagnosis-type__count')).toHaveTextContent('1건 / 전체 2건');
 });
});
