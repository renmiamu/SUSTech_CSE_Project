package edu.sustech.cs307.aggregation.AggState;

import edu.sustech.cs307.exception.DBException;
import edu.sustech.cs307.value.Value;

public interface AggState {
    /** 把一行里的输入值累加到当前状态 */
    void add(Value v) throws DBException;

    /** 扫描结束后给出聚合结果 */
    Value result();
}