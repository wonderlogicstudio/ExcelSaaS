from pathlib import Path
path = Path('scripts/verify_delivery_output_excel.ps1')
text = path.read_text(encoding='utf-8-sig')
text = text.replace(
"  $book=$excel.Workbooks.Open($path,0,$true)\n  try {",
"  $nativeFormula=$null\n  $book=$excel.Workbooks.Open($path,0,$true)\n  try {",
)
text = text.replace(
'''   if($profile -eq 'RP03'){
    $cell=$sheet.Range('N18')
    if($cell.Formula -cne "='M10'!B16-'M10'!B15"){throw 'Actual monthly formula differs'}
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell)
   }''',
'''   if($profile -eq 'RP03'){
    $cell=$sheet.Range('N18')
    $nativeFormula=[string]$cell.Formula
    $canonicalNative=$nativeFormula.Replace("'M10'!",'M10!')
    if(-not [string]::Equals($canonicalNative,'=M10!B16-M10!B15',[StringComparison]::OrdinalIgnoreCase)){throw 'Actual monthly formula differs'}
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell)
   }''',
)
text = text.replace(
"  $results+=@{profile=$profile;repaired_opened=$true;changes_opened=$true;actual_values_match=$true;literal_report_formulas=$true;read_only_hash_unchanged=$true;output_hash=$hash;changes_hash=$changesHash;verification_html_hash=$htmlHash}",
"  $results+=@{profile=$profile;repaired_opened=$true;changes_opened=$true;actual_values_match=$true;literal_report_formulas=$true;read_only_hash_unchanged=$true;output_hash=$hash;changes_hash=$changesHash;verification_html_hash=$htmlHash;native_formula=$nativeFormula}",
)
path.write_text(text, encoding='utf-8')
