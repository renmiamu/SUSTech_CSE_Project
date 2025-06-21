package edu.sustech.cs307.aggregation;

import edu.sustech.cs307.aggregation.AggState.AggState;
import edu.sustech.cs307.aggregation.AggState.MaxState;
import edu.sustech.cs307.meta.TabCol;
import edu.sustech.cs307.value.ValueType;

public class MaxFunction implements AggregateFunction{
    private final String columnName;
    private final TabCol parameter;

    public MaxFunction(String columnName, TabCol parameter) {
        this.columnName = columnName;
        this.parameter = parameter;
    }

    @Override
    public AggState newState() { return new MaxState(); }
    @Override
    public ValueType outputType() {
        return ValueType.FLOAT;
    }

    @Override
    public String alias() {
        return "MAX(" + columnName + ")";
    }

    @Override
    public TabCol getTabCol() {
        return parameter;
    }
}
