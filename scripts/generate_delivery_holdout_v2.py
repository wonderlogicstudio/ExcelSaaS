"""Preserve v1 evidence; fix only the synthetic input's invalid OOXML cell order."""
from pathlib import Path
from io import BytesIO
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
from xml.etree import ElementTree as ET
import copy
import hashlib
import json
import re
from generate_delivery_holdouts import make

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'samples/delivery-v3_2'
NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'


def ordered(raw):
    with ZipFile(BytesIO(raw)) as z:
        parts = {n: z.read(n) for n in z.namelist()}
    tree = ET.fromstring(parts['xl/worksheets/sheet1.xml'])
    for row in tree.findall(NS + 'sheetData/' + NS + 'row'):
        cells = list(row)
        for cell in cells:
            row.remove(cell)
        for cell in sorted(cells, key=lambda c: (len(re.sub(r'\d', '', c.get('r'))), re.sub(r'\d', '', c.get('r')))):
            row.append(cell)
    parts['xl/worksheets/sheet1.xml'] = ET.tostring(tree, encoding='utf-8', xml_declaration=True)
    stream = BytesIO()
    with ZipFile(stream, 'w') as z:
        for name, data in sorted(parts.items()):
            info = ZipInfo(name, (2026, 9, 13, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            z.writestr(info, data)
    return stream.getvalue()


if __name__ == '__main__':
    oracle = copy.deepcopy(json.loads((OUT / 'holdout-expected.json').read_text(encoding='utf-8')))
    oracle['kind'] = 'D08_ORDERED_INPUT_V2_SAME_PREDECLARED_MANUAL_EXPECTED_VALUES'
    oracle['supersedes_positive_input'] = 'holdout-expected.json (invalid cell order retained as negative)'
    oracle['repair']['file'] = 'delivery-holdout-v2.xlsx'
    oracle['normal_exception']['file'] = 'delivery-holdout-no-change-v2.xlsx'
    oracle['source_hashes'] = {n: h for n, h in oracle['source_hashes'].items() if n.endswith('.csv')}
    for name, raw in [('delivery-holdout-v2.xlsx', make()), ('delivery-holdout-no-change-v2.xlsx', make(True))]:
        data = ordered(raw)
        path = OUT / name
        if path.exists() and path.read_bytes() != data:
            raise RuntimeError('Never overwrite a frozen v2 input')
        path.write_bytes(data)
        oracle['source_hashes'][name] = hashlib.sha256(data).hexdigest()
    path = OUT / 'holdout-v2-expected.json'
    text = json.dumps(oracle, ensure_ascii=False, indent=2) + '\n'
    if path.exists() and path.read_text(encoding='utf-8') != text:
        raise RuntimeError('Never overwrite a frozen v2 oracle')
    path.write_text(text, encoding='utf-8', newline='\n')
    print('V2 ordered synthetic inputs generated; all predeclared expected values unchanged; v1 retained.')
