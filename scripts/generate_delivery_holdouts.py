"""New independent synthetic values and fixed hand-calculated expectations, before execution."""
from pathlib import Path
from io import BytesIO
import hashlib,json
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED
from xml.etree import ElementTree as ET
from generate_delivery_fixtures import workbook_bytes

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'samples/delivery-v3_2';NS='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
def make(no_change=False):
    with ZipFile(BytesIO(workbook_bytes())) as z:parts={n:z.read(n) for n in z.namelist()}
    tree=ET.fromstring(parts['xl/worksheets/sheet1.xml'])
    values={'A2':'00042','B2':'-1,250','B3':'7,200','C2':3,'D2':1800,'E2':.15,'C3':4,'D3':875,'E3':.2}
    if no_change:values.update(B2=-1250,B3=7200)
    for node in tree.iter(NS+'c'):
        cell=node.get('r')
        if cell in values:
            for child in list(node):node.remove(child)
            value=values[cell]
            if isinstance(value,str):
                node.set('t','inlineStr');ET.SubElement(ET.SubElement(node,NS+'is'),NS+'t').text=value
            else:
                node.attrib.pop('t',None);ET.SubElement(node,NS+'v').text=str(value)
        if cell in {'B2','B3','F2','F4','F12'}:node.set('s','1')
        if cell=='A2':node.set('s','2')
    row3=next(r for r in tree.iter(NS+'row') if r.get('r')=='3')
    blank=ET.Element(NS+'c',{'r':'F3','s':'1'});row3.insert(4,blank)
    cols=ET.Element(NS+'cols');ET.SubElement(cols,NS+'col',{'min':'1','max':'10','width':'15','customWidth':'1'});tree.insert(0,cols)
    parts['xl/worksheets/sheet1.xml']=ET.tostring(tree,encoding='utf-8',xml_declaration=True)
    styles='''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><color rgb="FF1122DD"/><name val="Calibri"/></font></fonts><fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FFFFEEDD"/><bgColor indexed="64"/></patternFill></fill></fills><borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="3"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="3" fontId="0" fillId="2" borderId="0" xfId="0" applyNumberFormat="1" applyFill="1"/><xf numFmtId="49" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1" applyNumberFormat="1"/></cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>'''
    parts['xl/styles.xml']=styles.encode()
    parts['[Content_Types].xml']=parts['[Content_Types].xml'].replace(b'</Types>',b'<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/></Types>')
    parts['xl/_rels/workbook.xml.rels']=parts['xl/_rels/workbook.xml.rels'].replace(b'</Relationships>',b'<Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>')
    output=BytesIO()
    with ZipFile(output,'w') as z:
        for name,data in sorted(parts.items()):
            entry=ZipInfo(name,(2026,9,13,0,0,0));entry.compress_type=ZIP_DEFLATED;z.writestr(entry,data)
    return output.getvalue()

expected={'kind':'D08_NEW_SYNTHETIC_HOLDOUT_HAND_CALCULATED_BEFORE_PRODUCT_RUN','existing_oracles_unchanged':True,
 'repair':{'file':'delivery-holdout.xlsx','unchanged_id_A2':'00042','before':{'F2':4590,'F12':14090,'H2':0},
 'RP01':{'targets':['B2','B3'],'expected':{'B2':-1250,'B3':7200,'H2':5950,'F2':4590,'F12':14090},'style_preserved':['A2','B2','B3','F2','F3','F4','F12']},
 'RP02':{'anchor':'F2','target':'F3','formula':'=ROUND(C3*D3*(1-E3),0)','expected':{'F2':4590,'F3':2800,'F12':16890,'H2':0},'unchanged_text':{'B2':'-1,250','B3':'7,200'}}},
 'normal_exception':{'file':'delivery-holdout-no-change.xlsx','rp01_eligible_count':0,'cannot_order':True},
 'comparison':{'A_rows':7,'B_rows':5,'groups':7,'counts':{'MATCHED':1,'AMOUNT_DIFF':1,'ONLY_A':1,'ONLY_B':1,'AMBIGUOUS':1,'INPUT_ERROR':2},'known_A':'250','known_B':'190','unknown_A':1,'unknown_B':0,'delta_key':'DIF','delta':'20','duplicate_key':'DUP','duplicate_rows':3,'error_key':'ERR','error_rows':2}}
if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    files={'delivery-holdout.xlsx':make(),'delivery-holdout-no-change.xlsx':make(True),
           'comparison-holdout-A.csv':'ID,금액\r\n000A,0\r\nDIF,200\r\nLEFT,-25\r\n,50\r\nDUP,10\r\nDUP,15\r\nERR,bad\r\n'.encode('utf-8'),
           'comparison-holdout-B.csv':'ID,금액\r\n000A,0\r\nDIF,180\r\nRIGHT,-40\r\nDUP,30\r\nERR,20\r\n'.encode('utf-8')}
    for name,data in files.items():
        path=OUT/name
        if path.exists() and path.read_bytes()!=data:raise RuntimeError('Existing holdout differs; never replace a frozen oracle')
        path.write_bytes(data)
    expected['source_hashes']={n:hashlib.sha256(b).hexdigest() for n,b in files.items()}
    text=json.dumps(expected,ensure_ascii=False,indent=2)+'\n';path=OUT/'holdout-expected.json'
    if path.exists() and path.read_text(encoding='utf-8')!=text:raise RuntimeError('Frozen expected values differ')
    path.write_text(text,encoding='utf-8',newline='\n')
    print('New holdout inputs and manually calculated expected values frozen; no engine output used as oracle.')
