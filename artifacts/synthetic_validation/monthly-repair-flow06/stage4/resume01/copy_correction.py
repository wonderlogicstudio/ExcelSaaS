from pathlib import Path
p=Path('apps/web/src/components/RepairProposalPicker.tsx')
s=p.read_text(encoding='utf-8')
s=s.replace('이 수식은 사용자가 입력하지 않고 진단 결과에서 전달됩니다.', '이 수식은 사용자가 입력하지 않고 업로드한 원본에서 읽은 수식입니다.')
s=s.replace('제안 선택은 변경 승인 전이 아닙니다.', '제안 선택은 변경 승인이 아닙니다.')
p.write_text(s,encoding='utf-8',newline='\n')
