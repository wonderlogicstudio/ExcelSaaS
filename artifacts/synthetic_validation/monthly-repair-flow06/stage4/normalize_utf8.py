from pathlib import Path
files = [
 'apps/web/src/lib/repairReview.ts',
 'apps/web/src/lib/repairProposals.ts',
 'apps/web/src/components/RepairProposalPicker.tsx',
 'apps/web/src/components/RepairReview.tsx',
 'apps/web/src/components/DeliveryWorkspace.tsx',
 'apps/web/src/components/RepairPlanPreview.tsx',
 'apps/web/src/components/ProposalExample.tsx',
 'apps/web/src/types.ts',
]
for name in files:
    p = Path(name)
    data = p.read_bytes()
    if data.startswith(b'\xef\xbb\xbf'):
        data = data[3:]
    text = data.decode('utf-8')
    text = text.replace('대 주소를 몰라도 됩니다.', '셀 주소를 몰라도 됩니다.')
    p.write_text(text, encoding='utf-8', newline='\n')
