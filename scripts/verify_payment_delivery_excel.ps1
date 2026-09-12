param([ValidateSet('d06','d07','d07-operations')][string]$Stage='d06')
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$dir=Join-Path $root ('artifacts/verification/'+$Stage)
$evidence=Get-Content -LiteralPath (Join-Path $dir 'browser.json') -Raw -Encoding UTF8|ConvertFrom-Json
$excel=$null;$results=@()
try{
 $excel=New-Object -ComObject Excel.Application
 $excel.Visible=$false;$excel.DisplayAlerts=$false;$excel.AutomationSecurity=3;$excel.AskToUpdateLinks=$false;$excel.EnableEvents=$false
 foreach($case in $evidence.rows){
  if($case.retry_file){$case.files|Add-Member -NotePropertyName RETRY_REPAIRED_XLSX -NotePropertyValue $case.retry_file}
  foreach($file in $case.files.PSObject.Properties){
   if(-not $file.Name.EndsWith('XLSX')){continue}
   $path=$file.Value.path
   if(-not [IO.Path]::GetFullPath($path).StartsWith($dir+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Synthetic root mismatch'}
   $hash=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLower()
   if($hash -ne $file.Value.sha256){throw 'Browser receipt mismatch'}
   $book=$excel.Workbooks.Open($path,0,$true)
   try{
    if($file.Name -like '*REPAIRED_XLSX'){
     $sheet=$book.Worksheets.Item('검증');$excel.CalculateFullRebuild()
     foreach($value in $case.expected.PSObject.Properties){
      $cell=$sheet.Range($value.Name)
      if($cell.Value2 -is [string] -or [double]$cell.Value2 -ne [double]$value.Value){throw 'Actual repaired Excel expected value differs'}
      [void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell)
     }
     if($sheet.Range('A2').Value2 -cne '00123'){throw 'Identifier changed'}
     if($case.profile -eq 'RP01' -and $Stage -ne 'd07-operations' -and $sheet.Range('B3').Value2 -cne '3,500'){throw 'Unapproved B3 changed'}
     if($case.profile -eq 'RP02' -and $sheet.Range('F3').Formula -cne '=ROUND(C3*D3*(1-E3),0)'){throw 'Approved formula differs'}
     [void][Runtime.InteropServices.Marshal]::ReleaseComObject($sheet)
    }elseif($file.Name -eq 'CHANGES_XLSX'){
     $sheet=$book.Worksheets.Item('변경 셀')
     $expectedRows=if($Stage -eq 'd07-operations'){3}else{2};if($sheet.UsedRange.Rows.Count -ne $expectedRows){throw 'Exact approved patch count differs'}
     foreach($cell in $sheet.UsedRange.Cells){if($cell.HasFormula){throw 'Executable report formula'};[void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell)}
     [void][Runtime.InteropServices.Marshal]::ReleaseComObject($sheet)
    }else{
     $sheet=$book.Worksheets.Item('요약')
     if([string]$sheet.Range('C12').Value2 -cne $case.expected.A -or [string]$sheet.Range('D12').Value2 -cne $case.expected.B){throw 'Comparison expected totals differ'}
     [void][Runtime.InteropServices.Marshal]::ReleaseComObject($sheet)
     $count=0
     foreach($name in @('금액차이','한쪽자료','중복모호','자료오류','일치')){
      $sheet=$book.Worksheets.Item($name)
      for($row=2;$row -le $sheet.UsedRange.Rows.Count;$row++){if($sheet.Cells.Item($row,4).Value2){$count++}}
      [void][Runtime.InteropServices.Marshal]::ReleaseComObject($sheet)
     }
     if($count -ne $case.expected.source_rows){throw 'Comparison row conservation differs'}
    }
   }finally{$book.Close($false);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($book)}
   if((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLower() -ne $hash){throw 'Read-only Excel changed output'}
   $results+=@{profile=$case.profile;kind=$file.Name;sha256=$hash;expected_match=$true;unchanged=$true}
  }
 }
 @{status='PASS';kind='ACTUAL_PRODUCT_DOWNLOADS_REOPENED_IN_INSTALLED_EXCEL';official_pg_verified=$false;excel_version=$excel.Version;excel_build=$excel.Build;results=$results}|ConvertTo-Json -Depth 10|Set-Content -LiteralPath (Join-Path $dir 'excel-reopen.json') -Encoding UTF8
 Write-Output 'Actual synthetic product XLSX downloads reopened in Excel; exact approved subset and comparison totals PASS. PG not verified.'
}finally{if($excel){$excel.Quit();[void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel)};[GC]::Collect();[GC]::WaitForPendingFinalizers()}
