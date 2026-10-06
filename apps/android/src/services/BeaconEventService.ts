import { useMemo } from "react";
import { createBeaconScanner } from "./beacon/CreateBeaconScanner";
import { BeaconConnectionEvent } from "@/types/beacon";
import { postConnectionEvent } from "@/api/postConnectionEvent";

export function BeaconEventService() {
    const scanner = useMemo(() => createBeaconScanner(), []);

    scanner.start((event: BeaconConnectionEvent) =>{
        //postConnectionEvent(event);
        
        throw new Error("Not implemented yet.")
    })
    return scanner;
}

