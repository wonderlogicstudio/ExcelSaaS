param([ValidateSet('repair','comparison')][string]$Mode='repair')
$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $PSScriptRoot
$Pack=Join-Path $Root 'samples\WorkbookCare_Complex_Validation_2026-09-13'
$Out=Join-Path $Root 'artifacts\verification\d08-complex'
$Downloads=Join-Path $Out 'browser-downloads'
$spec=Get-Content -Raw -Encoding UTF8 (Join-Path $Pack 'expected\source-spec.json')|ConvertFrom-Json
$oracle=Get-Content -Raw -Encoding UTF8 (Join-Path $Pack 'expected\expected.json')|ConvertFrom-Json
$pdfDir=Join-Path $Out 'download-pdfs';New-Item -ItemType Directory -Path $pdfDir -Force|Out-Null
function Read-Cell($grid,[string]$address){$letters=[regex]::Match($address,'^[A-Z]+').Value;$column=0;foreach($c in $letters.ToCharArray()){$column=$column*26+[int]$c-64};$row=[int][regex]::Match($address,'\d+$').Value;return $grid[$row,$column]}
function Assert-Value($actual,$value,$label){
 if($value -is [string]){if($value -eq '' -and $null -eq $actual){return};if($actual -isnot [string] -or $actual -cne $value){throw ('Literal source mismatch: '+$label)}}
 elseif($null -eq $value){if($null -ne $actual){throw ('Blank mismatch: '+$label)}}
 elseif($actual -is [string] -or [Math]::Abs([double]$actual-[double]$value) -gt 0.0000001){throw ('Numeric mismatch: '+$label)}
}
$excel=$null;$results=@()
try{
 $excel=New-Object -ComObject Excel.Application;$excel.Visible=$false;$excel.DisplayAlerts=$false;$excel.EnableEvents=$false;$excel.AskToUpdateLinks=$false;$excel.AutomationSecurity=3
 foreach($label in $(if($Mode -eq 'repair'){@('RP01_ALL','RP01_SUBSET','RP02_ALL')}else{@()})){
  $case=$oracle.repair.PSObject.Properties[$label].Value
  $file=@(Get-ChildItem -LiteralPath (Join-Path $Downloads $label) -Filter 'workbookcare_repaired_*.xlsx');if($file.Count -ne 1){throw 'Expected one actual repaired download'}
  $before=(Get-FileHash -LiteralPath $file[0].FullName -Algorithm SHA256).Hash
  $book=$excel.Workbooks.Open($file[0].FullName,0,$true)
  try{
   $excel.CalculateFullRebuild();$checks=0;$formulas=0;$preserved=0
   foreach($sheetSpec in $spec.books[2].sheets){
    $sheet=$book.Worksheets.Item($sheetSpec.name);$grid=$sheet.Range('A1:M140').Value2;$formulaGrid=$sheet.Range('A1:M140').Formula
    foreach($prop in $sheetSpec.cells.PSObject.Properties){
     if($sheetSpec.name -eq $case.sheet -and $case.targets -contains $prop.Name){continue}
     Assert-Value (Read-Cell $grid $prop.Name) $prop.Value ('preservation '+$prop.Name);$preserved++
    }
    foreach($prop in $sheetSpec.formulas.PSObject.Properties){Assert-Value (Read-Cell $formulaGrid $prop.Name) $prop.Value ('formula '+$prop.Name);$formulas++}
    if($sheetSpec.name -eq $case.sheet){
     foreach($prop in $case.expected.PSObject.Properties){$expected=$prop.Value;$value=if($expected.type -eq 'blank'){$null}else{$expected.value};Assert-Value (Read-Cell $grid $prop.Name) $value $prop.Name;$checks++}
     foreach($prop in $case.restored_formulas.PSObject.Properties){Assert-Value (Read-Cell $formulaGrid $prop.Name) $prop.Value ('restored '+$prop.Name);$formulas++}
     $sheet.PageSetup.PrintArea='A118:J131';$sheet.PageSetup.Orientation=2;$sheet.PageSetup.Zoom=$false;$sheet.PageSetup.FitToPagesWide=1;$sheet.PageSetup.FitToPagesTall=1;$sheet.ExportAsFixedFormat(0,(Join-Path $pdfDir ($label+'.pdf')))
    }
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($sheet)
   }
   $results+=@{case=$label;status='PASS';native_calculated_cells=$checks;formula_checks=$formulas;preserved_source_values=$preserved;sum_after=$case.sum_after;sha256=$before.ToLower();download_unchanged=$true}
  }finally{$book.Close($false);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($book)}
  if((Get-FileHash -LiteralPath $file[0].FullName -Algorithm SHA256).Hash -cne $before){throw 'Native read-only validation changed download'}
  $change=@(Get-ChildItem -LiteralPath (Join-Path $Downloads $label) -Filter 'changes_*.xlsx');$book=$excel.Workbooks.Open($change[0].FullName,0,$true)
  try{$sheet=$book.Worksheets.Item('변경 셀');if($sheet.UsedRange.Rows.Count -ne $case.patch_count+1){throw 'Change report count mismatch'};$results+=@{case=($label+'-changes');status='PASS';native_open=$true;patch_count=$case.patch_count};[void][Runtime.InteropServices.Marshal]::ReleaseComObject($sheet)}finally{$book.Close($false);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($book)}
 }
 foreach($label in $(if($Mode -eq 'comparison'){@('comparison','comparison-capacity')}else{@()})){
  $file=@(Get-ChildItem -LiteralPath (Join-Path $Downloads $label) -Filter 'comparison_report_*.xlsx');if($file.Count -ne 1){throw 'Missing actual comparison report'};$book=$excel.Workbooks.Open($file[0].FullName,0,$true)
  try{
   $all=@();foreach($name in @('금액차이','한쪽자료','중복모호','자료오류','일치')){$sheet=$book.Worksheets.Item($name);$data=$sheet.UsedRange.Value2;for($i=2;$i -le $data.GetLength(0);$i++){if($data[$i,4]){$all+=@{id=$data[$i,4];side=$data[$i,3];row=$data[$i,6];status=$data[$i,2];key=$data[$i,7];delta=$data[$i,11];raw=$data[$i,8]}}};[void][Runtime.InteropServices.Marshal]::ReleaseComObject($sheet)}
   $required=if($label -eq 'comparison'){888}else{2000};if($all.Count -ne $required -or @($all|ForEach-Object {$_.id}|Select-Object -Unique).Count -ne $required){throw 'Native report source row preservation differs'}
   if($label -eq 'comparison'){
    foreach($side in @('A','B')){foreach($row in $oracle.comparison.physical_rows.PSObject.Properties[$side].Value){$found=@($all|Where-Object {$_.side -ceq $side -and $_.row -eq [string]$row.physical_row});if($found.Count -ne 1 -or $found[0].status -cne $row.status){throw 'Native classification differs'}}}
    $big=@($all|Where-Object {$_.key -like '*BIG*'});if($big.Count -ne 2 -or @($big|Where-Object {$_.delta -cne '1'}).Count -ne 0){throw 'Native exact big integer delta differs'}
   }
   if($label -eq 'comparison-capacity'){foreach($row in $all){if($row.status -cne 'MATCHED' -or $row.raw -ne [string](([int]$row.row-1)*7)){throw 'Native capacity classification or amount differs'}}}
   $sheet=$book.Worksheets.Item('요약');foreach($side in @('A','B')){$cell=if($side -eq 'A'){'C12'}else{'D12'};$expected=if($label -eq 'comparison'){$oracle.comparison.controls.PSObject.Properties[$side].Value.known_amount}else{$oracle.capacity.known_amount};Assert-Value $sheet.Range($cell).Value2 $expected ('comparison known total '+$side)};$sheet.PageSetup.PrintArea='A1:D18';$sheet.PageSetup.Orientation=2;$sheet.PageSetup.Zoom=$false;$sheet.PageSetup.FitToPagesWide=1;$sheet.PageSetup.FitToPagesTall=1;$sheet.ExportAsFixedFormat(0,(Join-Path $pdfDir ($label+'.pdf')));[void][Runtime.InteropServices.Marshal]::ReleaseComObject($sheet)
   $results+=@{case=$label;status='PASS';native_open=$true;all_source_rows=$required;all_classes_checked=$true;known_totals_checked=$true;exact_big_delta=($label -eq 'comparison')}
  }finally{$book.Close($false);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($book)}
 }
 @{status='PASS';kind='ACTUAL_BETA_DOWNLOADS_REOPENED_IN_INSTALLED_EXCEL';excel_version=$excel.Version;excel_build=$excel.Build;results=$results;official_pg_verified=$false}|ConvertTo-Json -Depth 10|Set-Content -LiteralPath (Join-Path $Out ('download-excel-'+$Mode+'.json')) -Encoding UTF8
 Write-Output ('Native downloaded Excel PASS: '+$results.Count+' workbooks')
}finally{if($excel){$excel.Quit();[void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel)};[GC]::Collect();[GC]::WaitForPendingFinalizers()}
