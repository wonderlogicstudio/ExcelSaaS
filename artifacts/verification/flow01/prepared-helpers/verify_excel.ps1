param([string]$Directory='compatibility',[ValidateSet('d04','d08')][string]$Stage='d04')
$ErrorActionPreference='Stop'
$root='C:/Users/JinwonLee/project/ExcelSaaS'
$verificationRoot=[IO.Path]::GetFullPath('C:/Users/JinwonLee/project/DigitalTwin/.tmp/workbookcare-flow01')
$dir=[IO.Path]::GetFullPath((Join-Path $verificationRoot $Directory))
if(-not $dir.StartsWith($verificationRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Verification directory outside synthetic artifact root'}
$inputs=Get-Content -LiteralPath (Join-Path $verificationRoot 'compatibility/inputs.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$excel=$null
$results=@()
try {
 $excel=New-Object -ComObject Excel.Application
 $excel.Visible=$false
 $excel.DisplayAlerts=$false
 $excel.AutomationSecurity=3
 $excel.AskToUpdateLinks=$false
 $excel.EnableEvents=$false
 $version=$excel.Version
 $build=$excel.Build
 foreach($profile in @('RP01','RP02')){
  $path=Join-Path $dir "$profile-REPAIRED_XLSX.xlsx"
  $hash=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLower()
  $book=$excel.Workbooks.Open($path,0,$true)
  try {
   $sheet=$book.Worksheets.Item(1)
   $excel.CalculateFullRebuild()
   $expected=if($profile -eq 'RP01'){@{B2=12000;B3=3500;H2=15500;F12=12200}}else{@{F3=6000;F12=18200;H2=0}}
   foreach($key in $expected.Keys){
    $cell=$sheet.Range($key)
    if($cell.Value2 -is [string] -or [double]$cell.Value2 -ne [double]$expected[$key]){throw "Excel output mismatch in synthetic $profile / $key"}
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell)
   }
   $cell=$sheet.Range('A2')
   if($cell.Value2 -cne '00123'){throw 'Identifier preservation failed'}
   [void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell)
   if($profile -eq 'RP02'){
    $cell=$sheet.Range('F3')
    if($cell.Formula -cne '=ROUND(C3*D3*(1-E3),0)'){throw 'Actual restored formula differs'}
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell)
   }
   [void][Runtime.InteropServices.Marshal]::ReleaseComObject($sheet)
  } finally {$book.Close($false);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($book)}
  if((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLower() -ne $hash){throw 'Read-only reference modified output'}
  $changes=Join-Path $dir "$profile-CHANGES_XLSX.xlsx"
  $book=$excel.Workbooks.Open($changes,0,$true)
  try {
   $sheet=$book.Worksheets.Item('변경 셀')
   $expectedCount=if($profile -eq 'RP01'){3}else{2}
   if($sheet.UsedRange.Rows.Count -ne $expectedCount){throw 'Changes rows mismatch'}
   if($profile -eq 'RP02'){
    $cell=$sheet.Range('F2')
    if($cell.HasFormula -or $cell.Value2 -cne '=ROUND(C3*D3*(1-E3),0)'){throw 'Report formula must be literal text'}
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell)
   }
   [void][Runtime.InteropServices.Marshal]::ReleaseComObject($sheet)
  } finally {$book.Close($false);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($book)}
  $results+=@{profile=$profile;repaired_opened=$true;changes_opened=$true;actual_values_match=$true;literal_report_formulas=$true;read_only_hash_unchanged=$true;output_hash=$hash}
 }
 $record=@{status='PASS';kind='ACTUAL_PRODUCT_PATCH_AND_INSTALLED_EXCEL_REOPEN';excel_version=$version;excel_build=$build;profiles=@('RP01','RP02');patch_fingerprint=$inputs.patch_fingerprint;results=$results}
 $record|ConvertTo-Json -Depth 10|Set-Content -LiteralPath (Join-Path $dir 'excel-reopen.json') -Encoding UTF8
 Write-Output 'RP01 and RP02: actual repaired and changes XLSX reopened in installed Excel; independent expected values matched.'
} finally {
 if($excel){$excel.Quit();[void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel)}
 [GC]::Collect();[GC]::WaitForPendingFinalizers()
}
