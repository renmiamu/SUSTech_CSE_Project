package edu.sustech.cs307.aggregation.AggState;

import edu.sustech.cs307.aggregation.AggState.AggState;
import edu.sustech.cs307.exception.DBException;
import edu.sustech.cs307.value.Value;

public class MinState implements AggState {
    private double min = Double.MAX_VALUE;
    @Override
    public void add(Value v) throws DBException {
        if (!(v == null)) {
            double d = Double.valueOf(v.toString());
            if (min > d) min = d;
        }
    }

    @Override
    public Value result() {
        String format = String.format("%.2f", min);
        return new Value(Double.valueOf(format));
    }
}
