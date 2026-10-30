import { StyleSheet, Text, View } from "react-native";

import { useToast } from "@/hooks/useToast";

/**
 * Show the app-wide toast. Mount it once, in the root layout.
 *
 * Renders whatever message useToast provides, or nothing, and never
 * intercepts touches (pointerEvents "none"), so it can float over the slider.
 * Works on Android and web alike: there is no cross-platform toast in React
 * Native core.
 */
export function Toast() {
  const message = useToast();

  if (message === null) {
    return null;
  }

  return (
    <View
      style={styles.toast}
      pointerEvents="none"
      accessibilityRole="alert"
      accessibilityLiveRegion="polite"
    >
      <Text style={styles.text}>{message}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  toast: {
    position: "absolute",
    bottom: 32,
    alignSelf: "center",
    maxWidth: "90%",
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 12,
    backgroundColor: "#262626",
  },
  text: {
    color: "#ffffff",
    fontSize: 14,
    textAlign: "center",
  },
});
