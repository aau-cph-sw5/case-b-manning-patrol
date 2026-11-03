/** Root layout of the app, wrapping every screen. */
import { Stack } from "expo-router";
import { StyleSheet } from "react-native";
import { GestureHandlerRootView } from "react-native-gesture-handler";

import { Toast } from "@/components/Toast";

/**
 * Render the tab group in a header-less stack, with the app-wide
 * {@link Toast} on top of every screen.
 *
 * `GestureHandlerRootView` must wrap everything that uses gestures, such as
 * the session slider.
 */
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
