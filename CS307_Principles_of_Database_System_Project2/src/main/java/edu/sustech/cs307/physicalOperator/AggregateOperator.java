package edu.sustech.cs307.physicalOperator;

import edu.sustech.cs307.aggregation.AggState.AggState;
import edu.sustech.cs307.aggregation.AggregateFunction;
import edu.sustech.cs307.exception.DBException;
import edu.sustech.cs307.meta.ColumnMeta;
import edu.sustech.cs307.meta.TabCol;
import edu.sustech.cs307.tuple.TempTuple;
import edu.sustech.cs307.tuple.Tuple;
import edu.sustech.cs307.value.Value;
import net.sf.jsqlparser.expression.Expression;

import java.util.*;

public class AggregateOperator implements PhysicalOperator {
    private final PhysicalOperator child;
    private final List<AggregateFunction> aggFuncs;
    private List<TabCol> outputSchema;
    private final List<Expression>  groupExprs;     // 分组键
    private final Map<GroupKey, AggState[]> hashTable = new HashMap<>();
    private Iterator<Map.Entry<GroupKey, AggState[]>> outputIter;
    private Map.Entry<GroupKey, AggState[]> current;
    private Tuple inputTuple;

    public AggregateOperator(PhysicalOperator child,
                             List<AggregateFunction> aggFuncs,
                             List<TabCol> outputSchema, List<Expression> groupExprs) {
        this.child = child;
        this.aggFuncs = aggFuncs;
        this.outputSchema = outputSchema;
        this.groupExprs = groupExprs;
    }

    @Override
    public void Begin() throws DBException {
        child.Begin();

        while (child.hasNext()) {
            child.Next();
            inputTuple = child.Current();

            // 计算 GroupKey
            GroupKey key;
            if (groupExprs == null || groupExprs.isEmpty()) {
                key = GroupKey.EMPTY;
            } else {
                List<Value> keyCols = new ArrayList<>(groupExprs.size());
                List<TabCol> tabCols = new ArrayList<>(groupExprs.size());
                for (Expression e : groupExprs) {
                    for (TabCol tabCol : outputSchema) {
                        if (tabCol.getColumnName().equals(e.toString())) {
                            Value v = getValue(tabCol);
                            tabCols.add(tabCol);
                            keyCols.add(v);
                        }
                    }
                }
                key = new GroupKey(keyCols, tabCols);
            }

            // 创建状态数组
            // 在哈希表里查一下这个 group key 有没有对应的状态数组
            AggState[] states = hashTable.get(key);
            if (states == null) {                     // 第一次遇到该分组，需要创建
                states = new AggState[aggFuncs.size()];   // 数组长度 = 聚合函数个数

                // 对每个聚合函数都 new 一份“空白”状态对象
                for (int i = 0; i < aggFuncs.size(); i++) {
                    AggregateFunction func = aggFuncs.get(i);
                    states[i] = func.newState();          // 调用工厂方法
                }

                // 把新建的状态数组放进哈希表，后续同组行可以复用
                hashTable.put(key, states);
            }

            // 累加
            Value[] values = getValues();
            for (int i = 0; i < aggFuncs.size(); i++) {
                AggregateFunction aggFunc = aggFuncs.get(i);
                states[i].add(values[i]);
            }
        }
        child.Close();
        outputIter = hashTable.entrySet().iterator();
    }
    private Value getValue(TabCol tabCol) throws DBException {
        for (TabCol projectColumn : outputSchema) {
            if (projectColumn.getColumnName().contains(tabCol.getColumnName())) {
                return inputTuple.getValue(tabCol); // Get value from input tuple
            }
        }
        return null;
    }
    private Value[] getValues() throws DBException {
        // 通过 meta 顺序和信息获取所有 Value
        ArrayList<Value> values = new ArrayList<>();
        for (AggregateFunction aggFunc : this.aggFuncs) {
            TabCol tabCol = aggFunc.getTabCol();
            Value value = getValue(tabCol);
            values.add(value);
        }

        return values.toArray(new Value[0]);
    }
    @Override
    public boolean hasNext() {
        return outputIter.hasNext();
    }

    @Override
    public void Next() {
        current = outputIter.next();
    }

    @Override
    public Tuple Current() {
        GroupKey key      = current.getKey();
        AggState[] states = current.getValue();

        List<Value> out = new ArrayList<>();

        //先放 group by 列值
        if (key != GroupKey.EMPTY) {
            for (int i = 0; i < key.cols.size(); i++) {
                TabCol tabCol = key.tabCols.get(i);
                if (checkOutput(tabCol)) out.add(key.cols.get(i));
            }
        }

        //再放聚合结果
        for (AggState s : states) out.add(s.result());

        return new TempTuple(out);
    }
    private boolean checkOutput(TabCol tabCol) {
        if (outputSchema.contains(tabCol)) return true;
        return false;
    }
    @Override
    public void Close() {}

    @Override
    public ArrayList<ColumnMeta> outputSchema() {
        ArrayList<ColumnMeta> result = new ArrayList<>();
        String table_name = "";

        ArrayList<String> columns = new ArrayList<>();
        for (TabCol tabCol : outputSchema){
            columns.add(tabCol.getColumnName().toLowerCase());
        }
        for (ColumnMeta columnMeta : child.outputSchema()) {
            if (columns.contains(columnMeta.name.toLowerCase())) {
                result.add(columnMeta);
            }
        }

        for (int i = 0; i < aggFuncs.size(); i++) {
            AggregateFunction func = aggFuncs.get(i);
            int offset = 0;
            result.add(new ColumnMeta(table_name, func.alias(), func.outputType(),
                    func.outputType().getLen(), offset));
            offset += func.outputType().getLen();
        }

        return result;
    }
    private static final class GroupKey {
        public static final GroupKey EMPTY = new GroupKey(Collections.emptyList(),
                Collections.emptyList());
        final List<Value> cols;
        final List<TabCol> tabCols;
        GroupKey(List<Value> cols, List<TabCol> tabCols) {
            this.cols = cols;
            this.tabCols = tabCols;
        }
        @Override public boolean equals(Object o){ return cols.equals(((GroupKey)o).cols);}
        @Override public int hashCode() {
            return cols.hashCode();
        }
    }
}
