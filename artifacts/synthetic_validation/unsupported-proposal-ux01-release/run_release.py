from pathlib import Path
import sys,runpy
ROOT=Path(__file__).resolve().parents[3]
OLD=ROOT/'artifacts/synthetic_validation/monthly-ux07-release/resume02/release-tools'
sys.path.insert(0,str(OLD))
import release_config as cfg
cfg.WEB_RELEASE=Path(__file__).resolve().parent/'output'
cfg.SOURCE_FREEZE=Path(__file__).resolve().parent/'source-freeze.json'
cfg.API_RELEASE=ROOT/'artifacts/synthetic_validation/false-repair-guard01-release/release-tools/output/api-release'
cfg.CONFIRM_MUTATION='UNSUPPORTED_PROPOSAL_UX01_RELEASE_APPROVED'
runpy.run_path(str(Path(__file__).resolve().parent/'release_web.py'),run_name='__main__')
