import { useReducer, useState } from "react";
import { StyleSheet, Switch, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { SessionButton } from "@/components/SessionButton";
import { sessionReducer } from "@/state/sessionReducer";
import { initialSessionState } from "@/types/session";

// demo of the session button: the real reducer drives it, only the server response is simulated.
// connecting the real api belongs to another ticket.
const SIMULATED_DELAY_MS = 1000;

export default function Index() {
  const [session, dispatch] = useReducer(sessionReducer, initialSessionState);
  const [simulateFailure, setSimulateFailure] = useState(false);

  async function startSession() {
    dispatch({ type: "START_REQUESTED" });
    try {
      await simulateRequest(simulateFailure);
      // the session counts from the moment it is confirmed, so the timer starts at 00:00:00
      dispatch({ type: "START_SUCCEEDED", startedAt: Date.now() });
    } catch {
      dispatch({ type: "START_FAILED", error: "Could not start the session. Try again." });
    }
  }

  async function stopSession() {
    dispatch({ type: "STOP_REQUESTED" });
    try {
      await simulateRequest(simulateFailure);
      dispatch({ type: "STOP_SUCCEEDED" });
    } catch {
      dispatch({ type: "STOP_FAILED", error: "Could not stop the session. Try again." });
    }
  }

  // the button is disabled while a request is in flight, so only "stopped" and "active" get here
  function handlePress() {
    if (session.status === "stopped") {
      void startSession();
    } else if (session.status === "active") {
      void stopSession();
    }
  }

  return (
    <SafeAreaView style={styles.screen} edges={["bottom"]}>
      <View style={styles.option}>
        <Text style={styles.optionLabel}>Simulate failure</Text>
        <Switch value={simulateFailure} onValueChange={setSimulateFailure} />
      </View>
      <SessionButton
        status={session.status}
        startedAt={session.startedAt}
        error={session.error}
        onPress={handlePress}
      />
    </SafeAreaView>
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
  // demo controls at the top, the button at the bottom like in the sketch
  screen: {
    flex: 1,
    justifyContent: "space-between",
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
