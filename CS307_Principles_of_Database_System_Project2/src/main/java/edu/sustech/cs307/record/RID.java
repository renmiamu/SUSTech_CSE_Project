package edu.sustech.cs307.record;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

public class RID {
    public int pageNum;
    public int slotNum;
    @JsonCreator
    public RID(@JsonProperty("pageNum") int pageNum,
               @JsonProperty("slotNum") int slotNum) {
        this.pageNum = pageNum;
        this.slotNum = slotNum;
    }

    public RID(RID rid) {
        this.pageNum = rid.pageNum;
        this.slotNum = rid.slotNum;
    }
}
