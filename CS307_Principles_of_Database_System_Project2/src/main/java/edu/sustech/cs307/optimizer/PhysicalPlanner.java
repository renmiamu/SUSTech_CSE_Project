package edu.sustech.cs307.optimizer;

import edu.sustech.cs307.exception.DBException;
import edu.sustech.cs307.exception.ExceptionTypes;
import edu.sustech.cs307.index.BPlusTreeIndex;
import edu.sustech.cs307.index.InMemoryOrderedIndex;
import edu.sustech.cs307.index.Index;
import edu.sustech.cs307.logicalOperator.*;
import edu.sustech.cs307.physicalOperator.*;
import edu.sustech.cs307.system.DBManager;
import edu.sustech.cs307.value.Value;
import edu.sustech.cs307.value.ValueType;
import edu.sustech.cs307.meta.ColumnMeta;
import edu.sustech.cs307.meta.TableMeta;

import net.sf.jsqlparser.expression.*;
import net.sf.jsqlparser.expression.operators.relational.Between;
import net.sf.jsqlparser.expression.operators.relational.ExpressionList;
import net.sf.jsqlparser.expression.operators.relational.ParenthesedExpressionList;
import net.sf.jsqlparser.schema.Column;
import net.sf.jsqlparser.statement.select.Values;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Map;

public class PhysicalPlanner {
    public static PhysicalOperator generateOperator(DBManager dbManager, LogicalOperator logicalOp) throws DBException {
        if (logicalOp instanceof LogicalTableScanOperator tableScanOperator) {
            return handleTableScan(dbManager, tableScanOperator);
        } else if (logicalOp instanceof LogicalFilterOperator filterOperator) {
            return handleFilter(dbManager, filterOperator);
        } else if (logicalOp instanceof LogicalJoinOperator joinOperator) {
            return handleJoin(dbManager, joinOperator);
        } else if (logicalOp instanceof LogicalProjectOperator projectOperator) {
            return handleProject(dbManager, projectOperator);
        } else if (logicalOp instanceof LogicalInsertOperator insertOperator) {
            return handleInsert(dbManager, insertOperator);
        } else if (logicalOp instanceof LogicalUpdateOperator updateOperator) {
            return handleUpdate(dbManager, updateOperator);
        } else if (logicalOp instanceof LogicalDeleteOperator deleteOperator) {
            return handleDelete(dbManager, deleteOperator);
        } else if (logicalOp instanceof LogicalAggregateOperator aggregateOperator) {
          return handleAggregate(dbManager, aggregateOperator);
        } else if (logicalOp instanceof LogicalSortOperator sortOperator) {
          return handleSort(dbManager, sortOperator);
        } else if (logicalOp instanceof LogicalCreateIndexOperator indexOperator) {
          return handleIndex(dbManager, indexOperator);
        } else {
            throw new DBException(ExceptionTypes.UnsupportedOperator(logicalOp.getClass().getSimpleName()));
        }
    }

    private static PhysicalOperator handleTableScan(DBManager dbManager, LogicalTableScanOperator logicalTableScanOp) {
        String tableName = logicalTableScanOp.getTableName();
        TableMeta tableMeta;
        try {
            tableMeta = dbManager.getMetaManager().getTable(tableName);
        } catch (DBException e) {
            // Fallback to SeqScan if TableMeta cannot be retrieved
            return new SeqScanOperator(tableName, dbManager);
        }

        return new SeqScanOperator(tableName, dbManager);
    }
    private static String whetherIndexScan (DBManager dbManager, LogicalFilterOperator logicalFilterOp) {
        LogicalTableScanOperator scan = ((LogicalTableScanOperator) logicalFilterOp.getChild());
        String tableName = scan.getTableName();
        TableMeta tableMeta;
        try {
            tableMeta = dbManager.getMetaManager().getTable(tableName);
        } catch (DBException e) {
            return null;
        }

        Map<String, TableMeta.IndexType > indexes = tableMeta.getIndexes();
        if (indexes.isEmpty()) {
            return "";
        }
        Expression expr = logicalFilterOp.getWhereExpr();
        String path = "CS307-DB/meta/" + tableName + "_";
        if (expr instanceof BinaryExpression binaryExpr) {
            Expression leftExpr = binaryExpr.getLeftExpression();
            Expression rightExpr = binaryExpr.getRightExpression();
            if (leftExpr instanceof Column leftColum) {
                if (indexes.containsKey(leftColum.getColumnName())) {
                    String type = indexes.get(leftColum.getColumnName()).name();
                    return path + leftColum.getColumnName() + "_" + type + ".json";
                }
            } else if (rightExpr instanceof Column rightColumn) {
                if (indexes.containsKey(rightColumn.getColumnName())) {
                    String type = indexes.get(rightColumn.getColumnName()).name();
                    return path + rightColumn.getColumnName() + "_" + type + ".json";
                }
            }
        } else if (expr instanceof Between between) {
            if (indexes.containsKey(between.getLeftExpression().toString())){
                String column = between.getLeftExpression().toString();
                String type = indexes.get(column).name();
                return path + column + "_" + type + ".json";
            }
        }
        return "";
    }

