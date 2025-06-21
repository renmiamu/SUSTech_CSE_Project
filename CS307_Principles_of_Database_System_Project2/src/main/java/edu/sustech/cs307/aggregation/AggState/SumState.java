package edu.sustech.cs307.aggregation.AggState;

import edu.sustech.cs307.aggregation.AggState.AggState;
import edu.sustech.cs307.exception.DBException;
import edu.sustech.cs307.value.Value;

public class SumState implements AggState {
    private double sum = 0;
    @Override
    public void add(Value v) throws DBException {
        if (!(v == null)) {
            double d = Double.valueOf(v.toString());
            sum += d;
        }
    }

    @Override
    public Value result() {
        String format = String.format("%.2f", sum);
        return new Value(Double.valueOf(format));
    }
}
