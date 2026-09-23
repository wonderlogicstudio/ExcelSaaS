param([string]$Directory='compatibility',[ValidateSet('d04','d08')][string]$Stage='d04')
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$artifactRoot=[IO.Path]::GetFullPath((Join-Path $root 'artifacts'))
if([IO.Path]::IsPathRooted($Directory)){$dir=[IO.Path]::GetFullPath($Directory)}else{$dir=[IO.Path]::GetFullPath((Join-Path (Join-Path $root ('artifacts/verification/'+$Stage)) $Directory))}
if($dir -ne $artifactRoot -and -not $dir.StartsWith($artifactRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Verification directory outside repository artifacts root'}
$inputs=Get-Content -LiteralPath (Join-Path $dir 'inputs.json') -Raw -Encoding UTF8 | ConvertFrom-Json
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
 foreach($profile in @('RP01','RP02','RP03')){
  $path=Join-Path $dir "$profile-REPAIRED_XLSX.xlsx"
  $hash=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLower()
  $changes=Join-Path $dir "$profile-CHANGES_XLSX.xlsx"
  $changesHash=(Get-FileHash -LiteralPath $changes -Algorithm SHA256).Hash.ToLower()
  $html=Join-Path $dir "$profile-VERIFICATION_HTML.html"
  $htmlHash=(Get-FileHash -LiteralPath $html -Algorithm SHA256).Hash.ToLower()
  $nativeFormula=$null
  $book=$excel.Workbooks.Open($path,0,$true)
  try {
   $sheet=$book.Worksheets.Item(1)
   $excel.CalculateFullRebuild()
   if($profile -eq 'RP01'){$expected=@{B2=12000;B3=3500;H2=15500;F12=12200}}
   elseif($profile -eq 'RP02'){$expected=@{F3=6000;F12=18200;H2=0}}
   else{$expected=@{N18=-5}}
   foreach($key in $expected.Keys){
    $cell=$sheet.Range($key)
    if($cell.Value2 -is [string] -or [double]$cell.Value2 -ne [double]$expected[$key]){throw "Excel output mismatch in synthetic $profile / $key"}
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell)
   }
   if($profile -ne 'RP03'){
    $cell=$sheet.Range('A2')
    if($cell.Value2 -cne '00123'){throw 'Identifier preservation failed'}
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell)
   }
   if($profile -eq 'RP02'){
    $cell=$sheet.Range('F3')
    if($cell.Formula -cne '=ROUND(C3*D3*(1-E3),0)'){throw 'Actual restored formula differs'}
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell)
   }
   if($profile -eq 'RP03'){
    $cell=$sheet.Range('N18')
    $nativeFormula=[string]$cell.Formula
    $canonicalNative=$nativeFormula.Replace("'M10'!",'M10!')
    if(-not [string]::Equals($canonicalNative,'=M10!B16-M10!B15',[StringComparison]::OrdinalIgnoreCase)){throw 'Actual monthly formula differs'}
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell)
   }
   [void][Runtime.InteropServices.Marshal]::ReleaseComObject($sheet)
  } finally {$book.Close($false);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($book)}
  if((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLower() -ne $hash){throw 'Read-only reference modified repaired output'}
  $book=$excel.Workbooks.Open($changes,0,$true)
  try {
   $sheet=$book.Worksheets.Item('변경 셀')
   if($profile -eq 'RP01'){$expectedCount=3}else{$expectedCount=2}
   if($sheet.UsedRange.Rows.Count -ne $expectedCount){throw 'Changes rows mismatch'}
   if($profile -eq 'RP02'){
    $cell=$sheet.Range('F2')
    if($cell.HasFormula -or $cell.Value2 -cne '=ROUND(C3*D3*(1-E3),0)'){throw 'Report formula must be literal text'}
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell)
   }
   if($profile -eq 'RP03'){
    $cell=$sheet.Range('F2')
    if($cell.HasFormula -or $cell.Value2 -cne "='M10'!B16-'M10'!B15"){throw 'Monthly report formula must be literal text'}
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell)
   }
   [void][Runtime.InteropServices.Marshal]::ReleaseComObject($sheet)
  } finally {$book.Close($false);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($book)}
  if((Get-FileHash -LiteralPath $changes -Algorithm SHA256).Hash.ToLower() -ne $changesHash){throw 'Read-only reference modified changes output'}
  if((Get-FileHash -LiteralPath $html -Algorithm SHA256).Hash.ToLower() -ne $htmlHash){throw 'Read-only reference modified verification HTML'}
  $results+=@{profile=$profile;repaired_opened=$true;changes_opened=$true;actual_values_match=$true;literal_report_formulas=$true;read_only_hash_unchanged=$true;output_hash=$hash;changes_hash=$changesHash;verification_html_hash=$htmlHash;native_formula=$nativeFormula}
 }
 $record=@{status='PASS';kind='ACTUAL_PRODUCT_PATCH_AND_INSTALLED_EXCEL_REOPEN';excel_version=$version;excel_build=$build;profiles=@('RP01','RP02','RP03');patch_fingerprint=$inputs.patch_fingerprint;results=$results}
 $record|ConvertTo-Json -Depth 10|Set-Content -LiteralPath (Join-Path $dir 'excel-reopen.json') -Encoding UTF8
 Write-Output 'RP01, RP02, and RP03: actual repaired and changes XLSX reopened in installed Excel; independent expected values matched.'
} finally {
 if($excel){$excel.Quit();[void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel)}
 [GC]::Collect();[GC]::WaitForPendingFinalizers()
}
