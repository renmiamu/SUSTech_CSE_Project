package edu.sustech.cs307.logicalOperator.dml;

import edu.sustech.cs307.exception.DBException;
import edu.sustech.cs307.system.DBManager;
import net.sf.jsqlparser.statement.drop.Drop;
import org.pmw.tinylog.Logger;

public class DropExecutor implements DMLExecutor{
    private final DBManager dbManager;
    private final Drop drop;

    public DropExecutor(DBManager dbManager, Drop drop) {
        this.dbManager = dbManager;
        this.drop = drop;
    }

    @Override
    public void execute() throws DBException {
        String table_name = drop.getName().getName();
        if (drop.getType().toLowerCase().equals("index")) {
            String indexName = table_name;
            table_name = drop.getParameters().get(1);
            dbManager.dropIndex(table_name, indexName);
            Logger.info("Successfully dropped index: {}", indexName);
        } else {
            dbManager.dropTable(table_name);
            Logger.info("Successfully dropped table: {}", table_name);
        }
    }
}
