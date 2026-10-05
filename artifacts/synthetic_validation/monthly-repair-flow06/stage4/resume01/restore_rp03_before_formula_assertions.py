from pathlib import Path
p=Path('apps/web/src/components/ProposalFlow.test.tsx')
s=p.read_text(encoding='utf-8')
s=s.replace("expect(prepare).toHaveBeenCalledWith(expect.objectContaining({profile:RP03,sheet:'Budget',targets:['N18'],confirmed:true,proposal:true}));", "expect(prepare).toHaveBeenCalledWith(expect.objectContaining({profile:RP03,sheet:'Budget',targets:['N18'],before_formula:'=N15-N14',confirmed:true,proposal:true}));")
s=s.replace("expect(prepare).toHaveBeenCalledWith(expect.objectContaining({profile:RP03,targets:['N18']}));", "expect(prepare).toHaveBeenCalledWith(expect.objectContaining({profile:RP03,targets:['N18'],before_formula:'=N15-N14'}));")
s=s.replace("render(<DeliveryWorkspace file={file} reviewDraft={{profile:RP03,sheet:'Budget',targets:['N18'],confirmed:true,proposal:true}}/>);", "render(<DeliveryWorkspace file={file} reviewDraft={{profile:RP03,sheet:'Budget',targets:['N18'],before_formula:'=N15-N14',confirmed:true,proposal:true}}/>);")
s=s.replace("expect(actions.find(a=>a.action==='preflight')).toMatchObject({policy:{profile:RP03,sheet:'Budget',targets:['N18'],confirmed:true}});", "expect(actions.find(a=>a.action==='preflight')).toMatchObject({policy:{profile:RP03,sheet:'Budget',targets:['N18'],before_formula:'=N15-N14',confirmed:true}});")
p.write_text(s,encoding='utf-8',newline='\n')
