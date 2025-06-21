package edu.sustech.cs307.physicalOperator;

import java.util.ArrayList;
import java.util.Collection;

import edu.sustech.cs307.exception.DBException;
import edu.sustech.cs307.meta.ColumnMeta;
import edu.sustech.cs307.meta.TabCol;
import edu.sustech.cs307.tuple.JoinTuple;
import edu.sustech.cs307.tuple.Tuple;
import edu.sustech.cs307.value.Value;
import edu.sustech.cs307.value.ValueComparer;
import net.sf.jsqlparser.expression.BinaryExpression;
import net.sf.jsqlparser.expression.Expression;

public class NestedLoopJoinOperator implements PhysicalOperator {

    private PhysicalOperator leftOperator;
    private PhysicalOperator rightOperator;
    private Collection<Expression> expr;
    // 运行期状态
    private Tuple   rightRow;
    private boolean rightExhausted;
    private Tuple   current;          // 当前输出行
    private TabCol[] joinedSchema;

    public NestedLoopJoinOperator(PhysicalOperator leftOperator, PhysicalOperator rightOperator,
            Collection<Expression> expr) {
        this.leftOperator = leftOperator;
        this.rightOperator = rightOperator;
        this.expr = expr;
    }

    @Override
    public boolean hasNext() throws DBException {
        if (rightExhausted) return false;

        while (true) {
            while (leftOperator.hasNext()) {
                leftOperator.Next();
                Tuple leftRow = leftOperator.Current();
                if (match(rightRow, leftRow)) {
                    current = buildJoinTuple(rightRow, leftRow);
                    return true;
                }
            }
            // left 用尽，换 right
            rightExhausted = !advanceRight();
            if (rightExhausted) return false;
        }
    }
    private boolean match(Tuple l, Tuple r) throws DBException {
        TabCol[] leftSchema = l.getTupleSchema();
        Value left = null;
        TabCol[] rightSchema = r.getTupleSchema();
        Value right = null;
        for (Expression exp : expr) {
            String leftColName = evalLeft(exp);
            String rightColName = evalRight(exp);
            for (int i = 0; i < leftSchema.length; i++) {
                TabCol col = leftSchema[i];
                if (col.getColumnName().toLowerCase().equals(leftColName)) {
                    left = l.getValue(col);
                }
            }
            for (int i = 0; i < rightSchema.length; i++) {
                TabCol col = rightSchema[i];
                if (col.getColumnName().toLowerCase().equals(rightColName)) {
                    right = r.getValue(col);
                }
            }
            if (ValueComparer.compare(left, right) != 0) return false;
        }
        return true;
    }
    private String evalLeft (Expression expression) {
        BinaryExpression binaryExpression = ((BinaryExpression) expression);
        String left = binaryExpression.getLeftExpression().toString().toLowerCase();
        if (left.contains(".")) {
            left = left.substring(left.indexOf('.') + 1);
        }
        return left;
    }
    private String evalRight (Expression expression) {
        BinaryExpression binaryExpression = ((BinaryExpression) expression);
        String right = binaryExpression.getRightExpression().toString().toLowerCase();
        if (right.contains(".")) {
            right = right.substring(right.indexOf('.') + 1);
        }
        return right;
    }
    private JoinTuple buildJoinTuple(Tuple l, Tuple r) {
        if (joinedSchema == null) {
            int m = l.getTupleSchema().length;
            int n = r.getTupleSchema().length;
            joinedSchema = new TabCol[m + n];
            System.arraycopy(l.getTupleSchema(), 0, joinedSchema, 0, m);
            System.arraycopy(r.getTupleSchema(), 0, joinedSchema, m, n);
        }
        return new JoinTuple(l, r, joinedSchema);
    }


    @Override
    public void Begin() throws DBException {
        leftOperator.Begin();
        rightOperator.Begin();

        rightExhausted = !advanceRight();   // 先定位第一条 right
    }
    /** 读取下一条 outer 行，成功返回 true；否则 false */
    private boolean advanceRight() throws DBException {
        if (!rightOperator.hasNext()) return false;
        rightOperator.Next();
        rightRow = rightOperator.Current();
        rewindLeft();                       // left 重新开始
        return true;
    }

    private void rewindLeft() throws DBException {
        leftOperator.Close();
        leftOperator.Begin();
    }
    @Override
    public void Next() {

    }

    @Override
    public Tuple Current() {
        return current;
    }

    @Override
    public void Close() {
        leftOperator.Close();
        rightOperator.Close();
    }

    @Override
    public ArrayList<ColumnMeta> outputSchema() {
        ArrayList<ColumnMeta> list = new ArrayList<>();
        list.addAll(leftOperator.outputSchema());
        list.addAll(rightOperator.outputSchema());
        return list;
    }
}
