package edu.sustech.cs307;

import edu.sustech.cs307.exception.DBException;
import edu.sustech.cs307.meta.MetaManager;
import edu.sustech.cs307.meta.TableMeta;
import edu.sustech.cs307.record.BitMap;
import edu.sustech.cs307.record.RID;
import edu.sustech.cs307.record.Record;
import edu.sustech.cs307.record.RecordFileHandle;
import edu.sustech.cs307.record.RecordPageHandle;
import edu.sustech.cs307.storage.BufferPool;
import edu.sustech.cs307.storage.DiskManager;
import edu.sustech.cs307.system.DBManager;
import edu.sustech.cs307.system.RecordManager;
import edu.sustech.cs307.tuple.TableTuple;
import edu.sustech.cs307.value.Value;
import org.pmw.tinylog.Logger;

import java.util.HashMap;
import java.util.Map;

public class Exercise {
    public static void main(String[] args) {
        try {
            Map<String, Integer> disk_manager_meta = new HashMap<>(DiskManager.read_disk_manager_meta());
            DiskManager diskManager = new DiskManager("CS307-DB", disk_manager_meta);
            BufferPool bufferPool = new BufferPool(256 * 512, diskManager);
            RecordManager recordManager = new RecordManager(diskManager, bufferPool);
            MetaManager metaManager = new MetaManager("CS307-DB" + "/meta");
            DBManager dbManager = new DBManager(diskManager, bufferPool, recordManager, metaManager);

            RecordFileHandle fileHandle = dbManager.getRecordManager().OpenFile("t");
            int pageCount = fileHandle.getFileHeader().getNumberOfPages();
            int recordsCount = fileHandle.getFileHeader().getNumberOfRecordsPrePage();

            int currentPageNum = 1;
            int currentSlotNum = 0;

            if (currentPageNum <= pageCount) {
                while (currentPageNum <= pageCount) {
                    RecordPageHandle pageHandle = fileHandle.FetchPageHandle(currentPageNum);
                    while (currentSlotNum < recordsCount) {
                        if (BitMap.isSet(pageHandle.bitmap, currentSlotNum)) {
                            // Found next record
                            RID id = new RID(currentPageNum, currentSlotNum);
                            Record record = fileHandle.GetRecord(id);
                            currentSlotNum ++;
                            if (currentSlotNum > recordsCount) {
                                currentSlotNum = 0;
                                currentPageNum ++;
                            }
                            fileHandle.UnpinPageHandle(currentPageNum, false);
                            TableMeta meta = metaManager.getTable("t");
                            TableTuple tuple = new TableTuple("t", meta, record, id);
                            Value[] values = tuple.getValues();
                            System.out.print("Page " + pageCount + " Slot " + currentSlotNum +
                                    " is set. Values: ");
                            for (Value value : values) {
                                System.out.print(value.toString() + ", ");
                            }
                            System.out.println();
                        }
                    }
                    currentPageNum++;
                    currentSlotNum = 0; // Reset slot num for new page
                }
            }


        } catch (DBException e) {
            Logger.error(e.getMessage());
            Logger.error("An error occurred during initializing. Exiting....");
        }
    }
}
