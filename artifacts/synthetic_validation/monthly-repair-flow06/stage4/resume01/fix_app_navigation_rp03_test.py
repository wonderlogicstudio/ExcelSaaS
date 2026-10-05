from pathlib import Path
p=Path('apps/web/src/App.navigation.test.tsx')
s=p.read_text(encoding='utf-8')
s=s.replace("it('maps only explicit numeric text and true-blank candidates to a server preflight, never infers a formula', () => {", "it('maps explicit repair candidates and value-free monthly candidates without inferring generic formulas', () => {")
line="    expect(reviewDisposition({...f,rule_code:'FORMULA_PATTERN_OUTLIER',sheet:'Budget',cell:'N18',formula_pattern:{pattern_type:'DOMINANT_NORMALIZED_PATTERN_OUTLIER',formula_region:'N18',dominant_pattern_id:'x',neighbor_count:4,evidence_locations:['L18','M18','O18','P18'],detection_basis:'synthetic',current_limitations:[],pattern_subtype:'REFERENCE_SHEET_DRIFT'}}).profile).toBeUndefined();\n"
if line not in s:
    raise SystemExit('contradictory assertion not found')
s=s.replace(line,'')
# Preserve a generic nonmonthly formula outlier negative explicitly.
needle="    expect(reviewDisposition({...f,rule_code:'FORMULA_PATTERN_OUTLIER',formula_pattern:null}).profile).toBeUndefined();\n"
insert=needle+"    expect(reviewDisposition({...f,rule_code:'FORMULA_PATTERN_OUTLIER',sheet:'Budget',cell:'N18',formula_pattern:{pattern_type:'DOMINANT_NORMALIZED_PATTERN_OUTLIER',formula_region:'N18',dominant_pattern_id:'x',neighbor_count:4,evidence_locations:['L18','M18','O18','P18'],detection_basis:'synthetic',current_limitations:[],pattern_subtype:'GENERIC_PATTERN_DRIFT'}}).profile).toBeUndefined();\n"
if needle not in s:
    raise SystemExit('generic negative anchor not found')
s=s.replace(needle,insert)
p.write_text(s,encoding='utf-8',newline='\n')
