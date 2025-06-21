package edu.sustech.cs307.logicalOperator;

import edu.sustech.cs307.meta.MetaManager;
import edu.sustech.cs307.meta.TableMeta;
import net.sf.jsqlparser.statement.create.index.CreateIndex;

import java.util.Collections;

public class LogicalCreateIndexOperator extends LogicalOperator {
    private final String tableName, columnName, indexName;
    private final TableMeta.IndexType indexType;

    public LogicalCreateIndexOperator(LogicalOperator child,
                                      CreateIndex createIndex, TableMeta.IndexType indexType) {
        super(Collections.singletonList(child));
        this.tableName = createIndex.getTable().getName();
        this.columnName = createIndex.getIndex().getColumns().get(0).getColumnName();
        this.indexName = createIndex.getIndex().getName();
        this.indexType = indexType;
    }

    public String getColumn() { return columnName; }
    public TableMeta.IndexType getType() { return indexType; }
    @Override
    public String toString() {
        return null;
    }
}
