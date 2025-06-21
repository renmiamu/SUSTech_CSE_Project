package edu.sustech.cs307.aggregation.AggState;

import edu.sustech.cs307.exception.DBException;
import edu.sustech.cs307.value.Value;

public class AvgState implements AggState {
    private double sum = 0;
    private long cnt = 0;

    @Override
    public void add(Value v) throws DBException {
        if (!(v == null)) {
            double d = Double.valueOf(v.toString());
            sum += d;
            cnt++;
        }
    }

    @Override
    public Value result() {
        sum /= cnt;
        String format = String.format("%.2f", sum);
        return new Value(Double.valueOf(format));
    }
}