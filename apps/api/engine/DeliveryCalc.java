import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.apache.poi.ss.usermodel.*;
import org.apache.poi.ss.formula.*;
import org.apache.poi.ss.formula.ptg.*;
import org.apache.poi.ss.util.CellReference;
import org.apache.poi.xssf.usermodel.*;

/** Bounded typed calculation only. Never reads or writes a customer XLSX. */
public final class DeliveryCalc {
  private static final Set<String> FUNCTIONS=Set.of("SUM","ROUND","IF","IFERROR","AND","OR","ISNUMBER");
  private static final Set<String> TOKENS=Set.of("RefPtg","AreaPtg","IntPtg","NumberPtg","StringPtg","BoolPtg","ErrPtg",
    "AddPtg","SubtractPtg","MultiplyPtg","DividePtg","UnaryMinusPtg","UnaryPlusPtg","ParenthesisPtg",
    "EqualPtg","NotEqualPtg","GreaterThanPtg","LessThanPtg","GreaterEqualPtg","LessEqualPtg","AttrPtg");
  private static String decode(String s){return new String(Base64.getDecoder().decode(s),StandardCharsets.UTF_8);}
  private static String encode(String s){return Base64.getEncoder().encodeToString(s.getBytes(StandardCharsets.UTF_8));}
  public static void main(String[] args) {
    try {run();} catch(OutOfMemoryError e){System.exit(22);} catch(Throwable e){System.exit(20);}
  }
  static void run() throws Exception {
    BufferedReader reader=new BufferedReader(new InputStreamReader(System.in,StandardCharsets.UTF_8));
    if(!"CALC_V1".equals(reader.readLine()))throw new IllegalArgumentException();
    try(XSSFWorkbook workbook=new XSSFWorkbook()){
      String line;int count=0,chars=0;
      while((line=reader.readLine())!=null){
        chars+=line.length();if(++count>10010||chars>3000000)throw new IllegalArgumentException();
        String[] pieces=line.split("\t",-1);if(pieces.length!=4)throw new IllegalArgumentException();
        String name=decode(pieces[0]);Sheet sheet=workbook.getSheet(name);
        if(sheet==null){if(workbook.getNumberOfSheets()>=10)throw new IllegalArgumentException();sheet=workbook.createSheet(name);}
        CellReference ref=new CellReference(pieces[1]);Row row=sheet.getRow(ref.getRow());if(row==null)row=sheet.createRow(ref.getRow());
        if(row.getCell(ref.getCol())!=null)throw new IllegalArgumentException();Cell cell=row.createCell(ref.getCol());
        String value=decode(pieces[3]);
        switch(pieces[2]){
          case "number":double n=Double.parseDouble(value);if(!Double.isFinite(n))throw new IllegalArgumentException();cell.setCellValue(n);break;
          case "text":cell.setCellValue(value);break;
          case "boolean":cell.setCellValue("true".equals(value));break;
          case "blank":cell.setBlank();break;
          case "error":cell.setCellErrorValue(FormulaError.forString(value).getCode());break;
          case "formula":cell.setCellFormula(value.substring(1));break;
          default:throw new IllegalArgumentException();
        }
      }
      XSSFEvaluationWorkbook model=XSSFEvaluationWorkbook.create(workbook);int formulas=0;
      for(Sheet sheet:workbook)for(Row row:sheet)for(Cell cell:row)if(cell.getCellType()==CellType.FORMULA){
        if(++formulas>1100)throw new IllegalArgumentException();
        int allowedLocalIfError=0;
        for(Ptg ptg:FormulaParser.parse(cell.getCellFormula(),model,FormulaType.CELL,workbook.getSheetIndex(sheet))){
          if(ptg instanceof NameXPxg){
            NameXPxg name=(NameXPxg)ptg;
            if(!"IFERROR".equals(name.getNameName())||name.getExternalWorkbookNumber()!=-1||name.getSheetName()!=null)throw new IllegalArgumentException();
            allowedLocalIfError++;
          } else if(ptg instanceof AbstractFunctionPtg){
            String name=((AbstractFunctionPtg)ptg).getName();
            if("#external#".equals(name)&&allowedLocalIfError>0)allowedLocalIfError--;
            else if(!FUNCTIONS.contains(name))throw new IllegalArgumentException();
          }
          else if(!TOKENS.contains(ptg.getClass().getSimpleName()))throw new IllegalArgumentException();
        }
      }
      FormulaEvaluator evaluator=workbook.getCreationHelper().createFormulaEvaluator();
      evaluator.setIgnoreMissingWorkbooks(false);evaluator.clearAllCachedResultValues();
      StringBuilder out=new StringBuilder("CALC_RESULT_V1\n");
      for(Sheet sheet:workbook)for(Row row:sheet)for(Cell cell:row){
        CellValue v=evaluator.evaluate(cell);String type,value;
        if(v==null){type="blank";value="";}
        else switch(v.getCellType()){
          case NUMERIC:type="number";value=Double.toString(v.getNumberValue());if(!Double.isFinite(v.getNumberValue()))throw new IllegalArgumentException();break;
          case STRING:type="text";value=v.getStringValue();break;
          case BOOLEAN:type="boolean";value=Boolean.toString(v.getBooleanValue());break;
          case ERROR:type="error";value=FormulaError.forInt(v.getErrorValue()).getString();break;
          case BLANK:type="blank";value="";break;
          default:throw new IllegalArgumentException();
        }
        out.append(encode(sheet.getSheetName())).append('\t').append(cell.getAddress().formatAsString()).append('\t').append(type).append('\t').append(encode(value)).append('\n');
        if(out.length()>2000000)throw new IllegalArgumentException();
      }
      System.out.print(out);
    }
  }
}
