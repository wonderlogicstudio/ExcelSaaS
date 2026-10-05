$ErrorActionPreference='Stop'
$repo='C:\Users\JinwonLee\project\ExcelSaaS'
$scratch='C:\Users\JinwonLee\project\DigitalTwin\.tmp\monthly-calc-excel04'
$oraclePath=Join-Path $repo 'artifacts\synthetic_validation\monthly-repair-spec01\acceptance-oracle.json'
$oracle=Get-Content -LiteralPath $oraclePath -Raw -Encoding UTF8 | ConvertFrom-Json
if($oracle.case.sheet -ne 'Budget'){throw 'unexpected oracle sheet'}
if($oracle.case.cell -ne 'N18'){throw 'unexpected oracle cell'}
if($oracle.case.after_formula -ne "='M10'!B16-'M10'!B15"){throw 'unexpected oracle formula'}
if([double]$oracle.case.after_value.value -ne -5){throw 'unexpected oracle expected value'}
if($oracle.case.derivation -ne 'M10!B16=1001 minus M10!B15=1006 = -5'){throw 'unexpected oracle derivation'}
$excel=$null
try {
  $excel=New-Object -ComObject Excel.Application
  $excel.Visible=$false
  $excel.DisplayAlerts=$false
  $excel.AutomationSecurity=3
  $excel.AskToUpdateLinks=$false
  $excel.EnableEvents=$false
  $version=$excel.Version
  $build=$excel.Build
  $book=$excel.Workbooks.Add(-4167)
  try {
    $budget=$book.Worksheets.Item(1)
    $budget.Name='Budget'
    $m10=$book.Worksheets.Add()
    $m10.Name='M10'
    $m10.Range('B16').Value2=[double]1001
    $m10.Range('B15').Value2=[double]1006
    $budget.Range('N18').Formula=$oracle.case.after_formula
    $excel.CalculateFullRebuild()
    $cell=$budget.Range('N18')
    $value=$cell.Value2
    $isError=$excel.WorksheetFunction.IsError($cell)
    if($isError){$kind='error';$actual=$cell.Text}
    elseif($value -is [string]){$kind='text';$actual=$value}
    elseif($null -eq $value){$kind='blank';$actual=$null}
    else {$kind='number';$actual=[double]$value}
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell)
    if($kind -ne 'number' -or [double]$actual -ne -5){throw "unexpected Excel result $kind $actual"}
    $evidence=[ordered]@{
      status='PASS'
      kind='REDUCED_MONTHLY_INTERNAL_EXCEL_COM_CONTROL'
      excel_version=$version
      excel_build=$build
      source='monthly-repair-spec01 acceptance oracle case.after_formula/after_value/derivation'
      formula=$oracle.case.after_formula
      operands=[ordered]@{'M10!B16'=1001;'M10!B15'=1006}
      expected=$oracle.case.after_value
      actual=[ordered]@{type=$kind;value=$actual}
      note='Reduced two-sheet internal calculation control; not a supported full 13-sheet fixture run.'
    }
    $out=Join-Path $scratch 'monthly-excel-result.json'
    $evidence | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $out -Encoding UTF8
    Write-Output "Monthly Excel reduced control: Budget!N18=$actual; saved $out"
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($m10)
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($budget)
  } finally {
    if($book){$book.Close($false);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($book)}
  }
} finally {
  if($excel){$excel.Quit();[void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel)}
  [GC]::Collect();[GC]::WaitForPendingFinalizers()
}

