# Synthetic sample workbook

Generate a workbook containing intentionally risky formulas and workbook structures:

```powershell
cd apps/api
.\.venv\Scripts\Activate.ps1
python ..\..\scripts\generate_sample_workbook.py
```

The generated `demo-risky-workbook.xlsx` contains only synthetic data and is ignored by Git so real upload files are not committed accidentally.
