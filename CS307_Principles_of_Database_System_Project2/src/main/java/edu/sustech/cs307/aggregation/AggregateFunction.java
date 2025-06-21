package edu.sustech.cs307.aggregation;

import edu.sustech.cs307.aggregation.AggState.AggState;
import edu.sustech.cs307.meta.TabCol;
import edu.sustech.cs307.value.ValueType;

public interface AggregateFunction {
    AggState newState();
    ValueType outputType();       // 结果列类型（SUM int ⇒ BIGINT 等）
    String alias();               // 结果列名，建议形如 "SUM(salary)"
    TabCol getTabCol();
}
