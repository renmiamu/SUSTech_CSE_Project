package edu.sustech.cs307.optimizer;

import java.io.StringReader;
import java.util.ArrayList;
import java.util.List;

import edu.sustech.cs307.aggregation.*;
import edu.sustech.cs307.logicalOperator.dml.*;
import edu.sustech.cs307.meta.TabCol;
import edu.sustech.cs307.meta.TableMeta;
import net.sf.jsqlparser.JSQLParserException;
import net.sf.jsqlparser.expression.Expression;
import net.sf.jsqlparser.expression.Function;
import net.sf.jsqlparser.expression.operators.relational.ExpressionList;
import net.sf.jsqlparser.parser.CCJSqlParserManager;
import net.sf.jsqlparser.parser.JSqlParser;
import net.sf.jsqlparser.statement.DescribeStatement;
import net.sf.jsqlparser.statement.ExplainStatement;
import net.sf.jsqlparser.statement.ShowStatement;
import net.sf.jsqlparser.statement.Statement;
import net.sf.jsqlparser.statement.create.index.CreateIndex;
import net.sf.jsqlparser.statement.drop.Drop;
import net.sf.jsqlparser.statement.select.*;
import net.sf.jsqlparser.statement.show.ShowTablesStatement;
import net.sf.jsqlparser.statement.update.Update;
import net.sf.jsqlparser.statement.insert.Insert;
import net.sf.jsqlparser.statement.delete.Delete;
import net.sf.jsqlparser.statement.create.table.CreateTable;

import edu.sustech.cs307.exception.ExceptionTypes;
import edu.sustech.cs307.logicalOperator.*;
import edu.sustech.cs307.system.DBManager;
import edu.sustech.cs307.exception.DBException;

public class LogicalPlanner {
    public static LogicalOperator resolveAndPlan(DBManager dbManager, String sql) throws DBException {
        JSqlParser parser = new CCJSqlParserManager();
        Statement stmt = null;
        try {
            stmt = parser.parse(new StringReader(sql));
        } catch (JSQLParserException e) {
            throw new DBException(ExceptionTypes.InvalidSQL(sql, e.getMessage()));
        }
        LogicalOperator operator = null;
        // Query
        if (stmt instanceof Select selectStmt) {
            operator = handleSelect(dbManager, selectStmt);
        } else if (stmt instanceof Insert insertStmt) {
            operator = handleInsert(dbManager, insertStmt);
        } else if (stmt instanceof Update updateStmt) {
            operator = handleUpdate(dbManager, updateStmt);
        } else if (stmt instanceof Delete deleteStmt) {
            operator = handleDelete(dbManager, deleteStmt);
        } else if (stmt instanceof CreateIndex createIndex) {
            operator = handleIndex(dbManager, createIndex);
        }
        //todo: add condition of handleDelete
        // functional
        else if (stmt instanceof CreateTable createTableStmt) {
            CreateTableExecutor createTable = new CreateTableExecutor(createTableStmt, dbManager, sql);
            createTable.execute();
            return null;
        } else if (stmt instanceof ExplainStatement explainStatement) {
            ExplainExecutor explainExecutor = new ExplainExecutor(explainStatement, dbManager);
            explainExecutor.execute();
            return null;
        } else if (stmt instanceof ShowStatement showStatement) {
            ShowDatabaseExecutor showDatabaseExecutor = new ShowDatabaseExecutor(showStatement);
            showDatabaseExecutor.execute();
            return null;
        } else if (stmt instanceof ShowTablesStatement showTablesStatement) {
            ShowTablesExecutor showTablesExecutor = new ShowTablesExecutor(dbManager);
            showTablesExecutor.execute();
            return null;
        } else if (stmt instanceof DescribeStatement describeStatement) {
            DescribeExecutor describeExecutor = new DescribeExecutor(dbManager,describeStatement);
            describeExecutor.execute();
            return null;
        } else if (stmt instanceof Drop drop) {
            DropExecutor dropExecutor = new DropExecutor(dbManager,drop);
            dropExecutor.execute();
            return null;
        } else if (stmt instanceof ExplainStatement explainStatement) {
            ExplainExecutor explainExecutor = new ExplainExecutor(explainStatement, dbManager);
            explainExecutor.execute();
            return null;
        } else {
            throw new DBException(ExceptionTypes.UnsupportedCommand((stmt.toString())));
        }
        return operator;
    }


