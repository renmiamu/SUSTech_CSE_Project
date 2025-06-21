package edu.sustech.cs307.value;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import edu.sustech.cs307.exception.DBException;

import java.nio.ByteBuffer;

public class Value implements Comparable<Value> {
    public Object value;
    public ValueType type;
    public static final int INT_SIZE = 8;
    public static final int FLOAT_SIZE = 8;
    public static final int CHAR_SIZE = 64;
    @JsonCreator
    public Value(@JsonProperty("value")Object value,
                 @JsonProperty("type")ValueType type) {
        this.value = value;
        this.type = type;
    }

    public Value(Long value) {
        this.value = value;
        type = ValueType.INTEGER;
    }

    public Value(Double value) {
        this.value = value;
        type = ValueType.FLOAT;
    }

    public Value(String value) {
        this.value = value;
        type = ValueType.CHAR;
    }

    /**
     * 将当前值转换为字节数组。
     * 
     * @return 字节数组表示的值，根据值的类型（INTEGER、FLOAT、CHAR）进行转换。
     * @throws RuntimeException 如果值的类型不受支持。
     */
    public byte[] ToByte() {
        return switch (type) {
            case INTEGER -> {
                ByteBuffer buffer1 = ByteBuffer.allocate(8);
                buffer1.putLong((long) value);
                yield buffer1.array();
            }
            case FLOAT -> {
                ByteBuffer buffer2 = ByteBuffer.allocate(8);
                buffer2.putDouble((double) value);
                yield buffer2.array();
            }
            case CHAR -> {
                String str = (String) value;
                ByteBuffer buffer3 = ByteBuffer.allocate(64);
                buffer3.putInt(str.length());
                buffer3.put(str.getBytes());
                yield buffer3.array();
            }
            default -> throw new RuntimeException("Unsupported value type: " + type);
        };
    }

    /**
     * 根据给定的字节数组和值类型创建一个 Value 对象。
     *
     * @param bytes 字节数组，表示要转换的值。
     * @param type  值的类型，支持 INTEGER、FLOAT 和 CHAR。
     * @return 转换后的 Value 对象。
     * @throws RuntimeException 如果提供的值类型不受支持。
     */
    public static Value FromByte(byte[] bytes, ValueType type) {
        return switch (type) {
            case INTEGER -> {
                ByteBuffer buffer1 = ByteBuffer.wrap(bytes);
                yield new Value(buffer1.getLong());
            }
            case FLOAT -> {
                ByteBuffer buffer2 = ByteBuffer.wrap(bytes);
                yield new Value(buffer2.getDouble());
            }
            case CHAR -> {
                ByteBuffer buffer3 = ByteBuffer.wrap(bytes);
                var length = buffer3.getInt();
                // int is 4 byte
                String s = new String(bytes, 4, length);
                yield new Value(s);
            }
            default -> throw new RuntimeException("Unsupported value type: " + type);
        };

    }

    @Override
    public String toString() {
        switch (type) {
            case INTEGER, FLOAT ->{
                return this.value.toString();
            }
            case CHAR -> {
                byte[] bytes = ((String) this.value).getBytes();
                ByteBuffer buffer3 = ByteBuffer.wrap(bytes);
                var length = buffer3.getInt();
                if (length >= 64) return (String) this.value;
                // int is 4 byte
                return new String(bytes, 4, length);
            }
            default -> throw new RuntimeException("Unsupported value type: " + type);
        }
    }
    public ValueType getType(){
        return type;
    }
    @Override
    public int hashCode() {
        return switch (type) {
            case INTEGER -> Long.hashCode((Long) value);
            case FLOAT   -> Double.hashCode((Double) value);
            case CHAR    -> value.hashCode();   // String 自带良好 hash
            default      -> 0;
        };
    }
    @Override

    public boolean equals(Object obj) {
        if (this == obj) return true;
        Value other = (Value) obj;
        try {
            return ValueComparer.compare(this, other) == 0; // null-safe
        } catch (DBException e) {
            throw new RuntimeException(e);
        }
    }
    @Override
    public int compareTo(Value o) {
        try {
            Value v1 = formatValue(this);
            Value v2 = formatValue(o);
            return ValueComparer.compare(v1, v2);
        } catch (DBException e) {
            throw new RuntimeException(e);
        }
    }
    public static Value formatValue(Value o) {
        String s = o.value.toString();
        if (s.contains("_")) {
            String type = s.substring(0, s.indexOf('_'));
            String val = s.substring(s.indexOf('_') + 1);
            switch (type) {
                case "int" :
                    o = new Value(Long.parseLong(val), ValueType.INTEGER);
                    break;

                case "char" :
                    o = new Value(val, ValueType.CHAR);
                    break;

                case "float" :
                    o = new Value(Double.parseDouble(val), ValueType.FLOAT);
                    break;
            }
        }
        return o;
    }
}