    private static PhysicalOperator handleFilter(DBManager dbManager, LogicalFilterOperator logicalFilterOp)
            throws DBException {
        LogicalTableScanOperator scan = ((LogicalTableScanOperator) logicalFilterOp.getChild());
        String tableName = scan.getTableName();
        String index_name = whetherIndexScan(dbManager, logicalFilterOp);
        if (index_name.length() > 0) {
            Expression expression = logicalFilterOp.getWhereExpr();
            if (expression instanceof BinaryExpression expr) {
                if (index_name.contains("InMemory")) {
                    InMemoryOrderedIndex index = new InMemoryOrderedIndex(index_name);
                    return new InMemoryIndexScanOperator(index, dbManager, tableName, expr);
                } else {
                    BPlusTreeIndex index = new BPlusTreeIndex(index_name);
                    return new IndexScanOperator(index, dbManager, tableName, expr);
                }
            } else if (expression instanceof Between between) {
                if (index_name.contains("InMemory")) {
                    InMemoryOrderedIndex index = new InMemoryOrderedIndex(index_name);
                    return new InMemoryIndexScanOperator(index, dbManager, tableName, between);
                } else {
                    BPlusTreeIndex index = new BPlusTreeIndex(index_name);
                    return new IndexScanOperator(index, dbManager, tableName, between);
                }
            }

        }
        PhysicalOperator inputOp = generateOperator(dbManager, logicalFilterOp.getChild());
        return new FilterOperator(inputOp, logicalFilterOp.getWhereExpr());
    }

    private static PhysicalOperator handleJoin(DBManager dbManager, LogicalJoinOperator logicalJoinOp)
            throws DBException {
        PhysicalOperator leftOp = generateOperator(dbManager, logicalJoinOp.getLeftInput());
        PhysicalOperator rightOp = generateOperator(dbManager, logicalJoinOp.getRightInput());
        PhysicalOperator joinOp = new NestedLoopJoinOperator(leftOp, rightOp, logicalJoinOp.getJoinExprs());

        Collection<Expression> joinFilters = logicalJoinOp.getJoinExprs();
        PhysicalOperator finalOp = new FilterOperator(joinOp, joinFilters);

        return finalOp;
    }

    private static PhysicalOperator handleProject(DBManager dbManager, LogicalProjectOperator logicalProjectOp)
            throws DBException {
        PhysicalOperator inputOp = generateOperator(dbManager, logicalProjectOp.getChild());
        return new ProjectOperator(inputOp, logicalProjectOp.getOutputSchema());
    }

    private static PhysicalOperator handleAggregate(DBManager dbManager, LogicalAggregateOperator aggregateOperator)
            throws DBException {
        PhysicalOperator inputOp = generateOperator(dbManager, aggregateOperator.getChild());
        return new AggregateOperator(inputOp, aggregateOperator.getAggregateFunctions(),
                aggregateOperator.getOutputSchema(),aggregateOperator.getGroupByExpressions()
                 );
    }

