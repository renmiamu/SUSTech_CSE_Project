package edu.sustech.cs307.aggregation.AggState;

import edu.sustech.cs307.aggregation.AggState.AggState;
import edu.sustech.cs307.exception.DBException;
import edu.sustech.cs307.value.Value;

public class MaxState implements AggState {
    private double max = Double.MIN_VALUE;
    @Override
    public void add(Value v) throws DBException {
        if (!(v == null)) {
            double d = Double.valueOf(v.toString());
            if (max < d) max = d;
        }
    }

    @Override
    public Value result() {
        String format = String.format("%.2f", max);
        return new Value(Double.valueOf(format));
    }
}
