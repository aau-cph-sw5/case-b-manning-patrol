import { Stack } from "expo-router";
import { StyleSheet } from "react-native";
import { GestureHandlerRootView } from "react-native-gesture-handler";

import { Toast } from "@/components/Toast";

/** Wrap the app in the gesture handler root and mount the app-wide toast above the screens. */
export default function RootLayout() {
  return (
    <GestureHandlerRootView style={styles.root}>
      <Stack>
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      </Stack>
      <Toast />
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
  },
});
