package edu.sustech.cs307.logicalOperator.dml;

import edu.sustech.cs307.exception.DBException;
import edu.sustech.cs307.system.DBManager;

public class ShowTablesExecutor implements DMLExecutor{
    private final DBManager dbManager;
    public ShowTablesExecutor(DBManager dbManager) {
        this.dbManager = dbManager;
    }

    @Override
    public void execute() throws DBException {
        dbManager.showTables();
    }
}
