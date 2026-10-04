import { ScrollView, StyleSheet } from "react-native";

import { SessionButton } from "@/components/SessionButton";

function logPress() {
  console.log("session button: pressed");
}

// temporary preview of every button state, so they can be compared side by side
export default function Index() {
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <SessionButton status="stopped" onPress={logPress} />
      <SessionButton status="starting" onPress={logPress} />
      <SessionButton status="active" onPress={logPress} />
      <SessionButton status="stopping" onPress={logPress} />
      <SessionButton
        status="stopped"
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