    public static LogicalOperator handleSelect(DBManager dbManager, Select selectStmt) throws DBException {
        PlainSelect plainSelect = selectStmt.getPlainSelect();
        if (plainSelect.getFromItem() == null) {
            throw new DBException(ExceptionTypes.UnsupportedCommand((plainSelect.toString())));
        }
        LogicalOperator root = new LogicalTableScanOperator(plainSelect.getFromItem().toString(), dbManager);
        String table_name = plainSelect.getFromItem().toString();

        int depth = 0;
        if (plainSelect.getJoins() != null) {
            for (Join join : plainSelect.getJoins()) {
                root = new LogicalJoinOperator(
                        root,
                        new LogicalTableScanOperator(join.getRightItem().toString(), dbManager),
                        join.getOnExpressions(),
                        depth);
                depth += 1;
            }
        }

        // 在 Join 之后应用 Filter，Filter 的输入是 Join 的结果 (root)
        if (!hasAggregate(plainSelect)) {
            // 非聚合查询：Filter -> Project
            if (plainSelect.getWhere() != null) {
                root = new LogicalFilterOperator(root, plainSelect.getWhere());
            }
        } else {
            // 聚合查询：处理 GROUP BY 和聚合函数
            // 1. 提取 GROUP BY 表达式（如 t.age）
            List<Expression> groupByExpressions = new ArrayList<>();
            if (plainSelect.getGroupBy() != null) {
                groupByExpressions = plainSelect.getGroupBy().getGroupByExpressionList();
            }
            // 2. 提取 SELECT 中的聚合函数（如 SUM(gpa)）
            List<AggregateFunction> aggregateFunctions = extractAggFunctions(plainSelect.getSelectItems(), table_name);

            // 3. 校验非聚合字段是否在 GROUP BY 中（如 SELECT dept, salary ... GROUP BY dept）
            validateNonAggColumns(plainSelect.getSelectItems(), groupByExpressions);

            // 4. 创建 LogicalAggregateOperator 统一处理分组和聚合
            root = new LogicalAggregateOperator(root, groupByExpressions, aggregateFunctions);
        }
        // 判断是否含有order by
        List<OrderByElement> orderByElements = plainSelect.getOrderByElements();
        if (orderByElements != null) {
            root = new LogicalSortOperator(root, orderByElements, table_name);
        }

        // 5. 最后添加 ProjectOperator 选择输出列
        root = new LogicalProjectOperator(root, plainSelect.getSelectItems());
        return root;
    }
    private static void validateNonAggColumns(List<SelectItem<?>> selectItems, List<Expression> groupByExpressions)
            throws DBException {
        List<Expression> nonAggColumns = new ArrayList<>();
        for (SelectItem<?> item : selectItems) {
            Expression expr = item.getExpression();
            if (!(expr instanceof Function) &&
            !containsExp(groupByExpressions, expr.toString())) {
                nonAggColumns.add(expr);
            }
        }
        if (!nonAggColumns.isEmpty()) {
            throw new DBException(ExceptionTypes.NonGroupedColumn(nonAggColumns.toString()));
        }
    }
    private static boolean containsExp(List<Expression> groupByExpressions, String exp) {
        for (Expression expression : groupByExpressions) {
            if (exp.equals(expression.toString())) return true;
        }
        return false;
    }
    private static List<AggregateFunction> extractAggFunctions(
            List<SelectItem<?>> selectItems, String table_name) throws DBException {
        List<AggregateFunction> aggFunctions = new ArrayList<>();
        for (SelectItem<?> item : selectItems) {
            Expression expr = item.getExpression();
            if (expr instanceof Function function) {
                String funcName = function.getName().toUpperCase();
                if (isAggregateFunction(funcName)) {
                    String columnName = function.getParameters().toString();
                    aggFunctions.add(getAggFunction(funcName, columnName, table_name));
                }
            }
        }
        return aggFunctions;
    }

    private static AggregateFunction getAggFunction(
            String functionName, String columnName, String table_name)
            throws DBException {
        switch (functionName.toUpperCase()) {
            case "SUM":
                return new SumFunction(columnName, new TabCol(table_name, columnName));
            case "AVG":
                return new AvgFunction(columnName, new TabCol(table_name, columnName));
            case "COUNT":
                return new CountFunction(columnName, new TabCol(table_name, columnName));
            case "MAX":
                return new MaxFunction(columnName, new TabCol(table_name, columnName));
            case "MIN":
                return new MinFunction(columnName, new TabCol(table_name, columnName));
            default:
                throw new DBException(ExceptionTypes.UnsupportedFunction(functionName));
        }
    }

    private static boolean isAggregateFunction(String funcName) {
        return funcName.equals("SUM") || funcName.equals("AVG") || funcName.equals("COUNT")
                || funcName.equals("MAX") || funcName.equals("MIN");
    }

    private static boolean hasAggregate(PlainSelect select) {
        for (SelectItem<?> selectItem : select.getSelectItems()) {
            if (selectItem.getExpression() instanceof Function function) {
                String funcName = function.getName().toUpperCase();
                if (isAggregateFunction(funcName)) return true;
            };
        }
        return false;
    }

    private static LogicalOperator handleInsert(DBManager dbManager, Insert insertStmt) {
        return new LogicalInsertOperator(insertStmt.getTable().getName(), insertStmt.getColumns(),
                insertStmt.getValues());
    }

    private static LogicalOperator handleUpdate(DBManager dbManager, Update updateStmt) throws DBException {
        LogicalOperator root = new LogicalTableScanOperator(updateStmt.getTable().getName(), dbManager);
        return new LogicalUpdateOperator(root, updateStmt.getTable().getName(), updateStmt.getUpdateSets(),
                updateStmt.getWhere());
    }

    private static LogicalOperator handleDelete(DBManager dbManager, Delete deleteStmt) throws DBException {
        LogicalOperator root = new LogicalTableScanOperator(deleteStmt.getTable().getName(), dbManager);
        return new LogicalDeleteOperator(root, deleteStmt.getTable().getName(),
                deleteStmt.getWhere());
    }

    private static LogicalOperator handleIndex(DBManager dbManager, CreateIndex createIndex) throws DBException {
        LogicalOperator root = new LogicalTableScanOperator(createIndex.getTable().getName(), dbManager);
        return new LogicalCreateIndexOperator(root, createIndex, TableMeta.IndexType.BTREE);
    }
}
