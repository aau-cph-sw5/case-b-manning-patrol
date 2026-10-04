import { useReducer, useState } from "react";
import { StyleSheet, Switch, Text, View } from "react-native";

import { SessionSlider } from "@/components/SessionSlider";
import { sessionReducer } from "@/state/sessionReducer";
import { initialSessionState } from "@/types/session";

// demo of the session slider: the real reducer drives it, only the server response is simulated.
// connecting the real api belongs to another ticket.
const SIMULATED_DELAY_MS = 1000;

export default function Index() {
  const [session, dispatch] = useReducer(sessionReducer, initialSessionState);
  const [simulateFailure, setSimulateFailure] = useState(false);

  async function handleStart() {
    // the moment the slide completes is the session's start time
    dispatch({ type: "START_REQUESTED", startedAt: Date.now() });
    try {
      await simulateRequest(simulateFailure);
      dispatch({ type: "START_SUCCEEDED" });
    } catch {
      dispatch({ type: "START_FAILED", error: "Could not start the session. Try again." });
    }
  }

  async function handleStop() {
    dispatch({ type: "STOP_REQUESTED" });
    try {
      await simulateRequest(simulateFailure);
      dispatch({ type: "STOP_SUCCEEDED" });
    } catch {
      dispatch({ type: "STOP_FAILED", error: "Could not stop the session. Try again." });
    }
  }

  return (
    <View style={styles.container}>
      <SessionSlider
        status={session.status}
        startedAt={session.startedAt}
        error={session.error}
        onStart={handleStart}
        onStop={handleStop}
      />
      <View style={styles.option}>
        <Text style={styles.optionLabel}>Simulate failure</Text>
        <Switch value={simulateFailure} onValueChange={setSimulateFailure} />
      </View>
    </View>
  );
}

// stands in for the server: answers after a delay, or fails when asked to
function simulateRequest(fail: boolean): Promise<void> {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      if (fail) {
        reject(new Error("simulated failure"));
      } else {
        resolve();
      }
    }, SIMULATED_DELAY_MS);
  });
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: "center",
    gap: 32,
    padding: 16,
    backgroundColor: "white",
  },
  option: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
  },
  optionLabel: {
    fontSize: 16,
  },
});
