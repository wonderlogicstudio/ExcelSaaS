from pathlib import Path
p=Path('apps/web/src/App.navigation.test.tsx')
s=p.read_text(encoding='utf-8')
needle="""    expect(reviewDisposition({...f,rule_code:'FORMULA_PATTERN_OUTLIER'}).profile).toBeUndefined();
    expect(reviewDisposition({...f,rule_code:'FORMULA_PATTERN_GAP'}).profile).toBeUndefined();
"""
replacement="""    expect(reviewDisposition({...f,rule_code:'FORMULA_PATTERN_OUTLIER'}).profile).toBeUndefined();
    expect(reviewDisposition({...f,rule_code:'FORMULA_PATTERN_OUTLIER',sheet:'Budget',cell:'N18',formula_pattern:{pattern_type:'DOMINANT_NORMALIZED_PATTERN_OUTLIER',formula_region:'N18',dominant_pattern_id:'x',neighbor_count:4,evidence_locations:['L18','M18','O18','P18'],detection_basis:'synthetic',current_limitations:[],pattern_subtype:'REFERENCE_SHEET_DRIFT'}}).profile).toBeUndefined();
    expect(reviewDisposition({...f,rule_code:'FORMULA_PATTERN_OUTLIER',sheet:'Budget',cell:'N18',formula_pattern:{pattern_type:'DOMINANT_NORMALIZED_PATTERN_OUTLIER',formula_region:'N18',dominant_pattern_id:'x',neighbor_count:4,evidence_locations:['L18','M18','O18','P18'],detection_basis:'synthetic',current_limitations:[],pattern_subtype:'REFERENCE_SHEET_DRIFT',before_formula:'=N15-N14'}}).profile).toBe('RP03_MONTHLY_SHEET_FORMULA_REPLACEMENT_V1');
    expect(reviewDisposition({...f,rule_code:'FORMULA_PATTERN_GAP'}).profile).toBeUndefined();
"""
if needle not in s:
    raise SystemExit('navigation needle not found')
p.write_text(s.replace(needle,replacement),encoding='utf-8',newline='\n')
