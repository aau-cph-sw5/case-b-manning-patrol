import { StyleSheet } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { SessionButton } from "@/components/SessionButton";

// not connected yet: wiring the button to sessionReducer and the session api is a separate ticket.
// see the frontend README for how to connect it.
function handleSessionPress() {}

export default function Index() {
  return (
    <SafeAreaView style={styles.screen} edges={["bottom"]}>
      <SessionButton status="stopped" startedAt={null} onPress={handleSessionPress} />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  // the session button sits at the bottom of the screen
  screen: {
    flex: 1,
    justifyContent: "flex-end",
    padding: 16,
    backgroundColor: "white",
  },
});
