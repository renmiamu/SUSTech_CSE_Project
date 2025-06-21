package edu.sustech.cs307.logicalOperator;

import net.sf.jsqlparser.expression.Expression;

import java.util.Collections;

public class LogicalDeleteOperator extends LogicalOperator{
    private final String tableName;
    private final Expression expressions;
    public LogicalDeleteOperator(LogicalOperator child, String tableName, Expression expressions) {
        super(Collections.singletonList(child));
        this.tableName = tableName;
        this.expressions = expressions;
    }
    public Expression getExpression() {
        return expressions;
    }
    public String getTableName() {
        return tableName;
    }
    @Override
    public String toString() {
        return "DeleteOperator(table=" + tableName + ")\n ├── " + childern.get(0);
    }
}
