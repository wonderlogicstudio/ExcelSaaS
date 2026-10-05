"""Validate this instruction package and its illustrative fixtures (standard library).
Does not read local customer files, execute app code, call APIs, or change project status.
"""
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET
import json, re, hashlib, ast

ROOT=Path(__file__).resolve().parents[1]
checks=[]
def require(name,ok):
    checks.append({'name':name,'passed':bool(ok)})
    if not ok: raise AssertionError(name)
def load(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    commands=load('commands.json'); bundles=load('bundles/BUNDLES.json')
    require('eight_unique_bundles',len(bundles)==len({b['id'] for b in bundles})==8)
    require('commands_cover_bundles',{c['id'] for c in commands}=={b['id'] for b in bundles})
    require('prompt_files_match',all((ROOT/f"prompts/{c['id']}.txt").read_text(encoding='utf-8').strip()==c['text'].strip() for c in commands))
    require('start_prompt_matches_D01',(ROOT/'CODEX_START_D01.txt').read_text(encoding='utf-8').strip()==commands[0]['text'].strip())
    ids={b['id'] for b in bundles}
    require('dependencies_exist',all(set(b['deps'])<=ids for b in bundles))
    visited=set()
    def visit(x,path):
        if x in path:raise AssertionError('cycle')
        if x in visited:return
        for d in next(b for b in bundles if b['id']==x)['deps']:visit(d,path+[x])
        visited.add(x)
    for x in ids:visit(x,[])
    require('dependency_graph_acyclic',len(visited)==8)
    preserved=load('reference/PRESERVATION.json')
    zp=ROOT/'reference/previous_v31.zip'
    require('previous_zip_exact_hash',digest(zp)==preserved['sha256'])
    with ZipFile(zp) as z:
        require('previous_zip_integrity',z.testzip() is None)
        name=next(n for n in z.namelist() if n.endswith('/mapping/TASK_120_DECISIONS.json'))
        old=json.loads(z.read(name))
        cfname=next(n for n in z.namelist() if n.endswith('/mapping/CF_UXR_DECISIONS.json'))
        oldcf=json.loads(z.read(cfname))
        for f in ['BASELINE_EXPECTED.json','BASELINE_INPUTS.json','EDGE_CASES.json']:
            n=next(n for n in z.namelist() if n.endswith('/fixtures/'+f))
            require('original_comparison_fixture_'+f,z.read(n)==(ROOT/'fixtures/comparison'/f).read_bytes())
    mapping=load('mapping/TASK_120_V32.json')
    require('120_unique_original_tasks',len(mapping)==len({m['id'] for m in mapping})==120)
    require('120_records_unchanged',[m['original_v31_record'] for m in mapping]==old)
    require('task_bundle_links_valid',all(set(m['v32_delta']['bundles'])<=ids for m in mapping))
    cf=load('mapping/CF_UXR_V32.json')
    require('17_CF_UXR_records_unchanged',len(cf)==17 and [c['original_v31_record'] for c in cf]==oldcf)
    require('no_false_original_completion',all(m['v32_delta']['original_task_fully_completed'] is False for m in mapping))
    require('all_JSON_parse',all(json.loads(p.read_text(encoding='utf-8')) is not None for p in ROOT.rglob('*.json')))
    require('all_Python_parse',all(ast.parse(p.read_text(encoding='utf-8')) is not None for p in (ROOT/'tools').glob('*.py')))
    # Validate real Markdown hyperlinks, not illustrative code paths.
    broken=[]
    for p in ROOT.rglob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
            if target.startswith(('http:','https:','mailto:','#')):continue
            target=target.split('#')[0]
            if not (p.parent/target).exists():broken.append((str(p.relative_to(ROOT)),target))
    require('markdown_local_links_exist',not broken)
    for f in ['START_HERE.html','examples/DELIVERY_GUIDE.html','examples/repair_delivery/verification_DEMO.html']:
        p=ROOT/f;links=re.findall(r'href="([^"]+)"',p.read_text(encoding='utf-8'))
        require('HTML_local_links_'+f,all((p.parent/t.split('#')[0]).exists() for t in links if not t.startswith(('http:','https:','#'))))
    n={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    def cellmap(filename):
        with ZipFile(ROOT/'examples/repair_delivery'/filename) as z:
            require('XLSX_ZIP_'+filename,z.testzip() is None)
            t=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
            return {c.get('r'):(c.get('t'),c.findtext('s:v',None,n),c.findtext('s:f',None,n)) for c in t.findall('.//s:c',n)}
    a=cellmap('source_DEMO.xlsx');b=cellmap('workbookcare_repaired_DEMO.xlsx');c=cellmap('changes_DEMO.xlsx')
    require('numeric_type_conversion_example',a['C7']==('str','12000',None) and b['C7']==('n','12000',None))
    require('formula_restoration_example',a['E8'][2] is None and b['E8'][2]=='ROUND(B8*C8*(1-D8),0)' and b['E8'][1]=='9500')
    require('totals_match_independent_oracle',a['E10'][1]=='51000' and b['E10'][1]=='60500')
    require('ids_keep_leading_zero',all(a[p]==b[p]==('str',v,None) for p,v in [('A6','0001'),('A7','0002'),('A8','0003')]))
    require('example_cell_changes_bounded',{p for p in a if a[p]!=b.get(p)}=={'C7','E8','E10'})
    require('change_log_formulas_are_literal',not any(v[2] for v in c.values()))
    dm=load('examples/repair_delivery/manifest_DEMO.json')
    require('demo_not_product_verified',not dm['product_pipeline_executed'] and not dm['excel_reference_executed'])
    require('demo_hashes_match',all(digest(ROOT/'examples/repair_delivery'/x['name'])==x['sha256'] for x in dm['required_artifacts']))
    cases=load('fixtures/NEGATIVE_ACCEPTANCE_CASES.json')
    require('32_negative_acceptance_cases',len(cases)==len({c['id'] for c in cases})==32)
    require('no_live_progress_shipped',not (ROOT/'delivery-progress.json').exists())
    checksum_file=ROOT/'CHECKSUMS.sha256'
    if checksum_file.exists():
        entries=[line.split('  ',1) for line in checksum_file.read_text(encoding='utf-8').splitlines() if line.strip()]
        require('packaged_file_checksums',all((ROOT/n).exists() and digest(ROOT/n)==h for h,n in entries))
    result={'scope':'package+public illustrative files only; not app/Excel/PG', 'passed':len(checks),'failed':0,'checks':checks}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return result
if __name__=='__main__':main()
