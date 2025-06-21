package edu.sustech.cs307.logicalOperator.dml;

import edu.sustech.cs307.exception.DBException;
import edu.sustech.cs307.system.DBManager;
import net.sf.jsqlparser.statement.DescribeStatement;

public class DescribeExecutor implements DMLExecutor{
    private final DBManager dbManager;
    private final DescribeStatement describeStatement;
    public DescribeExecutor(DBManager dbManager, DescribeStatement describeStatement) {
        this.dbManager = dbManager;
        this.describeStatement = describeStatement;
    }

    @Override
    public void execute() throws DBException {
        String table_name = describeStatement.getTable().getName();
        dbManager.descTable(table_name);
    }
}
