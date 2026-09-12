$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$inputPath=Join-Path $root 'samples/delivery-v3_2/reference-cases.json'
$outputPath=Join-Path $root 'artifacts/verification/d03/excel-reference.json'
$referenceCases=Get-Content -LiteralPath $inputPath -Raw -Encoding UTF8 | ConvertFrom-Json
$excel=$null
$results=@()
try {
  # Own a new hidden instance. Never attach to or edit a user's open workbook.
  $excel=New-Object -ComObject Excel.Application
  $excel.Visible=$false
  $excel.DisplayAlerts=$false
  $excel.AutomationSecurity=3
  $excel.AskToUpdateLinks=$false
  $excel.EnableEvents=$false
  $version=$excel.Version
  $build=$excel.Build
  foreach($case in $referenceCases.cases){
    $book=$excel.Workbooks.Add(-4167)
    try {
      $sheet=$book.Worksheets.Item(1)
      foreach($property in $case.values.PSObject.Properties){
        $cell=$sheet.Range($property.Name)
        if($property.Value -is [string]){$cell.NumberFormat='@';$cell.Value2=$property.Value}
        elseif($property.Value -is [bool]){$cell.Value2=[bool]$property.Value}
        else {$cell.Value2=[double]$property.Value}
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell)
      }
      foreach($property in $case.formulas.PSObject.Properties){
        $cell=$sheet.Range($property.Name);$cell.Formula=$property.Value
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell)
      }
      $excel.CalculateFullRebuild()
      $values=@{}
      foreach($property in $case.expected.PSObject.Properties){
        $cell=$sheet.Range($property.Name)
        $v=$cell.Value2
        $isError=$excel.WorksheetFunction.IsError($cell)
        if($isError){$kind='error';$v=$cell.Text}
        elseif($v -is [string]){$kind='text'}
        elseif($v -is [bool]){$kind='boolean'}
        elseif($null -eq $v){$kind='blank'}
        else {$kind='number';$v=[double]$v}
        $values[$property.Name]=@{type=$kind;value=$v}
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell)
      }
      $results+=@{id=$case.id;values=$values}
      [void][Runtime.InteropServices.Marshal]::ReleaseComObject($sheet)
    } finally {$book.Close($false);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($book)}
  }
  $dir=Split-Path -Parent $outputPath
  [void](New-Item -ItemType Directory -Path $dir -Force)
  @{kind='ACTUAL_INSTALLED_EXCEL_REFERENCE';version=$version;build=$build;source_sha256=(Get-FileHash -LiteralPath $inputPath -Algorithm SHA256).Hash.ToLower();results=$results} | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $outputPath -Encoding UTF8
  Write-Output "Excel reference: $($results.Count) synthetic cases; saved without modifying source files."
} finally {
  if($excel){$excel.Quit();[void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel)}
  [GC]::Collect();[GC]::WaitForPendingFinalizers()
}
