param([ValidateSet('d05','d07-comparison','d08-comparison')][string]$Stage='d05')
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$dir=Join-Path $root ('artifacts/verification/'+$Stage)
$evidence=Get-Content -LiteralPath (Join-Path $dir 'browser.json') -Raw -Encoding UTF8|ConvertFrom-Json
$excel=$null;$results=@()
try{
 $excel=New-Object -ComObject Excel.Application
 $excel.Visible=$false;$excel.DisplayAlerts=$false;$excel.AutomationSecurity=3;$excel.AskToUpdateLinks=$false;$excel.EnableEvents=$false
 foreach($case in $evidence.rows){
  $path=$case.files.COMPARISON_REPORT_XLSX.path
  if(-not [IO.Path]::GetFullPath($path).StartsWith($dir+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Synthetic artifact root mismatch'}
  $hash=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLower()
  $book=$excel.Workbooks.Open($path,0,$true)
  try{
   if($book.Worksheets.Count -ne 8){throw 'Comparison sheet count mismatch'}
   $count=0;$ids=@{}
   foreach($name in @('금액차이','한쪽자료','중복모호','자료오류','일치')){
    $sheet=$book.Worksheets.Item($name)
    for($row=2;$row -le $sheet.UsedRange.Rows.Count;$row++){
     $id=[string]$sheet.Cells.Item($row,4).Value2
     if(-not $id){continue}
     if($ids.ContainsKey($id)){throw 'Duplicate source row in Excel'}
     $ids[$id]=$true;$count++
     for($col=1;$col -le 12;$col++){if($sheet.Cells.Item($row,$col).HasFormula){throw 'Executable formula in comparison report'}}
     if($case.caseName -eq 'large'){
      if($sheet.Cells.Item($row,10).Value2 -cnotin @('10000000000000001','10000000000000000')){throw 'Exact large integer lost'}
      if($sheet.Cells.Item($row,11).Value2 -cne '1'){throw 'Exact delta differs'}
     }
    }
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($sheet)
   }
   if($count -ne $case.expected.rows){throw 'Source count mismatch'}
   $summary=$book.Worksheets.Item('요약')
   if([string]$summary.Range('C12').Value2 -cne $case.expected.A.Replace(',','').Replace('원','')){throw 'A total mismatch'}
   if([string]$summary.Range('D12').Value2 -cne $case.expected.B.Replace(',','').Replace('원','')){throw 'B total mismatch'}
   if($case.width -eq 1440 -and $case.kind -eq 'csv' -and $case.caseName -eq 'baseline'){
    $summary.ExportAsFixedFormat(0,(Join-Path $dir 'comparison-summary-excel.pdf'))
   }
   [void][Runtime.InteropServices.Marshal]::ReleaseComObject($summary)
  }finally{$book.Close($false);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($book)}
  if((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLower() -ne $hash){throw 'Read-only Excel open changed source'}
  $results+=@{width=$case.width;kind=$case.kind;case=$case.caseName;sha256=$hash;source_rows=$count;expected_matched=$true;no_formulas=$true}
 }
 @{kind='ACTUAL_DOWNLOADED_COMPARISON_REPORTS_REOPENED_IN_INSTALLED_EXCEL';status='PASS';excel_version=$excel.Version;excel_build=$excel.Build;results=$results}|ConvertTo-Json -Depth 10|Set-Content -LiteralPath (Join-Path $dir 'excel-reopen.json') -Encoding UTF8
 Write-Output 'Actual downloaded comparison XLSX: six Excel reopens, exact totals/rows/large integer delta PASS.'
}finally{if($excel){$excel.Quit();[void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel)};[GC]::Collect();[GC]::WaitForPendingFinalizers()}
