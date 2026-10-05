$tokens=$null
$errors=$null
[System.Management.Automation.Language.Parser]::ParseFile('scripts/verify_delivery_output_excel.ps1',[ref]$tokens,[ref]$errors) | Out-Null
if($errors.Count){$errors | ForEach-Object { $_.Message }; exit 1}
'ps parser passed'
