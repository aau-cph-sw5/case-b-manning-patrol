import { StyleSheet } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { SessionButton } from "@/components/SessionButton";
import { initialSessionState } from "@/types/session";

// not connected yet: the session api is a separate ticket. once it exists, replace the two lines
// below with useSession (see the frontend README).
function handleSessionPress() {}

export default function Index() {
  return (
    <SafeAreaView style={styles.screen} edges={["bottom"]}>
      <SessionButton {...initialSessionState} onPress={handleSessionPress} />
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
