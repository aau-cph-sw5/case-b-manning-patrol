/** Root layout of the app, wrapping every screen. */
import { Stack } from "expo-router";
import { StyleSheet } from "react-native";
import { GestureHandlerRootView } from "react-native-gesture-handler";

import { SafeAreaProvider } from "react-native-safe-area-context";

import { Toast } from "@/components/Toast";

/**
 * Render the tab group in a header-less stack, with the app-wide
 * {@link Toast} on top of every screen.
 *
 * `SafeAreaProvider` must wrap the app so safe-area insets (status bar, and
 * on Samsung devices the OS navigation bar) are real; without it the header
 * and tab bar `SafeAreaView`s get zero insets and stretch behind the OS bars.
 *
 * `GestureHandlerRootView` must wrap everything that uses gestures, such as
 * the session slider.
 */
export default function RootLayout() {
  return (
    <SafeAreaProvider style={styles.root}>
      <GestureHandlerRootView style={styles.root}>
        <Stack>
          <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        </Stack>
        <Toast />
      </GestureHandlerRootView>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
  },
});
