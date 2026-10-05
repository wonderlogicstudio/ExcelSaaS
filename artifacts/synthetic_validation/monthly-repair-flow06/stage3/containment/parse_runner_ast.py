from pathlib import Path
import ast
ast.parse(Path('artifacts/synthetic_validation/monthly-repair-flow06/stage3/rp03_saved_artifact_runtime.py').read_text(encoding='utf-8-sig'))
print('runner ast parse passed')
