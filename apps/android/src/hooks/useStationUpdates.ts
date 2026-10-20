import { useEffect, useState } from "react";
import { connectToStationUpdates } from "../api/stationEventStream";
import { Station, type StationOverview } from "../types/station/station";

export function StationScreen() {
    const [stationData, setStationData] = useState<StationOverview>();

    useEffect(() => {
        const disconnect = connectToStationUpdates(
        (data) => {
            console.log("Received station update:", data);

            setStationData(data);
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

