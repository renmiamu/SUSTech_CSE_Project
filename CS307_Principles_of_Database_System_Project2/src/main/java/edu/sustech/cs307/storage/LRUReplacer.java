package edu.sustech.cs307.storage;

import java.util.*;

public class LRUReplacer {
    private final int maxSize;
    private final Set<Integer> pinnedFrames = new HashSet<>();
    private final Set<Integer> LRUHash = new HashSet<>();
    private final LinkedList<Integer> LRUList = new LinkedList<>();

    public LRUReplacer(int numPages) {
        this.maxSize = numPages;
    }

    public int Victim() {
        if (!LRUList.isEmpty()) return LRUList.removeFirst();
        else return -1;
    }

    public void Pin(int frameId) {
        if (pinnedFrames.contains(frameId)) return;

        if (LRUHash.contains(frameId)) {
            LRUList.remove(Integer.valueOf(frameId));
            LRUHash.remove(frameId);
        }

        pinnedFrames.add(frameId);
        if (size() > maxSize) throw new RuntimeException("REPLACER IS FULL");
    }


    public void Unpin(int frameId) {
        if (pinnedFrames.contains(frameId)){
            pinnedFrames.remove(frameId);
            LRUHash.add(frameId);
            LRUList.add(frameId);
        }
        else throw new RuntimeException("UNPIN PAGE NOT FOUND");
    }


    public int size() {
        return LRUList.size() + pinnedFrames.size();
    }
}