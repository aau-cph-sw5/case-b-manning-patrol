import EventSource from "react-native-sse";
import { StationOverviewSchema, type StationOverview } from "@/types/station";
const SSE_URL = "testUrl"

//Connection to SSE with actions acceptable are open, message and error
export function connectToStationUpdates(
    onUpdate: (data: StationOverview) => void,
    onError: (error: unknown) => void,
) {
    const source = new EventSource(SSE_URL);


    source.addEventListener("open", () => {
        console.log("SSE connection opened");
    });

    source.addEventListener("message", (event) => {
        if (event.data === null) {
            return;
        }
        try {
            // SSE delivers event.data as a raw JSON string, so parse before zod.
            const extractedData = StationOverviewSchema.parse(JSON.parse(event.data));
            onUpdate(extractedData);
        } catch (error) {
            onError(error);
        }
    });

    source.addEventListener("error", (event) => {
        onError(event);
    });

    return () => {
        source.close();
    };
}
