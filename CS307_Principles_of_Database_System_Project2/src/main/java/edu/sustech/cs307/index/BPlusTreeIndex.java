package edu.sustech.cs307.index;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import edu.sustech.cs307.record.RID;
import edu.sustech.cs307.value.Value;
import edu.sustech.cs307.value.ValueType;
import org.pmw.tinylog.Logger;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.*;
import java.util.Map.Entry;

/**
 * BPlusTreeIndex — 基于内存 B+ 树的 PRIMARYKEY 索引实现，**不使用 mirror／descendingMap**，
 * 所有范围迭代均按键 **升序** 返回。<br/>
 * 设计假设：键唯一（主键约束）；若插入重复键需在更高层抛异常。
 */
public class BPlusTreeIndex implements Index {
    private final BPlusTree<Value, RID> tree;
    private final String persistPath;
    private final ObjectMapper objectMapper = new ObjectMapper();

    /** 默认阶数 128 的 B+ 树，不持久化 */
    public BPlusTreeIndex() {
        this(null, 128);
    }

    /** 指定持久化文件、阶数 */
    public BPlusTreeIndex(String persistPath, int branchingFactor) {
        this.persistPath = persistPath;
        this.tree = new BPlusTree<>(branchingFactor);
        // 若给了持久化路径，则尝试恢复
        if (persistPath != null) {
            try {
                File file = new File(persistPath);
                if (file.exists()) {
                    TypeReference<TreeMap<Value, RID>> typeRef = new TypeReference<>() {
                    };
                    TreeMap<Value, RID> map = objectMapper.readValue(file, typeRef);
                    map.forEach(this::insert);
                    //System.out.println(tree.toString());
                }
            } catch (IOException e) {
                Logger.error("[BPlusTreeIndex] restore failed: " + e.getMessage());
            }
        }
    }

    /** 方便与旧实现保持一致的构造 —— 只给持久化路径，阶数用默认值 */
    public BPlusTreeIndex(String persistPath) {
        this(persistPath, 128);
    }


    @Override
    public RID EqualTo(Value value) {
        return tree.search(value);
    }

    @Override
    public Iterator<Entry<Value, RID>> LessThan(Value key, boolean inclusive) {
        Value minSentinel = new Value(Long.MIN_VALUE); // 假定系统最小值；若值域不同请替换
        List<Entry<Value, RID>> list = tree.searchRange(minSentinel, BPlusTree.RangePolicy.EXCLUSIVE,
                key, inclusive ? BPlusTree.RangePolicy.INCLUSIVE : BPlusTree.RangePolicy.EXCLUSIVE);
        return list.iterator();
    }

    @Override
    public Iterator<Entry<Value, RID>> MoreThan(Value key, boolean inclusive) {
        Value maxSentinel = new Value(Long.MAX_VALUE); // 假定系统最大值；若值域不同请替换
        List<Entry<Value, RID>> list = tree.searchRange(key, inclusive ? BPlusTree.RangePolicy.INCLUSIVE : BPlusTree.RangePolicy.EXCLUSIVE,
                maxSentinel, BPlusTree.RangePolicy.EXCLUSIVE);
        return list.iterator();
    }

    @Override
    public Iterator<Entry<Value, RID>> Range(Value low, Value high, boolean leftInclusive, boolean rightInclusive) {
        List<Entry<Value, RID>> list = tree.searchRange(low,
                leftInclusive ? BPlusTree.RangePolicy.INCLUSIVE : BPlusTree.RangePolicy.EXCLUSIVE,
                high,
                rightInclusive ? BPlusTree.RangePolicy.INCLUSIVE : BPlusTree.RangePolicy.EXCLUSIVE);
        return list.iterator();
    }

    @Override
    public void SaveIndexes(String persistPath, Map<Value, RID> map) {
        if (!new File(persistPath).exists()) {
            // create it
            try {
                new File(persistPath).createNewFile();
            } catch (IOException e) {
                throw new RuntimeException(e);
            }

        }
        try (FileWriter writer = new FileWriter(persistPath)) {
            for (Map.Entry<Value, RID> entry : map.entrySet()) {
                String key = entry.getKey().type + "_";
                if (entry.getKey().type == ValueType.CHAR) {
                    String val = (String)entry.getKey().value;
                    if (val.contains("\b")) val = val.substring(val.indexOf("\b") + 1);
                    key += val.trim();
                } else key += entry.getKey().value.toString();
                tree.insert(new Value(key), entry.getValue());
            }
            objectMapper.writeValue(writer, tree.toMap());
        } catch (IOException e) {
            Logger.error("Error saving index data: " + e.getMessage());
        }
    }

    /** 插入新键 —— 供上层 InsertOperator 调用 */
    public void insert(Value key, RID rid) {
        tree.insert(key, rid);
        try (FileWriter writer = new FileWriter(persistPath)) {
            objectMapper.writeValue(writer, tree.toMap());
        } catch (IOException e) {
            Logger.error("Error saving index data: " + e.getMessage());
        }
    }

    /** 删除键 —— 供 Delete/Update 调用 */
    public void delete(Value key) {
        tree.delete(key);
        try (FileWriter writer = new FileWriter(persistPath)) {
            objectMapper.writeValue(writer, tree.toMap());
        } catch (IOException e) {
            Logger.error("Error saving index data: " + e.getMessage());
        }
    }
}