    /**
     * 处理将逻辑插入操作转换为物理插入运算符的过程
     * 
     * @param dbManager       提供数据库操作访问的数据库管理器实例
     * @param logicalInsertOp 需要被转换的逻辑插入运算符
     * @return 准备好执行的物理插入运算符
     * @throws DBException 如果存在列不匹配、类型不匹配或无效SQL语法时抛出
     */
    @SuppressWarnings("deprecation") // for ExpressionList<?>::getExpressions
    private static PhysicalOperator handleInsert(DBManager dbManager, LogicalInsertOperator logicalInsertOp)
            throws DBException {
        var tableMeta = dbManager.getMetaManager().getTable(logicalInsertOp.tableName);
        // Process columns
        List<String> columns = new ArrayList<>();
        if (logicalInsertOp.columns != null) {
            // the length must equal to the number of columns in the table
            if (tableMeta.columns.size() != logicalInsertOp.columns.size()) {
                throw new DBException(ExceptionTypes.InsertColumnSizeMismatch());
            }
            for (int i = 0; i < logicalInsertOp.columns.size(); i++) {
                String colName = logicalInsertOp.columns.get(i).getColumnName();
                if (tableMeta.getColumnMeta(colName) == null) {
                    throw new DBException(ExceptionTypes.ColumnDoseNotExist(colName));
                }
                if (!tableMeta.columns_list.get(i).name.equals(colName)) {
                    throw new DBException(ExceptionTypes.InsertColumnNameMismatch());
                }
                columns.add(colName);
            }

        } else {
            // If no columns specified, use all table columns in order
            for (ColumnMeta columnMeta : tableMeta.columns_list) {
                columns.add(columnMeta.name);
            }
        }
        if (!(logicalInsertOp.values instanceof Values)) {
            throw new DBException(ExceptionTypes.InvalidSQL("INSERT", "Values must be an expression list"));
        }
        ExpressionList<?> valuesList = ((Values) logicalInsertOp.values).getExpressions();
        if (columns.size() != valuesList.size()) {
            var element = valuesList.get(0);
            if (element instanceof ParenthesedExpressionList<?> parenthesed) {
                // check the children reexpressions
                for (Expression expr : valuesList) {
                    if (expr instanceof ParenthesedExpressionList<?> expressionList) {
                        if (expressionList.getExpressions().size() != columns.size()) {
                            throw new DBException(ExceptionTypes.InsertColumnSizeMismatch());
                        }
                    } else {
                        throw new DBException(ExceptionTypes.InsertColumnSizeMismatch());
                    }
                }
            } else {
                throw new DBException(ExceptionTypes.InsertColumnSizeMismatch());
            }
        }

        List<Value> values = new ArrayList<>();
        parseValue(values, valuesList, tableMeta);
        // will always be same size tuple


        return new InsertOperator(logicalInsertOp.tableName, columns,
                values, dbManager);
    }

    @SuppressWarnings("deprecation")
    private static void parseValue(List<Value> values, ExpressionList<?> valuesList, TableMeta tableMeta)
            throws DBException {
        for (int i = 0; i < valuesList.size(); i++) {
            var expr = valuesList.getExpressions().get(i);
            if (expr instanceof StringValue string_value) {
                if (tableMeta.columns_list.get(i).type != ValueType.CHAR) {
                    throw new DBException(ExceptionTypes.InsertColumnTypeMismatch());
                }
                String value_str = string_value.getValue();
                if (value_str.length() > 64) {
                    value_str = value_str.substring(0, 64);
                }
                values.add(new Value(value_str));
            } else if (expr instanceof DoubleValue float_value) {
                if (tableMeta.columns_list.get(i).type != ValueType.FLOAT) {
                    throw new DBException(ExceptionTypes.InsertColumnTypeMismatch());
                }
                values.add(new Value(float_value.getValue()));
            } else if (expr instanceof LongValue long_value) {
                if (tableMeta.columns_list.get(i).type != ValueType.INTEGER) {
                    throw new DBException(ExceptionTypes.InsertColumnTypeMismatch());
                }
                values.add(new Value(long_value.getValue()));
            } else if (expr instanceof ParenthesedExpressionList<?> expressionList) {
                parseValue(values, expressionList, tableMeta);
            } else {
                throw new DBException(ExceptionTypes.InvalidSQL("INSERT", "Unsupported value type in VALUES clause"));
            }
        }
    }


    private static PhysicalOperator handleUpdate(DBManager dbManager, LogicalUpdateOperator logicalUpdateOp) throws DBException {
        // TODO: Implement handleUpdate
        PhysicalOperator scanner = generateOperator(dbManager, logicalUpdateOp.getChild());
        if (logicalUpdateOp.getColumns().size() != 1 ) {
            throw new DBException(ExceptionTypes.InvalidSQL("INSERT", "Unsupported expression list"));
        }
        return new UpdateOperator(scanner, logicalUpdateOp.getTableName(), logicalUpdateOp.getColumns().get(0), logicalUpdateOp.getExpression());
    }

    private static PhysicalOperator handleDelete(DBManager dbManager, LogicalDeleteOperator logicalDeleteOp) throws DBException {
        PhysicalOperator scanner = generateOperator(dbManager, logicalDeleteOp.getChild());
        return new DeleteOperator(scanner, logicalDeleteOp.getTableName(), logicalDeleteOp.getExpression());
    }

    private static PhysicalOperator handleSort(DBManager dbManager, LogicalSortOperator sortOperator) throws DBException {
        PhysicalOperator inputOp = generateOperator(dbManager, sortOperator.getChild());
        return new SortOperator(inputOp, sortOperator.getOrderByElements(), sortOperator.getTable());
    }

    private static PhysicalOperator handleIndex(DBManager dbManager, LogicalCreateIndexOperator indexOperator) throws DBException {
        PhysicalOperator inputOp = generateOperator(dbManager, indexOperator.getChild());
        return new CreateIndexOperator(inputOp, indexOperator.getColumn(), indexOperator.getType());
    }
}
