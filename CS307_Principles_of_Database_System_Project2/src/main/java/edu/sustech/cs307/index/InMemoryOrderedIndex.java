package edu.sustech.cs307.index;

import edu.sustech.cs307.exception.DBException;
import edu.sustech.cs307.record.RID;
import edu.sustech.cs307.value.Value;

import java.io.FileWriter;
import java.util.Map;
import java.util.TreeMap;

import edu.sustech.cs307.value.ValueComparer;
import edu.sustech.cs307.value.ValueType;
import org.pmw.tinylog.Logger;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.File;
import java.io.IOException;
import java.util.Iterator;
import java.util.Map.Entry;
import java.util.NavigableMap;

public class InMemoryOrderedIndex implements Index {

    private TreeMap<Value, RID> indexMap;
    private ObjectMapper objectMapper;

    public InMemoryOrderedIndex(String persistPath) {
        // read from persistPath
        try {
            File file = new File(persistPath);
            objectMapper = new ObjectMapper();
            if (file.exists()) {
                TypeReference<TreeMap<Value, RID>> typeRef = new TypeReference<>() {
                };
                TreeMap<Value, RID> map = objectMapper.readValue(file, typeRef);
                this.indexMap = new TreeMap<>();
                for (Entry<Value, RID> entry : map.entrySet()) {
                    Value val = Value.formatValue(entry.getKey());
                    indexMap.put(val, entry.getValue());
                }

            }
        } catch (IOException e) {
            Logger.error("Error loading index data: " + e.getMessage());
        }
    }

    @Override
    public RID EqualTo(Value value) {
        if (value.type == ValueType.CHAR){
            for (Entry<Value, RID> entry : indexMap.entrySet()) {
                String key = entry.getKey().toString();
                String target = (String)value.value;
                if (key.equals(target)) return entry.getValue();
            }
            return null;
        } else return indexMap.getOrDefault(value, null);
    }

    /**
     * 返回一个迭代器，该迭代器用于遍历所有严格小于给定值的条目。
     * 
     * @param value 要比较的值
     * @return 一个迭代器，按从大到小的顺序遍历所有严格小于给定值的条目
     */
    @Override
    public Iterator<Entry<Value, RID>> LessThan(Value value, boolean isEqual) {
        // 获取严格小于value的所有条目视图
        NavigableMap<Value, RID> subMap = indexMap.headMap(value, false);

        // 使用descendingMap获取从大到小的迭代器
        return subMap.descendingMap().entrySet().iterator();
    }

    /**
     * 返回一个迭代器，遍历所有严格大于给定值的条目。
     *
     * @param value 要比较的值
     * @return 一个迭代器，包含所有严格大于指定值的条目
     */
    @Override
    public Iterator<Entry<Value, RID>> MoreThan(Value value, boolean isEqual) {
        // 获取严格大于value的所有条目视图
        NavigableMap<Value, RID> subMap = indexMap.tailMap(value, false);
        return subMap.entrySet().iterator();
    }

    /**
     * 返回指定范围内的条目迭代器。
     * 
     * @param low        范围的下界
     * @param high       范围的上界
     * @param leftEqual  是否包含下界
     * @param rightEqual 是否包含上界
     * @return 指定范围内条目的迭代器
     */
    @Override
    public Iterator<Entry<Value, RID>> Range(Value low, Value high, boolean leftEqual, boolean rightEqual) {
        // 获取范围视图（左闭右开）
        NavigableMap<Value, RID> subMap = indexMap.subMap(
                low, leftEqual,
                high, rightEqual);

        return subMap.entrySet().iterator();
    }

    @Override
    public void SaveIndexes(String path, Map<Value, RID> map) {
        if (!new File(path).exists()) {
            // create it
            try {
                new File(path).createNewFile();
            } catch (IOException e) {
                throw new RuntimeException(e);
            }

        }
        try (FileWriter writer = new FileWriter(path)) {
            TreeMap<String, RID> stringKeyMap = new TreeMap<>();
            for (Map.Entry<Value, RID> entry : map.entrySet()) {
                String key = entry.getKey().type + "_" + entry.getKey().value.toString();
                stringKeyMap.put(key, entry.getValue());
            }
            objectMapper.writeValue(writer, stringKeyMap);
        } catch (IOException e) {
            Logger.error("Error saving index data: " + e.getMessage());
        }
    }
}
