import EventSource from "react-native-sse";
import { StationOverviewSchema, type StationOverview } from "@/types/station";

// the dashboard stream of the positioning-interface contract, served by the
// same API as the POST endpoints.
const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";
const SSE_URL = `${API_BASE_URL}/api/v2/dashboard/stream`;

//Connection to SSE with actions acceptable are open, dashboard and error
export function connectToStationUpdates(
    onUpdate: (data: StationOverview) => void,
    onError: (error: unknown) => void,
) {
    // the type parameter names the custom event the backend sends, so the
    // dashboard listener receives it with a typed data field.
    const source = new EventSource<"dashboard">(SSE_URL);


    source.addEventListener("open", () => {
        console.log("SSE connection opened");
    });

    source.addEventListener("dashboard", (event) => {
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
