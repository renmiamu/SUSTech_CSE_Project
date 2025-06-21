package edu.sustech.cs307.physicalOperator;

import edu.sustech.cs307.exception.DBException;
import edu.sustech.cs307.index.BPlusTreeIndex;
import edu.sustech.cs307.index.InMemoryOrderedIndex;
import edu.sustech.cs307.meta.ColumnMeta;
import edu.sustech.cs307.meta.TableMeta;
import edu.sustech.cs307.record.RID;
import edu.sustech.cs307.record.Record;
import edu.sustech.cs307.record.RecordFileHandle;
import edu.sustech.cs307.record.RecordPageHandle;
import edu.sustech.cs307.system.DBManager;
import edu.sustech.cs307.tuple.TableTuple;
import edu.sustech.cs307.tuple.Tuple;
import edu.sustech.cs307.value.Value;
import edu.sustech.cs307.value.ValueType;
import net.sf.jsqlparser.expression.*;
import net.sf.jsqlparser.expression.operators.relational.Between;
import net.sf.jsqlparser.schema.Column;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

public class IndexScanOperator implements PhysicalOperator {
    private BPlusTreeIndex index;
    private DBManager dbManager;
    private final String tableName;
    private TableMeta tableMeta;
    private RecordFileHandle fileHandle;
    private Record currentRecord;
    private RID currentRID;

    //这里目前只处理binary expression和between expression
    private final BinaryExpression expr;
    private final Between between;
    private final String operator;
    Iterator<Map.Entry<Value, RID>> iter;
    private RecordPageHandle pinnedPage = null;
    private int pinnedPageNum  = -1;
    public IndexScanOperator(BPlusTreeIndex index, DBManager dbManager,
                                     String tableName, Expression expr) {
        this.dbManager = dbManager;
        this.index = index;
        this.tableName = tableName;
        try {
            this.tableMeta = dbManager.getMetaManager().getTable(tableName);
        } catch (DBException e) {
            // Handle exception properly, maybe log or rethrow
            e.printStackTrace();
        }
        if (expr instanceof BinaryExpression binaryExpression) {
            this.expr = binaryExpression;
            this.between = null;
            this.operator = binaryExpression.getStringExpression();
        } else {
            this.expr = null;
            this.between = (Between)expr;
            this.operator = null;
        }
    }
    @Override
    public boolean hasNext() {
        return iter != null && iter.hasNext();
    }

    @Override
    public void Begin() throws DBException {
        if (expr != null) {
            Value value = getValue(expr);
            switch (operator) {
                case "=" :
                    RID rid = index.EqualTo(value);
                    if (rid != null)
                        iter = List.of(Map.entry(value, rid)).iterator();
                    break;

                case ">" :
                    iter = index.MoreThan(value, false);
                    break;

                case ">=" :
                    iter = index.MoreThan(value, true);
                    break;

                case "<" :
                    iter = index.LessThan(value, false);
                    break;

                case "<=" :
                    iter = index.LessThan(value, true);
                    break;
            }
        } else {
            Value left = getConstantValue(between.getBetweenExpressionStart());
            Value right = getConstantValue(between.getBetweenExpressionEnd());
            iter = index.Range(left, right, true, false);
        }
        fileHandle = dbManager.getRecordManager().OpenFile(tableName);
    }

    private Value getValue(BinaryExpression binaryExpr) {
        Expression leftExpr = binaryExpr.getLeftExpression();
        Expression rightExpr = binaryExpr.getRightExpression();
        String operator = binaryExpr.getStringExpression();
        Value value = null;

        if (leftExpr instanceof Column leftColumn) {
            value = getConstantValue(rightExpr);
        } else {
            value = getConstantValue(leftExpr); // Handle constant left value
        }
        return value;
    }

    private Value getConstantValue(Expression expr) {
        if (expr instanceof StringValue) {
            return new Value(((StringValue) expr).getValue(), ValueType.CHAR);
        } else if (expr instanceof DoubleValue) {
            return new Value(((DoubleValue) expr).getValue(), ValueType.FLOAT);
        } else if (expr instanceof LongValue) {
            return new Value(((LongValue) expr).getValue(), ValueType.INTEGER);
        }
        return null; // Unsupported constant type
    }
    @Override
    public void Next() {
        currentRecord = null;
        try{
            if (hasNext()) {
                Map.Entry<Value,RID> e = iter.next();
                currentRID = e.getValue();

                //modify
                if (pinnedPage == null || pinnedPageNum != currentRID.pageNum) {
                    // 2a. 先 Unpin 旧页
                    if (pinnedPage != null)
                        fileHandle.UnpinPageHandle(pinnedPageNum,false);

                    // 2b. 再 Pin 新页
                    pinnedPage     = fileHandle.FetchPageHandle(currentRID.pageNum);
                    pinnedPageNum  = currentRID.pageNum;
                }

                currentRecord = fileHandle.GetRecord(currentRID);
            }
        } catch (DBException e) {
            throw new RuntimeException(e);
        }
    }

    @Override
    public Tuple Current() { // Return Tuple
        if (currentRecord == null) {
            return null;
        }
        return new TableTuple(tableName, tableMeta, currentRecord, currentRID);
    }

    @Override
    public void Close() {
        try {
            if (pinnedPage != null)
                fileHandle.UnpinPageHandle(pinnedPageNum,false);
            if (fileHandle != null)
                dbManager.getRecordManager().CloseFile(fileHandle);
        } catch (DBException ignored) {}
        iter = null; fileHandle = null; pinnedPage = null;
    }

    @Override
    public ArrayList<ColumnMeta> outputSchema() {
        return tableMeta.columns_list;
    }
}
