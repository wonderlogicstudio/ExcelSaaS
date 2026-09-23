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
  private static final Set<String> MONTHLY_SHEETS=Set.of("M01","M02","M03","M04","M05","M06","M07","M08","M09","M10","M11","M12");
  private static final Set<String> TOKENS=Set.of("RefPtg","AreaPtg","IntPtg","NumberPtg","StringPtg","BoolPtg","ErrPtg",
    "AddPtg","SubtractPtg","MultiplyPtg","DividePtg","UnaryMinusPtg","UnaryPlusPtg","ParenthesisPtg",
    "EqualPtg","NotEqualPtg","GreaterThanPtg","LessThanPtg","GreaterEqualPtg","LessEqualPtg","AttrPtg");
  private static String decode(String s){return new String(Base64.getDecoder().decode(s),StandardCharsets.UTF_8);}
  private static String encode(String s){return Base64.getEncoder().encodeToString(s.getBytes(StandardCharsets.UTF_8));}
  private static String key(Sheet sheet,Cell cell){return sheet.getSheetName()+"!"+cell.getAddress().formatAsString();}
  private static Cell cellAt(Sheet sheet,int row,int col){
    Row r=sheet.getRow(row);return r==null?null:r.getCell(col);
  }
  private static void addFormulaDependency(Map<String,List<String>> graph,String node,Sheet sheet,Cell source){
    if(source!=null&&source.getCellType()==CellType.FORMULA)graph.get(node).add(key(sheet,source));
  }
  private static void addAreaDependencies(Map<String,List<String>> graph,String node,Sheet sheet,AreaPtg area){
    int firstRow=area.getFirstRow(),lastRow=area.getLastRow();
    int firstCol=area.getFirstColumn(),lastCol=area.getLastColumn();
    int rows=lastRow-firstRow+1,cols=lastCol-firstCol+1;
    long cells=(long)rows*(long)cols;
    if(rows<1||cols<1||cells>10000L)throw new IllegalArgumentException();
    for(int r=firstRow;r<=lastRow;r++)for(int c=firstCol;c<=lastCol;c++)addFormulaDependency(graph,node,sheet,cellAt(sheet,r,c));
  }
  private static void requireMonthlySource(Cell cell){
    if(cell==null)throw new IllegalArgumentException();
    CellType type=cell.getCellType();
    if(type==CellType.FORMULA)return;
    if(type==CellType.NUMERIC){if(!Double.isFinite(cell.getNumericCellValue()))throw new IllegalArgumentException();return;}
    throw new IllegalArgumentException();
  }
  private static int walk(Map<String,List<String>> graph,Map<String,Integer> depths,Set<String> visiting,String node,int depth){
    if(depth>100)throw new IllegalArgumentException();
    if(visiting.contains(node))throw new IllegalArgumentException();
    if(depths.containsKey(node)){
      if(depth+depths.get(node)>100)throw new IllegalArgumentException();
      return depths.get(node);
    }
    visiting.add(node);int longest=0;
    for(String child:graph.get(node))longest=Math.max(longest,1+walk(graph,depths,visiting,child,depth+1));
    visiting.remove(node);
    if(longest>100)throw new IllegalArgumentException();
    depths.put(node,longest);
    return longest;
  }
  public static void main(String[] args) {
    try {run();} catch(OutOfMemoryError e){System.exit(22);} catch(Throwable e){System.exit(20);}
  }
  static void run() throws Exception {
    BufferedReader reader=new BufferedReader(new InputStreamReader(System.in,StandardCharsets.UTF_8));
    String header=reader.readLine();
    boolean monthlyMode=false;
    if("CALC_V1".equals(header))monthlyMode=false;
    else if("CALC_V1\tmonthly_sheet_internal".equals(header))monthlyMode=true;
    else throw new IllegalArgumentException();
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
      Map<String,List<String>> graph=new HashMap<>();
      ArrayList<Cell> monthlyOperands=new ArrayList<>();
      ArrayList<Cell> monthlyFormulas=new ArrayList<>();
      for(Sheet sheet:workbook)for(Row row:sheet)for(Cell cell:row)if(cell.getCellType()==CellType.FORMULA){
        if(++formulas>1100)throw new IllegalArgumentException();
        String node=key(sheet,cell);graph.put(node,new ArrayList<>());
        int allowedLocalIfError=0;
        ArrayList<String> shape=new ArrayList<>();
        String monthlySheet=null;
        for(Ptg ptg:FormulaParser.parse(cell.getCellFormula(),model,FormulaType.CELL,workbook.getSheetIndex(sheet))){
          if(ptg instanceof NameXPxg){
            NameXPxg name=(NameXPxg)ptg;
            if(!"IFERROR".equals(name.getNameName())||name.getExternalWorkbookNumber()!=-1||name.getSheetName()!=null)throw new IllegalArgumentException();
            allowedLocalIfError++;
            shape.add("NAME");
          } else if(ptg instanceof Ref3DPxg){
            Ref3DPxg ref=(Ref3DPxg)ptg;
            String refSheet=ref.getSheetName();
            if(!monthlyMode||ref.getExternalWorkbookNumber()!=-1||ref.getLastSheetName()!=null||
              !MONTHLY_SHEETS.contains(refSheet)||!ref.isRowRelative()||!ref.isColRelative())throw new IllegalArgumentException();
            Sheet sourceSheet=workbook.getSheet(refSheet);if(sourceSheet==null)throw new IllegalArgumentException();
            Cell source=cellAt(sourceSheet,ref.getRow(),ref.getColumn());requireMonthlySource(source);
            monthlyOperands.add(source);
            if(source.getCellType()==CellType.FORMULA)graph.get(node).add(key(sourceSheet,source));
            if(monthlySheet==null)monthlySheet=refSheet;
            else if(!monthlySheet.equals(refSheet))throw new IllegalArgumentException();
            shape.add("M!R");
          } else if(ptg instanceof AbstractFunctionPtg){
            String name=((AbstractFunctionPtg)ptg).getName();
            if("#external#".equals(name)&&allowedLocalIfError>0)allowedLocalIfError--;
            else if(!FUNCTIONS.contains(name))throw new IllegalArgumentException();
            shape.add("FUNC");
          } else if(ptg instanceof RefPtg){
            RefPtg ref=(RefPtg)ptg;
            addFormulaDependency(graph,node,sheet,cellAt(sheet,ref.getRow(),ref.getColumn()));
            shape.add("R");
          } else if(ptg instanceof AreaPtg){
            addAreaDependencies(graph,node,sheet,(AreaPtg)ptg);
            shape.add("G");
          } else if(ptg instanceof SubtractPtg){
            shape.add("-");
          }
          else if(!TOKENS.contains(ptg.getClass().getSimpleName()))throw new IllegalArgumentException();
          else shape.add(ptg.getClass().getSimpleName());
        }
        if(monthlySheet!=null){
          String signature=String.join("",shape);
          if(!"M!R".equals(signature)&&!"M!RM!R-".equals(signature))throw new IllegalArgumentException();
          monthlyFormulas.add(cell);
        }
      }
      Map<String,Integer> depths=new HashMap<>();
      for(String node:graph.keySet())walk(graph,depths,new HashSet<>(),node,0);
      FormulaEvaluator evaluator=workbook.getCreationHelper().createFormulaEvaluator();
      evaluator.setIgnoreMissingWorkbooks(false);evaluator.clearAllCachedResultValues();
      for(Cell cell:monthlyOperands){
        CellValue v=evaluator.evaluate(cell);
        if(v==null||v.getCellType()!=CellType.NUMERIC||!Double.isFinite(v.getNumberValue()))throw new IllegalArgumentException();
      }
      for(Cell cell:monthlyFormulas){
        CellValue v=evaluator.evaluate(cell);
        if(v==null||v.getCellType()!=CellType.NUMERIC||!Double.isFinite(v.getNumberValue()))throw new IllegalArgumentException();
      }
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
