package edu.sustech.cs307.physicalOperator;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import edu.sustech.cs307.exception.DBException;
import edu.sustech.cs307.exception.ExceptionTypes;
import edu.sustech.cs307.index.BPlusTreeIndex;
import edu.sustech.cs307.index.InMemoryOrderedIndex;
import edu.sustech.cs307.index.Index;
import edu.sustech.cs307.meta.ColumnMeta;
import edu.sustech.cs307.meta.MetaManager;
import edu.sustech.cs307.meta.TabCol;
import edu.sustech.cs307.meta.TableMeta;
import edu.sustech.cs307.record.RID;
import edu.sustech.cs307.record.RecordFileHandle;
import edu.sustech.cs307.tuple.TableTuple;
import edu.sustech.cs307.tuple.TempTuple;
import edu.sustech.cs307.tuple.Tuple;
import edu.sustech.cs307.value.Value;
import edu.sustech.cs307.value.ValueType;
import org.pmw.tinylog.Logger;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.Writer;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import java.util.TreeMap;

public class CreateIndexOperator implements PhysicalOperator {
    private static final String ROOT_DIR = "CS307-DB/meta";
    private final SeqScanOperator seqScanOperator;
    private final String column;          // column to index (raw name, no table prefix)
    private final TableMeta.IndexType type;
    private TableMeta tableMeta;
    private Index indexImpl;              // concrete index instance
    private boolean finished = false;
    private Map<Value, RID> map;

    public CreateIndexOperator(PhysicalOperator inputOperator, String column, TableMeta.IndexType type) {
        if (!(inputOperator instanceof SeqScanOperator seqScanOperator)) {
            throw new RuntimeException("The delete operator only accepts SeqScanOperator as input");
        }
        this.seqScanOperator = seqScanOperator;
        this.column = column;
        this.type = type;
        tableMeta = seqScanOperator.getTableMeta();
        map = new HashMap<>();
    }

    @Override
    public boolean hasNext() throws DBException {
        return !finished;
    }

    @Override
    public void Begin() throws DBException {
        String persistPath = ROOT_DIR + "/" + tableMeta.getTableName()
                + "_" + column + "_" + type + ".json";

        switch (type) {
            case InMemoryOrdered -> indexImpl = new InMemoryOrderedIndex(persistPath);
            case BTREE           -> indexImpl = new BPlusTreeIndex(persistPath);
            default              -> throw new IllegalStateException("Unknown IndexType " + type);
        }

        // 2) full table scan, insert every <value,RID>
        seqScanOperator.Begin();
        RecordFileHandle fileHandle = seqScanOperator.getFileHandle();
        while (seqScanOperator.hasNext()) {
            seqScanOperator.Next();
            TableTuple tuple = (TableTuple) seqScanOperator.Current();

            Value v = tuple.getValue(new TabCol(tuple.getTableName(), column));
            if (map.containsKey(v)) {
                throw new DBException(ExceptionTypes.DuplicatedIndex(v.toString()));
            }
            RID rid = tuple.getRID();
            if (rid.pageNum < 0 || rid.slotNum < 0 ) System.out.println(rid.slotNum);

            map.put(v, rid);
        }
        tableMeta.getIndexes().put(column, type);
        MetaManager metaManager = seqScanOperator.getMetaManager();
        metaManager.saveToJson();
        indexImpl.SaveIndexes(persistPath, map);

        finished = true;
    }
    @Override
    public void Next() throws DBException {
        finished = true;
    }

    @Override
    public Tuple Current() {
        if (finished) {
            ArrayList<Value> result = new ArrayList<>();
            result.add(new Value("Index Created", ValueType.CHAR));
            return new TempTuple(result);
        } else {
            throw new RuntimeException("Error occured");
        }
    }

    @Override
    public void Close() {
        seqScanOperator.Close();
    }

    @Override
    public ArrayList<ColumnMeta> outputSchema() {
        ArrayList<ColumnMeta> schema = new ArrayList<>();
        schema.add(new ColumnMeta("Index Created", "", ValueType.INTEGER, 0, 0));
        return schema;
    }
}
