$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $PSScriptRoot
$Pack=Join-Path $Root 'samples\WorkbookCare_Complex_Validation_2026-09-13'
$Out=Join-Path $Root 'artifacts\verification\d08-complex'
$spec=Get-Content -Raw -Encoding UTF8 (Join-Path $Pack 'expected\source-spec.json')|ConvertFrom-Json
$oracle=Get-Content -Raw -Encoding UTF8 (Join-Path $Pack 'expected\expected.json')|ConvertFrom-Json
$pdfDir=Join-Path $Out 'input-pdfs';New-Item -ItemType Directory -Path $pdfDir -Force|Out-Null
$excel=$null;$results=@();$visuals=@()
try {
 $excel=New-Object -ComObject Excel.Application
 $excel.Visible=$false;$excel.DisplayAlerts=$false;$excel.EnableEvents=$false;$excel.AskToUpdateLinks=$false;$excel.AutomationSecurity=3
 $index=0
 foreach($item in $spec.books){
  $index++;$path=Join-Path $Pack $item.file;$hash=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLower()
  $book=$excel.Workbooks.Open($path,0,$true);$checked=0;$formulaChecks=0
  try {
   $excel.CalculateFullRebuild();$sheetIndex=0
   foreach($sheetSpec in $item.sheets){
    $sheetIndex++;$sheet=$book.Worksheets.Item($sheetSpec.name)
    foreach($prop in $sheetSpec.cells.PSObject.Properties){
     $actual=$sheet.Range($prop.Name).Value2;$value=$prop.Value
     if($value -is [string]){if($value -eq '' -and $null -eq $actual){continue};if($actual -isnot [string] -or $actual -cne $value){throw ('Source text differs: '+$index+':'+$prop.Name)}}
     elseif([Math]::Abs([double]$actual-[double]$value) -gt 0.0000001){throw ('Source number differs: '+$index+':'+$prop.Name)}
     $checked++
    }
    foreach($prop in $sheetSpec.formulas.PSObject.Properties){
     if(-not $sheet.Range($prop.Name).HasFormula){throw 'Expected formula missing'};$formulaChecks++
    }
    if($item.kind -eq 'repair' -and $sheetSpec.name -eq '정산'){
     $case=$oracle.repair.RP01_ALL
     foreach($prop in $case.expected.PSObject.Properties){
      $expected=$prop.Value
      $impact=$case.impact.PSObject.Properties[$prop.Name]
      if($impact){$expected=$impact.Value.before}
      $actual=$sheet.Range($prop.Name).Value2
      if($expected.type -eq 'blank'){if($null -ne $actual){throw 'Expected true blank differs'}}
      elseif($expected.type -eq 'text'){if($actual -isnot [string] -or $actual -cne $expected.value){throw 'Expected source text differs'}}
      elseif([Math]::Abs([double]$actual-[double]$expected.value) -gt 0.0000001){throw ('Independent original calculation differs: '+$prop.Name)}
      $checked++
     }
    }
    if($item.kind -eq 'unsupported' -and $sheetSpec.name -eq '월별보고'){
     if($sheet.ChartObjects().Count -ne 1){throw 'Native chart missing'}
     for($month=1;$month -le 12;$month++){$sum=0;for($n=1;$n -le 240;$n++){if((($n-1)%12)+1 -eq $month){$sum+=$n*127}};if($sheet.Range('B'+($month+5)).Value2 -ne $sum){throw 'Native cross-sheet SUMIF differs'}}
    }
    if($item.kind -eq 'unsupported' -and $sheetSpec.name -eq '거래원장' -and $sheet.ListObjects.Count -ne 1){throw 'Native Excel table missing'}
    $area=if($sheetSpec.name -eq '월별보고'){'A1:L20'}elseif($sheetSpec.name -eq '정산' -or $sheetSpec.name -in @('온라인','매장','반품')){'A1:M17'}elseif($sheetSpec.name -eq '보존정보'){'A1:C14'}elseif($sheetSpec.name -eq '거래'){'A1:E12'}else{'A1:F14'}
    $sheet.PageSetup.PrintArea=$area;$sheet.PageSetup.Orientation=2;$sheet.PageSetup.Zoom=$false;$sheet.PageSetup.FitToPagesWide=1;$sheet.PageSetup.FitToPagesTall=1
    $pdf=Join-Path $pdfDir ($index.ToString()+'-'+$sheetIndex.ToString()+'.pdf');$sheet.ExportAsFixedFormat(0,$pdf);$visuals+=@{pdf=$pdf;sheet=$sheetSpec.name;file=$item.file}
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($sheet)
   }
  }finally{$book.Close($false);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($book)}
  if((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLower() -cne $hash){throw 'Read-only verification changed source'}
  $results+=@{file=$item.file;sha256=$hash;source_value_checks=$checked;formula_presence_checks=$formulaChecks;native_open='PASS';original_unchanged=$true}
 }
 @{status='PASS';excel_version=$excel.Version;excel_build=$excel.Build;results=$results;visuals=$visuals;product_or_pg_verified=$false}|ConvertTo-Json -Depth 10|Set-Content -LiteralPath (Join-Path $Out 'input-excel.json') -Encoding UTF8
 Write-Output ('Native Excel input quality PASS: '+$results.Count+' workbooks. This is source-fixture validation, not product execution.')
}finally{if($excel){$excel.Quit();[void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel)};[GC]::Collect();[GC]::WaitForPendingFinalizers()}
