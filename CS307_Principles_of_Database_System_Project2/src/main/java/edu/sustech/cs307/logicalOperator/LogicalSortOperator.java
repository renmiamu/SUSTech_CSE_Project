package edu.sustech.cs307.logicalOperator;
import net.sf.jsqlparser.statement.select.OrderByElement;

import java.util.Collections;
import java.util.List;

public class LogicalSortOperator extends LogicalOperator{
    private final LogicalOperator child;
    private final List<OrderByElement> orderByElements;
    private final String table_name;

    public LogicalSortOperator(LogicalOperator child, List<OrderByElement> orderByElements, String tableName) {
        super(Collections.singletonList(child));
        this.child = child;
        this.orderByElements = orderByElements;
        table_name = tableName;
    }

    public LogicalOperator getChild() {
        return child;
    }
    public List<OrderByElement> getOrderByElements() { return orderByElements; }

    @Override
    public String toString() {
        return null;
    }

    public String getTable() { return table_name; }
}
