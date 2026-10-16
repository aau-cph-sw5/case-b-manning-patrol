import EventSource from "react-native-sse";

const SSE_URL = "testUrl"

//Connection to SSE with actions acceptable are open, message and error
export function connectToStationUpdates(
    onUpdate: (data: string) => void,
    onError: (error: unknown) => void,
) {
    const source = new EventSource(SSE_URL);


    source.addEventListener("open", () => {
    console.log("SSE connection opened");
  });

  source.addEventListener("message", (event) => {
    if (event.data !== null) {
      onUpdate(event.data);
    }
  });

  source.addEventListener("error", (event) => {
    onError(event);
  });
  
    return () => {
        source.close();
    };
}