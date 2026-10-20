import { useEffect, useState } from "react";
import { connectToStationUpdates } from "../api/stationEventStream";

export function StationScreen() {
    const [stationData, setStationData] = useState<string[]>([]);

    useEffect(() => {
        const disconnect = connectToStationUpdates(
        (data) => {
            console.log("Received station update:", data);

            setStationData((currentData) => [
                ...currentData, data,
            ])
            //Add handling of data here
        },
        (error) => {
            console.error("SSE error:", error);
            //Add error handling here
        },
        );
        //Calls the disconnect function when done with useeffect
        return () => {
        disconnect();
        };
    }, []);

    return null;
}

interface Area {
    type: string
    lastConnected: Date
    status: string
    timeTillOverdue: Date
    line: string
}

interface Station {
    name: string
    areas: Area[]
}

interface StationOverview {
    stations: Station[]
}

function extractData(data: StationOverview) {

}