package edu.sustech.cs307.aggregation;

import edu.sustech.cs307.aggregation.AggState.AggState;

import edu.sustech.cs307.aggregation.AggState.AvgState;
import edu.sustech.cs307.meta.TabCol;
import edu.sustech.cs307.value.ValueType;

public class AvgFunction implements AggregateFunction{
    private final String columnName;
    private final TabCol parameter;

    public AvgFunction(String columnName, TabCol parameter) {
        this.columnName = columnName;
        this.parameter = parameter;
    }
    @Override
    public AggState newState() {
        return new AvgState();
    }
    @Override
    public ValueType outputType() {
        return ValueType.FLOAT;
    }

    @Override
    public String alias() {
        return "AVG(" + columnName + ")";
    }

    @Override
    public TabCol getTabCol() {
        return parameter;
    }
}
