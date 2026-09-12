"""New deterministic synthetic product inputs; expectations are hand-calculated.

These are not package example outputs and do not assert Excel-reference evidence.
"""
from __future__ import annotations

import json
from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]


def workbook_bytes(*, unsupported=False):
    from io import BytesIO
    cells = {'A1': 'ID', 'B1': '금액', 'C1': '수량', 'D1': '단가', 'E1': '할인율', 'F1': '계산금액',
             'A2': '00123', 'B2': '12000', 'C2': 2, 'D2': 1500, 'E2': .1,
             'F2': '=ROUND(C2*D2*(1-E2),0)', 'H2': '=SUM(B2:B3)',
             'A3': 'T-002', 'B3': '3,500', 'C3': 3, 'D3': 2000, 'E3': 0,
             'G3': '', 'H3': '=""', 'I3': 9, 'J3': ' ',
             'A4': '00004', 'B4': '비용12원', 'C4': 1, 'D4': 10000, 'E4': .05,
             'F4': '=ROUND(C4*D4*(1-E4),0)', 'B5': '1.5', 'B6': '1234567890123456',
             'B7': ' 1200', 'B8': '-0', 'B9': '12%', 'B10': '2026-09-13', 'B12': '00123',
             'F12': '=SUM(F2:F4)'}
    if unsupported:
        cells['F2'] = '=IFERROR(UNKNOWN(C2),0)'
    rows = {}
    for address, value in cells.items():
        row = int(''.join(c for c in address if c.isdigit()))
        if isinstance(value, str):
            content = f'<f>{escape(value[1:])}</f>' if value.startswith('=') else f'<is><t xml:space="preserve">{escape(value)}</t></is>'
            kind = '' if value.startswith('=') else ' t="inlineStr"'
        else:
            kind = ''; content = f'<v>{value}</v>'
        rows.setdefault(row, []).append(f'<c r="{address}"{kind}>{content}</c>')
    sheet = '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>' + ''.join(f'<row r="{row}">{"".join(values)}</row>' for row, values in sorted(rows.items())) + '</sheetData></worksheet>'
    parts = {
        '[Content_Types].xml': '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>',
        '_rels/.rels': '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>',
        'xl/workbook.xml': '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="검증" sheetId="1" r:id="rId1"/></sheets><calcPr calcId="191029" fullCalcOnLoad="1"/></workbook>',
        'xl/_rels/workbook.xml.rels': '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>',
        'xl/worksheets/sheet1.xml': sheet,
    }
    stream = BytesIO()
    with ZipFile(stream, 'w') as archive:
        for name, text in sorted(parts.items()):
            entry = ZipInfo(name, (2026, 9, 13, 0, 0, 0)); entry.compress_type = ZIP_DEFLATED
            archive.writestr(entry, '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'+text)
    return stream.getvalue()


if __name__ == '__main__':
    directory = ROOT / 'samples/delivery-v3_2'
    directory.mkdir(parents=True, exist_ok=True)
    (directory/'delivery-rp01-rp02.xlsx').write_bytes(workbook_bytes())
    (directory/'delivery-unsupported.xlsx').write_bytes(workbook_bytes(unsupported=True))
    expected = {'kind':'NEW_SYNTHETIC_PRODUCT_INPUT_HAND_CALCULATED_EXPECTATIONS','excel_reference_verified':False,
                'rp01':{'targets':['B2','B3'],'eligible_count':2,'before_H2':0,'after_H2':15500,'type_values':{'B2':12000,'B3':3500},'unchanged_id_A2':'00123'},
                'rp02':{'anchor':'F2','target':'F3','formula_after':'=ROUND(C3*D3*(1-E3),0)','after_F3':6000,'before_F12':12200,'after_F12':18200},
                'rejected_rp01':['A2','B4','B5','B6','B7','B8','B9','B10','B11','B12'],
                'rejected_rp02':['G3','H3','I3','J3'],'unsupported':'UNSUPPORTED_FORMULA'}
    (directory/'expected.json').write_text(json.dumps(expected,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Created two new synthetic inputs and independent expected values')
