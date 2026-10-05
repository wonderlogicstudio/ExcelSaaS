from pathlib import Path
import ast
files = [
    Path('scripts/verify_delivery_patch_compatibility.py'),
    Path('scripts/register_delivery_patch_reference.py'),
]
for file in files:
    ast.parse(file.read_text(encoding='utf-8-sig'))
text = Path('scripts/verify_delivery_output_excel.ps1').read_text(encoding='utf-8-sig')
required = [
    "Join-Path $dir 'inputs.json'",
    "Join-Path $dir 'excel-reopen.json'",
    "changes_hash",
    "verification_html_hash",
]
missing = [item for item in required if item not in text]
if missing:
    raise SystemExit(f'missing PS containment markers: {missing}')
for file in files:
    text = file.read_text(encoding='utf-8-sig')
    for marker in ['artifacts', 'resolve_']:
        if marker not in text:
            raise SystemExit(f'{file} missing {marker}')
print('script containment syntax/path-marker checks passed')
