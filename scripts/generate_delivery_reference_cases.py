from pathlib import Path
import json,importlib.util,hashlib
R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('fixture',R/'scripts/generate_delivery_fixtures.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
# Hand-authored arithmetic oracle, fixed before either evaluator runs.
cases=[]
def add(name,values,formulas,expected):cases.append({'id':name,'values':values,'formulas':formulas,'expected':expected})
def number(n):return {'type':'number','value':n}
def text(t):return {'type':'text','value':t}
add('sum_typed_text',{'A1':'12000','A2':'3,500','A3':7}, {'B1':'=SUM(A1:A3)'},{'B1':number(7)})
add('sum_numeric',{'A1':12000,'A2':3500,'A3':7}, {'B1':'=SUM(A1:A3)'},{'B1':number(15507)})
add('round_amount',{'A1':2,'B1':1500,'C1':.1}, {'D1':'=ROUND(A1*B1*(1-C1),0)'},{'D1':number(2700)})
add('mixed_absolute',{'A1':3,'B1':2000,'C1':0}, {'D1':'=ROUND($A1*B$1*(1-$C$1),0)'},{'D1':number(6000)})
add('round_positive_tie',{'A1':2.5}, {'B1':'=ROUND(A1,0)'},{'B1':number(3)})
add('round_negative_tie',{'A1':-2.5}, {'B1':'=ROUND(A1,0)'},{'B1':number(-3)})
add('if_and_true',{'A1':2,'B1':1500,'C1':.1}, {'D1':'=IF(AND(ISNUMBER(A1),ISNUMBER(B1),ISNUMBER(C1)),ROUND(A1*B1*(1-C1),0),0)'},{'D1':number(2700)})
add('if_and_text',{'A1':'2','B1':1500,'C1':.1}, {'D1':'=IF(AND(ISNUMBER(A1),ISNUMBER(B1),ISNUMBER(C1)),ROUND(A1*B1*(1-C1),0),0)'},{'D1':number(0)})
add('if_and_missing',{'B1':1500,'C1':.1}, {'D1':'=IF(AND(ISNUMBER(A1),ISNUMBER(B1),ISNUMBER(C1)),ROUND(A1*B1*(1-C1),0),0)'},{'D1':number(0)})
add('if_or_zero',{'A1':0,'B1':1500}, {'D1':'=IF(OR(A1=0,A1=""),0,ROUND(A1*B1,0))'},{'D1':number(0)})
add('if_or_empty',{'A1':'','B1':1500}, {'D1':'=IF(OR(A1=0,A1=""),0,ROUND(A1*B1,0))'},{'D1':number(0)})
add('if_or_nonzero',{'A1':2,'B1':1500}, {'D1':'=IF(OR(A1=0,A1=""),0,ROUND(A1*B1,0))'},{'D1':number(3000)})
add('iferror_semantic_div0',{'A1':2,'B1':0}, {'D1':'=IFERROR(A1/B1,0)'},{'D1':number(0)})
add('division_error',{'A1':2,'B1':0}, {'D1':'=A1/B1'},{'D1':{'type':'error','value':'#DIV/0!'}})
add('division_text_error',{'A1':'not-number','B1':2}, {'D1':'=A1/B1'},{'D1':{'type':'error','value':'#VALUE!'}})
add('division_normal',{'A1':9,'B1':2}, {'D1':'=IFERROR(A1/B1,0)'},{'D1':number(4.5)})
add('arithmetic',{'A1':7,'B1':3}, {'C1':'=A1+B1','D1':'=A1-B1','E1':'=A1*B1','F1':'=A1/B1'},{'C1':number(10),'D1':number(4),'E1':number(21),'F1':number(7/3)})
add('round_product',{'A1':2.5,'B1':3}, {'C1':'=ROUND(A1*B1,0)'},{'C1':number(8)})
add('empty_and_reference',{'A1':'abc'}, {'B1':'=""','C1':'=A1','D1':'=A2'},{'B1':text(''),'C1':text('abc'),'D1':number(0)})
add('boolean_sum',{'A1':True,'A2':2}, {'B1':'=SUM(A1:A3)'},{'B1':number(2)})
out=R/'samples/delivery-v3_2/reference-cases.json'
assert not out.exists()
out.write_text(json.dumps({'kind':'INDEPENDENT_HAND_CALCULATED_POLICY_ORACLE_V1','cases':cases},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Fixed independent oracle:',len(cases),'cases;',sum(len(c['expected']) for c in cases),'typed results')
