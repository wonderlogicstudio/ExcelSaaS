param([ValidateSet('d08','d08-comparison')][string]$Stage='d08')
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$dir=Join-Path $root ('artifacts/verification/'+$Stage)
$evidence=Get-Content -LiteralPath (Join-Path $dir 'browser.json') -Raw -Encoding UTF8|ConvertFrom-Json
$oracle=Get-Content -LiteralPath (Join-Path $root 'samples/delivery-v3_2/holdout-v2-expected.json') -Raw -Encoding UTF8|ConvertFrom-Json
$excel=$null;$results=@();$styleMap=@();$pdfs=@()
function Get-CellStyle($cell){
 return @([string]$cell.NumberFormat,[bool]$cell.Font.Bold,[string]$cell.Font.Color,[string]$cell.Interior.Color,[double]$cell.ColumnWidth) -join '|'
}
try{
 $excel=New-Object -ComObject Excel.Application
 $excel.Visible=$false;$excel.DisplayAlerts=$false;$excel.AutomationSecurity=3;$excel.AskToUpdateLinks=$false;$excel.EnableEvents=$false
 $source=Join-Path $root 'samples/delivery-v3_2/delivery-holdout-v2.xlsx'
 $sourceHash=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLower()
 if($sourceHash -cne $oracle.source_hashes.'delivery-holdout-v2.xlsx'){throw 'Frozen original hash differs'}
 $book=$excel.Workbooks.Open($source,0,$true)
 try{
  $sheet=$book.Worksheets.Item('검증');$excel.CalculateFullRebuild()
  foreach($item in $oracle.repair.before.PSObject.Properties){if([double]$sheet.Range($item.Name).Value2 -ne [double]$item.Value){throw ('Independent Excel original differs at '+$item.Name)}}
  $styleMap=@{}
  foreach($address in $oracle.repair.RP01.style_preserved){$cell=$sheet.Range($address);$styleMap[$address]=Get-CellStyle $cell;[void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell)}
  if($sheet.Range('A2').Value2 -cne '00042' -or -not $sheet.Range('A2').Font.Bold){throw 'Original identifier style missing'}
  [void][Runtime.InteropServices.Marshal]::ReleaseComObject($sheet)
 }finally{$book.Close($false);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($book)}
 foreach($case in $evidence.rows){
  foreach($file in $case.files.PSObject.Properties){
   if(-not $file.Name.EndsWith('XLSX')){continue}
   $path=$file.Value.path
   if(-not [IO.Path]::GetFullPath($path).StartsWith($dir+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Synthetic output root mismatch'}
   $hash=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLower()
   if($hash -cne $file.Value.sha256){throw 'Browser receipt differs'}
   $book=$excel.Workbooks.Open($path,0,$true)
   try{
    if($file.Name -eq 'REPAIRED_XLSX'){
     $sheet=$book.Worksheets.Item('검증');$excel.CalculateFullRebuild()
     foreach($item in $case.expected.PSObject.Properties){$cell=$sheet.Range($item.Name);if($cell.Value2 -is [string] -or [double]$cell.Value2 -ne [double]$item.Value){throw ('Actual repaired Excel expected differs at '+$item.Name)};[void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell)}
     if($sheet.Range('A2').Value2 -cne '00042' -or $sheet.Range('B12').Value2 -cne '00123'){throw 'Unapproved identifier changed'}
     foreach($address in $oracle.repair.RP01.style_preserved){$cell=$sheet.Range($address);if((Get-CellStyle $cell) -cne $styleMap[$address]){throw ('Style changed at '+$address)};[void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell)}
     if($case.profile -eq 'RP02'){
      if($sheet.Range('F3').Formula -cne $oracle.repair.RP02.formula){throw 'Approved formula differs'}
      foreach($item in $oracle.repair.RP02.unchanged_text.PSObject.Properties){if($sheet.Range($item.Name).Value2 -cne $item.Value){throw 'Unapproved text changed'}}
     }elseif($null -ne $sheet.Range('F3').Value2){throw 'Unapproved blank changed'}
     if($case.width -eq 1440){
      $sheet.PageSetup.PrintArea='$A$1:$J$12';$sheet.PageSetup.Orientation=2;$sheet.PageSetup.Zoom=$false;$sheet.PageSetup.FitToPagesWide=1;$sheet.PageSetup.FitToPagesTall=1
      $pdf=Join-Path $dir ($case.profile+'-holdout-excel.pdf');$sheet.ExportAsFixedFormat(0,$pdf);$pdfs+=$pdf
     }
     [void][Runtime.InteropServices.Marshal]::ReleaseComObject($sheet)
    }elseif($file.Name -eq 'CHANGES_XLSX'){
     $sheet=$book.Worksheets.Item('변경 셀');$rowCount=if($case.profile -eq 'RP01'){3}else{2}
     if($sheet.UsedRange.Rows.Count -ne $rowCount){throw 'Exact patch count differs'}
     foreach($cell in $sheet.UsedRange.Cells){if($cell.HasFormula){throw 'Executable report formula'};[void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell)}
     [void][Runtime.InteropServices.Marshal]::ReleaseComObject($sheet)
    }else{
     if($book.Worksheets.Count -ne 8){throw 'Comparison sheets missing'}
     $sheet=$book.Worksheets.Item('요약');if([string]$sheet.Range('C12').Value2 -cne '250' -or [string]$sheet.Range('D12').Value2 -cne '190'){throw 'Comparison known amounts differ'}
     if($case.width -eq 1440){$pdf=Join-Path $dir 'comparison-holdout-excel.pdf';$sheet.ExportAsFixedFormat(0,$pdf);$pdfs+=$pdf}
     [void][Runtime.InteropServices.Marshal]::ReleaseComObject($sheet)
     $count=0
     foreach($name in @('금액차이','한쪽자료','중복모호','자료오류','일치')){
      $sheet=$book.Worksheets.Item($name)
      for($row=2;$row -le $sheet.UsedRange.Rows.Count;$row++){if($sheet.Cells.Item($row,4).Value2){$count++;if($name -eq '금액차이' -and [string]$sheet.Cells.Item($row,11).Value2 -cne '20'){throw 'Exact delta differs'}}}
      foreach($cell in $sheet.UsedRange.Cells){if($cell.HasFormula){throw 'Comparison executable formula'};[void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell)}
      [void][Runtime.InteropServices.Marshal]::ReleaseComObject($sheet)
     }
     if($count -ne 12){throw 'Comparison source row conservation differs'}
    }
   }finally{$book.Close($false);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($book)}
   if((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLower() -cne $hash){throw 'Read-only Excel changed output'}
   $results+=@{width=$case.width;profile=$case.profile;kind=$file.Name;sha256=$hash;expected_match=$true;unchanged=$true;style_preserved=($file.Name -eq 'REPAIRED_XLSX')}
  }
 }
 if((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLower() -cne $sourceHash){throw 'Original changed'}
 @{status='PASS';kind='D08_ACTUAL_HOLDOUT_DOWNLOADS_IN_INSTALLED_EXCEL';official_pg_verified=$false;excel_version=$excel.Version;excel_build=$excel.Build;source_hash=$sourceHash;original_expected_match=$true;style_reference=$styleMap;results=$results;pdfs=$pdfs}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $dir 'excel-reopen.json') -Encoding UTF8
 Write-Output ('Actual installed Excel: '+$results.Count+' downloaded workbooks; original/reference/style/value/hash checks PASS. PG not verified.')
}finally{if($excel){$excel.Quit();[void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel)};[GC]::Collect();[GC]::WaitForPendingFinalizers()}
