package edu.sustech.cs307.logicalOperator;

import edu.sustech.cs307.aggregation.AggregateFunction;
import edu.sustech.cs307.exception.DBException;
import edu.sustech.cs307.exception.ExceptionTypes;
import edu.sustech.cs307.meta.TabCol;
import net.sf.jsqlparser.expression.Expression;
import net.sf.jsqlparser.expression.Function;
import net.sf.jsqlparser.schema.Column;
import net.sf.jsqlparser.statement.select.AllColumns;
import net.sf.jsqlparser.statement.select.SelectItem;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class LogicalAggregateOperator extends LogicalOperator {
    private final LogicalOperator child;
    private final List<Expression> groupByExpressions;  // 分组列（如 GROUP BY dept）
    private final List<AggregateFunction> aggregateFunctions;  // 聚合函数（如 SUM(salary))

    public LogicalAggregateOperator(LogicalOperator child,
            List<Expression> groupByExpressions,
            List<AggregateFunction> aggregateFunctions) {
        super(Collections.singletonList(child));
        this.child = child;
        this.groupByExpressions = groupByExpressions;
        this.aggregateFunctions = aggregateFunctions;
    }

    public LogicalOperator getChild() {
        return child;
    }

    public List<Expression> getGroupByExpressions() {
        return groupByExpressions;
    }

    public List<AggregateFunction> getAggregateFunctions() {
        return aggregateFunctions;
    }

    public List<TabCol> getOutputSchema() throws DBException {
        List<TabCol> outputSchema = new ArrayList<>();
        LogicalOperator iter = child;
        while (!(iter instanceof LogicalTableScanOperator)) {
            iter = iter.getChild();
        }
        LogicalTableScanOperator op = (LogicalTableScanOperator)iter;
        String table_name = op.getTableName();
        for (Expression exp : groupByExpressions) {
            outputSchema.add(new TabCol(table_name, exp.toString()));
        }
        for (AggregateFunction aggFunc : aggregateFunctions) {
            outputSchema.add(new TabCol(table_name, aggFunc.alias()));
        }
        return outputSchema;
    }
    @Override
    public String toString() {
        String gb = groupByExpressions == null || groupByExpressions.isEmpty()
                ? "[]"
                : groupByExpressions.toString();
        return "LogicalAggregateOperator(groupBy=" + gb +
                ", aggregates=" + aggregateFunctions.toString() + ")";
    }
}