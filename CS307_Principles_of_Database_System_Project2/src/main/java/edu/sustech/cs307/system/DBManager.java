package edu.sustech.cs307.system;

import edu.sustech.cs307.exception.DBException;
import edu.sustech.cs307.exception.ExceptionTypes;
import edu.sustech.cs307.meta.ColumnMeta;
import edu.sustech.cs307.meta.MetaManager;
import edu.sustech.cs307.meta.TableMeta;
import edu.sustech.cs307.storage.BufferPool;
import edu.sustech.cs307.storage.DiskManager;
import edu.sustech.cs307.value.ValueType;
import net.sf.jsqlparser.schema.Table;
import org.apache.commons.lang3.StringUtils;
import org.pmw.tinylog.Logger;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.Map;
import java.util.Set;

public class DBManager {
    private final MetaManager metaManager;
    /* --- --- --- */
    private final DiskManager diskManager;
    private final BufferPool bufferPool;
    private final RecordManager recordManager;

    public DBManager(DiskManager diskManager, BufferPool bufferPool, RecordManager recordManager,
            MetaManager metaManager) {
        this.diskManager = diskManager;
        this.bufferPool = bufferPool;
        this.recordManager = recordManager;
        this.metaManager = metaManager;
    }

    public BufferPool getBufferPool() {
        return bufferPool;
    }

    public RecordManager getRecordManager() {
        return recordManager;
    }

    public DiskManager getDiskManager() {
        return diskManager;
    }

    public MetaManager getMetaManager() {
        return metaManager;
    }

    public boolean isDirExists(String dir) {
        File file = new File(dir);
        return file.exists() && file.isDirectory();
    }

    /**
     * Displays a formatted table listing all available tables in the database.
     * The output is presented in a bordered ASCII table format with centered table
     * names.
     * Each table name is displayed in a separate row within the ASCII borders.
     */
    public void showTables() {
        Set<String> names = metaManager.getTableNames();
        int maxLength = "Tables".length();
        for (String name : names) {
            maxLength = Math.max(maxLength, name.length());
        }
        String horizontal = "-".repeat(maxLength + 4);
        horizontal = "|" + horizontal + "|";
        Logger.info(horizontal);
        Logger.info(center("tabels", maxLength));
        Logger.info(horizontal);
        for (String name : names){
            Logger.info(center(name, maxLength));
            Logger.info(horizontal);
        }

    }
    private String center(String name, int width){
        int padding = width - name.length();
        int front = (padding)/2 + 2;
        int end = padding - front + 4;
        return "|" + " ".repeat(front) + name + " ".repeat(end) + "|";
    }

    public void descTable(String table_name) throws DBException {
        TableMeta tableMeta = metaManager.getTable(table_name);
        int column1 = "Field".length();
        int column2 = "Type".length();
        for (int i = 0; i < tableMeta.columnCount(); i++) {
            ColumnMeta column = tableMeta.columns_list.get(i);
            String name = column.name;
            String type = column.type.toString();
            column1 = Math.max(column1, name.length());
            column2 = Math.max(column2, type.length());
        }
        String horizontal = "-".repeat(4 + column1 + 1 + column2 + 4);
        horizontal = "|" + horizontal + "|";
        String content = center("Field", column1);
        content = content.substring(0,content.length() - 1) + center("Type", column2);
        Logger.info(horizontal);
        Logger.info(content);
        for (int i = 0; i < tableMeta.columnCount(); i++) {
            ColumnMeta column = tableMeta.columns_list.get(i);
            String name = column.name;
            String type = column.type.toString();
            content = center(name, column1);
            content = content.substring(0,content.length() - 1) + center(type, column2);
            Logger.info(content);
        }
        Logger.info(horizontal);
    }

    /**
     * Creates a new table in the database with specified name and column metadata.
     * This method sets up both the table metadata and the physical storage
     * structure.
     *
     * @param table_name The name of the table to be created
     * @param columns    List of column metadata defining the table structure
     * @throws DBException If there is an error during table creation
     */
    public void createTable(String table_name, ArrayList<ColumnMeta> columns) throws DBException {
        TableMeta tableMeta = new TableMeta(
                table_name, columns);
        metaManager.createTable(tableMeta);
        String table_folder = String.format("%s/%s", diskManager.getCurrentDir(), table_name);
        File file_folder = new File(table_folder);
        if (!file_folder.exists()) {
            file_folder.mkdirs();
        }
        int record_size = 0;
        for (var col : columns) {
            record_size += col.len;
        }
        String data_file = String.format("%s/%s", table_name, "data");
        recordManager.CreateFile(data_file, record_size);
    }

    /**
     * Drops a table from the database by removing its metadata and associated
     * files.
     * 
     * @param table_name The name of the table to be dropped
     * @throws DBException If the table directory does not exist or encounters IO
     *                     errors during deletion
     */
    public void dropTable(String table_name) throws DBException {
//        if (!isDirExists(table_name)) throw new DBException(ExceptionTypes.BadIOError("" +
//                "Does not exists table " + table_name));
        // todo: finish drop table method
        String table_folder = String.format("%s/%s", diskManager.getCurrentDir(), table_name);
        File file_folder = new File(table_folder);
        deleteDirectory(file_folder);
        TableMeta meta = metaManager.getTable(table_name);
        for (String s : meta.getIndexesList()){
            dropIndex(table_name, s);
        }
        metaManager.dropTable(table_name);
    }

    /**
     * Recursively deletes a directory and all its contents.
     * If the given file is a directory, it first deletes all its entries
     * recursively.
     * Finally deletes the file/directory itself.
     *
     * @param file The file or directory to be deleted
     * @throws IOException If deletion of any file or directory fails
     */
    private void deleteDirectory(File file) throws DBException {
        if (file.isDirectory()) {
            File[] entries = file.listFiles();
            if (entries != null) {
                for (File entry : entries) {
                    deleteDirectory(entry);
                }
            }
        }
        if (!file.delete()) {
            throw new DBException(ExceptionTypes.BadIOError("File deletion failed: " + file.getAbsolutePath()));
        }
    }

    /**
     * Checks if a table exists in the database.
     *
     * @param table the name of the table to check
     * @return true if the table exists, false otherwise
     */
    public boolean isTableExists(String table) {
        return metaManager.getTableNames().contains(table);
    }

    /**
     * Closes the database manager and performs cleanup operations.
     * This method flushes all pages in the buffer pool, dumps disk manager
     * metadata,
     * and saves meta manager state to JSON format.
     *
     * @throws DBException if an error occurs during the closing process
     */
    public void closeDBManager() throws DBException {
        this.bufferPool.FlushAllPages("");
        DiskManager.dump_disk_manager_meta(this.diskManager);
        this.metaManager.saveToJson();
    }
    public void dropIndex(String tableName, String indexName) throws DBException {
        TableMeta tableMeta = metaManager.getTable(tableName);
        tableMeta.getIndexes().remove(indexName);
        metaManager.saveToJson();
        String path1 = "CS307-DB/meta/" + tableName + "_" + indexName + "_" +
                "InMemoryOrdered" + ".json";
        String path2 = "CS307-DB/meta/" + tableName + "_" + indexName + "_" +
                "BTREE" + ".json";
        try{
            File file1 = new File(path1);
            File file2 = new File(path2);
            file1.delete();
            file2.delete();
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }
}
