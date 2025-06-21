package edu.sustech.cs307.physicalOperator;

import edu.sustech.cs307.exception.DBException;
import edu.sustech.cs307.exception.ExceptionTypes;
import edu.sustech.cs307.meta.ColumnMeta;
import edu.sustech.cs307.meta.TabCol;
import edu.sustech.cs307.tuple.TableTuple;
import edu.sustech.cs307.tuple.TempTuple;
import edu.sustech.cs307.tuple.Tuple;
import edu.sustech.cs307.value.Value;
import edu.sustech.cs307.value.ValueComparer;
import net.sf.jsqlparser.expression.Expression;
import net.sf.jsqlparser.statement.select.OrderByElement;

import java.util.ArrayList;
import java.util.List;

public class SortOperator implements PhysicalOperator{
    private String table_name;
    private final PhysicalOperator child;
    private final List<OrderByElement> orderByElements;
    private List<Tuple> buffer;
    private List<TabCol> outputSchema;
    private int pos;

    public SortOperator(PhysicalOperator child, List<OrderByElement> orderByElements,
                        String table_name) {
        this.child = child;
        outputSchema();
        this.orderByElements = orderByElements;
        this.table_name = table_name;
        pos = -1;
    }

    @Override
    public boolean hasNext() { return pos + 1 < buffer.size(); }

    @Override
    public void Begin() throws DBException {
        child.Begin();
        buffer = new ArrayList<>();
        while (child.hasNext()) {
            child.Next();
            buffer.add(child.Current());
        }
        child.Close();

        // 排序
        try {
            buffer.sort((t1, t2) -> {               // λ 表达式当 Comparator
                try {
                    return compare(t1, t2);    // 内部真正比较
                } catch (DBException e) {
                    throw new RuntimeException(e);  // 包成非受检异常
                }
            });
        } catch (RuntimeException re) {
            if (re.getCause() instanceof DBException dbe)   // 拆包还原
                throw dbe;
            throw re;                                       // 其它异常原样抛
        }
    }

    private int compare(Tuple a, Tuple b) throws DBException {
        for (OrderByElement oe : orderByElements) {
            Value va = ExpressionEvaluator(oe.getExpression(), a);
            Value vb = ExpressionEvaluator(oe.getExpression(), b);
            int result  = ValueComparer.compare(va, vb);
            if (result != 0) return oe.isAsc() ? result : -result;
        }
        return 0;
    }
    private Value ExpressionEvaluator (Expression exp, Tuple tuple) throws DBException {
        return getValue(new TabCol(table_name, exp.toString()), tuple);
    }
    private Value getValue(TabCol tabCol, Tuple tuple) throws DBException {
        if (tuple instanceof TableTuple tableTuple) return tuple.getValue(tabCol);
        else if (tuple instanceof TempTuple tempTuple) {
            List<ColumnMeta> schema = outputSchema();
            for (int i = 0; i < schema.size(); i++) {
                String output = schema.get(i).name;
                if (tabCol.getColumnName().toLowerCase().equals(output.toLowerCase())) return tuple.getValues()[i];
            }
            return null;
        } else throw new DBException(ExceptionTypes.InvalidTuple("Getting" +
                " value from invalid tuple"));
    }
    @Override
    public void Next() { pos++; }

    @Override
    public Tuple Current()   { return buffer.get(pos); }

    @Override
    public void Close() {

    }

    @Override
    public ArrayList<ColumnMeta> outputSchema() {
        return child.outputSchema();
    }
}
