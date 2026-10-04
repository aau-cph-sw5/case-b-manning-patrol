import { ScrollView, StyleSheet } from "react-native";

import { SessionButton } from "@/components/SessionButton";

// pretend the active session started 46 minutes ago, so the timer shows a realistic value
const PREVIEW_STARTED_AT = Date.now() - 46 * 60 * 1000;

function logPress() {
  console.log("session button: pressed");
}

// temporary preview of every button state, so they can be compared side by side
export default function Index() {
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <SessionButton status="stopped" startedAt={null} onPress={logPress} />
      <SessionButton status="starting" startedAt={null} onPress={logPress} />
      <SessionButton status="active" startedAt={PREVIEW_STARTED_AT} onPress={logPress} />
      <SessionButton status="stopping" startedAt={PREVIEW_STARTED_AT} onPress={logPress} />
      <SessionButton
        status="stopped"
        startedAt={null}
        error="Could not start the session. Try again."
        onPress={logPress}
      />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    justifyContent: "center",
    gap: 24,
    padding: 16,
    backgroundColor: "white",
  },
});
