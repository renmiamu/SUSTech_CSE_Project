package edu.sustech.cs307.aggregation;

import edu.sustech.cs307.aggregation.AggState.AggState;
import edu.sustech.cs307.aggregation.AggState.SumState;
import edu.sustech.cs307.meta.TabCol;
import edu.sustech.cs307.value.ValueType;

public class SumFunction implements AggregateFunction {
    private final String columnName;
    private final TabCol parameter;

    public SumFunction(String columnName, TabCol parameter) {
        this.columnName = columnName;
        this.parameter = parameter;
    }

    @Override
    public AggState newState() { return new SumState(); }

    @Override
    public ValueType outputType() {
        return ValueType.FLOAT;
    }

    @Override
    public String alias() {
        return "SUM(" + columnName + ")";
    }

    @Override
    public TabCol getTabCol() {
        return parameter;
    }
}