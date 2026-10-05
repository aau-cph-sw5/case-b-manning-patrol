import { Button, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";

import { SessionSlider } from "@/components/SessionSlider";
import { useSession } from "@/hooks/useSession";

export default function Index() {
  const router = useRouter();
  const { state, start, stop } = useSession();

  return (
    <View style={styles.screen}>
      <SessionSlider
        status={state.status}
        startedAt={state.startedAt}
        error={state.error}
        onStart={start}
        onStop={stop}
      />
      <Button title="Beacon scanner demo" onPress={() => router.push("/beacon")} />
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    justifyContent: "center",
    padding: 16,
    backgroundColor: "white",
  },
});
