"""Create only a synthetic capped-detail workbook for D01 local UI checks."""
from pathlib import Path

from openpyxl import Workbook

root = Path(__file__).resolve().parents[1]
output = root / "artifacts/verification/d01/synthetic-many-findings.xlsx"
output.parent.mkdir(parents=True, exist_ok=True)
workbook = Workbook()
sheet = workbook.active
sheet.title = "=1+1"
for row in range(1, 151):
    sheet.cell(row, 1, "=#REF!")
workbook.save(output)
workbook.close()
print("Generated synthetic D01 capped-detail fixture (no formula execution)")
