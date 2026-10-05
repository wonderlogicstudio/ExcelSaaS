from pathlib import Path
p=Path('apps/web/src/components/ProposalFlow.test.tsx')
s=p.read_text(encoding='utf-8')
s=s.replace("import { noRepairIntent, RP01, RP02 } from '../lib/repairProposals';", "import { noRepairIntent, RP01, RP02, RP03 } from '../lib/repairProposals';")
insert=r'''
 it('sends a monthly RP03 request with finding-derived before_formula and no typed address or formula',async()=>{
  evidence.readSourceCells.mockResolvedValue([{cell:'N18',type:'formula',text:'=M10!B16-M10!B15',cached:'#VALUE!'}]);
  const prepare=vi.fn();
  const monthly={...f('N18','FORMULA_PATTERN_OUTLIER'),sheet:'Budget',formula_pattern:{pattern_type:'DOMINANT_NORMALIZED_PATTERN_OUTLIER',formula_region:'N18',dominant_pattern_id:'m',neighbor_count:4,evidence_locations:['L18','M18','O18','P18'],detection_basis:'synthetic',current_limitations:[],pattern_subtype:'REFERENCE_SHEET_DRIFT',before_formula:'=N15-N14'}} as Finding;
  render(<RepairProposalPicker findings={[monthly]} sheets={['Budget']} file={file} selection={{findings:[],locked:false,toggle:vi.fn()}} intent={noRepairIntent} available onPrepare={prepare}/>);
  await screen.findByText('=N15-N14');
  expect(screen.getByText(/검증 필요 후보/)).toBeVisible();
  fireEvent.click(screen.getByRole('checkbox',{name:/월별 수식 후보/}));
  fireEvent.click(screen.getByRole('button',{name:'이 묶음만 변경 예시 확인'}));
  expect(prepare).toHaveBeenCalledWith(expect.objectContaining({profile:RP03,sheet:'Budget',targets:['N18'],before_formula:'=N15-N14',confirmed:true,proposal:true}));
  expect(prepare.mock.calls[0][0]).not.toHaveProperty('anchor_formula');
 });
 it('keeps a monthly basket single-target and refuses mixing without erasing the existing choice',async()=>{
  evidence.readSourceCells.mockResolvedValue([{cell:'N18',type:'formula',text:'=M10!B16-M10!B15',cached:'#VALUE!'},{cell:'O18',type:'formula',text:'=M10!B17-M10!B16',cached:'#VALUE!'}]);
  const prepare=vi.fn();
  const m1={...f('N18','FORMULA_PATTERN_OUTLIER'),sheet:'Budget',formula_pattern:{pattern_type:'DOMINANT_NORMALIZED_PATTERN_OUTLIER',formula_region:'N18',dominant_pattern_id:'m',neighbor_count:4,evidence_locations:['L18','M18','O18','P18'],detection_basis:'synthetic',current_limitations:[],pattern_subtype:'REFERENCE_SHEET_DRIFT',before_formula:'=N15-N14'}} as Finding;
  const m2={...f('O18','FORMULA_PATTERN_OUTLIER'),sheet:'Budget',formula_pattern:{pattern_type:'DOMINANT_NORMALIZED_PATTERN_OUTLIER',formula_region:'O18',dominant_pattern_id:'m',neighbor_count:4,evidence_locations:['L18','M18','N18','P18'],detection_basis:'synthetic',current_limitations:[],pattern_subtype:'REFERENCE_SHEET_DRIFT',before_formula:'=O15-O14'}} as Finding;
  render(<RepairProposalPicker findings={[m1,m2]} sheets={['Budget']} file={file} selection={{findings:[],locked:false,toggle:vi.fn()}} intent={noRepairIntent} available onPrepare={prepare}/>);
  await screen.findByText('=N15-N14');
  fireEvent.click(screen.getByRole('checkbox',{name:/월별 수식 후보/}));
  fireEvent.click(screen.getByRole('button',{name:'변경 목록에 추가'}));
  expect(screen.getByRole('region',{name:'선택한 수정 목록'})).toHaveTextContent('선택한 1곳');
  fireEvent.click(screen.getAllByRole('button',{name:'이 수정 제안 보기'}).at(-1)!);
  await screen.findByText('=O15-O14');
  fireEvent.click(screen.getByRole('checkbox',{name:/월별 수식 후보/}));
  fireEvent.click(screen.getByRole('button',{name:'변경 목록에 추가'}));
  expect(screen.getByText(/월별 수식 후보는 다른 수정 묶음과 함께 보낼 수 없습니다/)).toBeVisible();
  expect(screen.getByRole('region',{name:'선택한 수정 목록'})).toHaveTextContent('선택한 1곳');
  fireEvent.click(screen.getByRole('button',{name:'선택한 1곳의 변경 예시 확인'}));
  expect(prepare).toHaveBeenCalledWith(expect.objectContaining({profile:RP03,targets:['N18'],before_formula:'=N15-N14'}));
 });
 it('passes monthly before_formula through the delivery preflight request',async()=>{
  const actions:Record<string,unknown>[]=[];
  vi.stubGlobal('fetch',vi.fn(async(_url,init)=>{const a=JSON.parse(String(init?.body));actions.push(a);return ok(a.action==='capabilities'?{max_bytes:2097152,payment_mode:'OFF'}:a.action==='create_input'?base:a.action==='preflight'?{...base,revision:2,policy:a.policy,preflight:plan.preflight}:{...plan,policy:a.policy});}));
  render(<DeliveryWorkspace file={file} reviewDraft={{profile:RP03,sheet:'Budget',targets:['N18'],before_formula:'=N15-N14',confirmed:true,proposal:true}}/>);
  fireEvent.click(await screen.findByRole('checkbox',{name:/업로드 권한/}));
  fireEvent.click(screen.getByRole('button',{name:/원본으로 수정 범위 확인/}));
  await waitFor(()=>expect(actions.some(a=>a.action==='preflight')).toBe(true));
  expect(actions.find(a=>a.action==='preflight')).toMatchObject({policy:{profile:RP03,sheet:'Budget',targets:['N18'],before_formula:'=N15-N14',confirmed:true}});
 });
'''
if not s.rstrip().endswith('});'):
    raise SystemExit('unexpected test end')
s=s.rstrip()[:-3]+insert+'});\n'
p.write_text(s,encoding='utf-8',newline='\n')
