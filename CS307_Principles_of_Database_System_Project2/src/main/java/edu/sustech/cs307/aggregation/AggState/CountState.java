package edu.sustech.cs307.aggregation.AggState;

import edu.sustech.cs307.aggregation.AggState.AggState;
import edu.sustech.cs307.exception.DBException;
import edu.sustech.cs307.value.Value;

public class CountState implements AggState {
    private long count = 0;
    @Override
    public void add(Value v) throws DBException {
        if (!(v == null)) {
            count ++;
        }
    }

    @Override
    public Value result() {
        return new Value(Long.valueOf(count));
    }
}
