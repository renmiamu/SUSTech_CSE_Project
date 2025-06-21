package edu.sustech.cs307.aggregation;

import edu.sustech.cs307.aggregation.AggState.AggState;
import edu.sustech.cs307.aggregation.AggState.CountState;
import edu.sustech.cs307.meta.TabCol;
import edu.sustech.cs307.value.ValueType;

public class CountFunction implements AggregateFunction{
    private final String columnName;
    private final TabCol parameter;

    public CountFunction(String columnName, TabCol parameter) {
        this.columnName = columnName;
        this.parameter = parameter;
    }

    @Override
    public AggState newState() { return new CountState(); }

    @Override
    public ValueType outputType() {
        return ValueType.INTEGER;
    }

    @Override
    public String alias() {
        return "COUNT(" + columnName + ")";
    }

    @Override
    public TabCol getTabCol() {
        return parameter;
    }
}
