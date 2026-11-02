import type { Record, RecordList } from "@/types/patrol_records/record";

export function splitRecords(records: Record[]): {open: Record[], closed: Record[]} {
    const open: Record[] = [];
    const closed: Record[] = [];

    for (const record of records){
        if (record.status === "open"){
            open.push(record);
        } else {
            closed.push(record);
        }
    }
    return {open, closed};
}