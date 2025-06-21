package edu.sustech.cs307.tuple;

import edu.sustech.cs307.exception.DBException;
import edu.sustech.cs307.exception.ExceptionTypes;
import edu.sustech.cs307.meta.TabCol;
import edu.sustech.cs307.value.Value;
import edu.sustech.cs307.value.ValueComparer;
import edu.sustech.cs307.value.ValueType;
import net.sf.jsqlparser.expression.*;
import net.sf.jsqlparser.expression.operators.conditional.AndExpression;
import net.sf.jsqlparser.expression.operators.conditional.OrExpression;
import net.sf.jsqlparser.expression.operators.relational.Between;
import net.sf.jsqlparser.expression.operators.relational.InExpression;
import net.sf.jsqlparser.expression.operators.relational.ParenthesedExpressionList;
import net.sf.jsqlparser.schema.Column;

import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public abstract class Tuple {
    public abstract Value getValue(TabCol tabCol) throws DBException;

    public abstract TabCol[] getTupleSchema();

    public abstract Value[] getValues() throws DBException;

    public boolean eval_expr(Expression expr) throws DBException {
        return evaluateCondition(this, expr);
    }

    private boolean evaluateCondition(Tuple tuple, Expression whereExpr) throws DBException {
        //todo: add Or condition
        if (whereExpr instanceof AndExpression andExpr) {
            // Recursively evaluate left and right expressions
            return evaluateCondition(tuple, andExpr.getLeftExpression())
                    && evaluateCondition(tuple, andExpr.getRightExpression());
        } else if (whereExpr instanceof OrExpression orExpression) {
            return evaluateCondition(tuple, orExpression.getLeftExpression())
                    || evaluateCondition(tuple, orExpression.getRightExpression());
        } else if (whereExpr instanceof BinaryExpression binaryExpression) {
            return evaluateBinaryExpression(tuple, binaryExpression);
        } else if (whereExpr instanceof InExpression inExpression) {
            return evaluateInExpression(tuple, inExpression);
        } else if (whereExpr instanceof Between between) {
            return evaluateBetween(tuple, between);
        } else {
            return true; // For non-binary and non-AND expressions, just return true for now
        }
    }

    private boolean evaluateBetween(Tuple tuple, Between between) throws DBException {
        Expression leftExpr = between.getLeftExpression();
        Expression start = between.getBetweenExpressionStart();
        Expression end = between.getBetweenExpressionEnd();
        String columnName = leftExpr.toString();
        TabCol[] tabCols = tuple.getTupleSchema();
        Value val = null;
        for (int i = 0; i < tabCols.length; i++) {
            String colName = tabCols[i].getColumnName().toLowerCase();
            if (leftExpr.toString().toLowerCase().equals(colName)) {
                val = tuple.getValue(tabCols[i]);
            }
        }
        ValueType type = val.getType();
        Value left = null;
        Value right = null;
        switch (type) {
            case INTEGER :
                left = new Value(Long.parseLong(start.toString()));
                right = new Value(Long.parseLong(end.toString()));
                break;

            case FLOAT :
                left = new Value(Double.parseDouble(start.toString()));
                right = new Value(Double.parseDouble(end.toString()));
                break;

            case CHAR :
                return false;
        }
        //左闭右开
        if (ValueComparer.compare(val,left) >= 0 &&
                ValueComparer.compare(right, val) > 0) return true;
        return false;
    }

    private boolean evaluateInExpression(Tuple tuple, InExpression inExpression) throws DBException {
        boolean contains = false;
        Expression leftExpr = inExpression.getLeftExpression();
        ParenthesedExpressionList<Expression> exprList =
                (ParenthesedExpressionList<Expression>) inExpression.getRightExpression();
        TabCol[] tabCols = tuple.getTupleSchema();
        String left = "";
        for (int i = 0; i < tabCols.length; i++) {
            String colName = tabCols[i].getColumnName().toLowerCase();
            if (leftExpr.toString().toLowerCase().equals(colName)) {
                left = tuple.getValue(tabCols[i]).toString().toLowerCase();
            }
        }
        for (Expression expr : exprList) {
            if (expr.toString().toLowerCase().equals(left)) contains = true;
        }
        return inExpression.isNot() ? !contains : contains;
    }
    private boolean evaluateBinaryExpression(Tuple tuple, BinaryExpression binaryExpr) {
        Expression leftExpr = binaryExpr.getLeftExpression();
        Expression rightExpr = binaryExpr.getRightExpression();
        String operator = binaryExpr.getStringExpression();
        Value leftValue = null;
        Value rightValue = null;


        try {
            if (leftExpr instanceof Column leftColumn) {
                String table_name = leftColumn.getTableName();
                if (tuple instanceof TableTuple) {
                    TableTuple tableTuple = (TableTuple) tuple;
                    table_name = tableTuple.getTableName();
                }
                leftValue = tuple.getValue(new TabCol(table_name, leftColumn.getColumnName()));
                if (leftValue.type == ValueType.CHAR) {
                    leftValue = new Value(leftValue.toString());
                }
            } else {
                leftValue = getConstantValue(leftExpr); // Handle constant left value
            }

            if (rightExpr instanceof Column rightColumn) {
                rightValue = tuple.getValue(new TabCol(rightColumn.getTableName(), rightColumn.getColumnName()));
            } else {
                rightValue = getConstantValue(rightExpr); // Handle constant right value

            }

            if (leftValue == null || rightValue == null)
                return false;

            int comparisonResult = ValueComparer.compare(leftValue, rightValue);
            if (operator.equals("=")) {
                return comparisonResult == 0;
            } else if (operator.equals(">")) {
                return comparisonResult == 1;
            } else if (operator.equals("<")) {
                return comparisonResult == -1;
            } else if (operator.equals(">=")) {
                return comparisonResult >= 0;
            } else if (operator.equals("<=")) {
                return comparisonResult <= 0;
            }
            // todo: finish condition > < >= <=

        } catch (DBException e) {
            e.printStackTrace(); // Handle exception properly
        }
        return false;
    }

    private Value getConstantValue(Expression expr) {
        if (expr instanceof StringValue) {
            return new Value(((StringValue) expr).getValue(), ValueType.CHAR);
        } else if (expr instanceof DoubleValue) {
            return new Value(((DoubleValue) expr).getValue(), ValueType.FLOAT);
        } else if (expr instanceof LongValue) {
            return new Value(((LongValue) expr).getValue(), ValueType.INTEGER);
        }
        return null; // Unsupported constant type
    }

    public Value evaluateExpression(Expression expr) throws DBException {
        if (expr instanceof StringValue) {
            return new Value(((StringValue) expr).getValue(), ValueType.CHAR);
        } else if (expr instanceof DoubleValue) {
            return new Value(((DoubleValue) expr).getValue(), ValueType.FLOAT);
        } else if (expr instanceof LongValue) {
            return new Value(((LongValue) expr).getValue(), ValueType.INTEGER);
        } else if (expr instanceof Column) {
            Column col = (Column) expr;
            return getValue(new TabCol(col.getTableName(), col.getColumnName()));
        } else {
            throw new DBException(ExceptionTypes.UnsupportedExpression(expr));
        }
    }

}
