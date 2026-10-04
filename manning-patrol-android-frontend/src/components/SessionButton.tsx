// the session start/stop button. ui only: it shows the status it's given and reports presses.
import { Pressable, StyleSheet, Text, View } from "react-native";

import { SessionButtonIcon, type SessionButtonIconName } from "@/components/SessionButtonIcon";
import type { SessionStatus } from "@/types/session";

// darker than the sketch so white text stays readable (contrast of at least 4.5:1)
const colors = {
  start: "#2e7d62",
  pending: "#6b7280",
  stop: "#d32f2f",
};

type Appearance = {
  label: string;
  // what a screen reader announces
  accessibilityLabel: string;
  color: string;
  icon: SessionButtonIconName;
};

// how the button looks in each status. Record makes the compiler demand an entry for every status.
const appearance: Record<SessionStatus, Appearance> = {
  stopped: {
    label: "Start",
    accessibilityLabel: "Start session",
    color: colors.start,
    icon: "play",
  },
  starting: {
    label: "Starting...",
    accessibilityLabel: "Starting session",
    color: colors.pending,
    icon: "spinner",
  },
  active: {
    label: "Stop",
    accessibilityLabel: "Stop session",
    color: colors.stop,
    icon: "stop",
  },
  stopping: {
    label: "Stopping...",
    accessibilityLabel: "Stopping session",
    color: colors.pending,
    icon: "spinner",
  },
};

type SessionButtonProps = {
  status: SessionStatus;
  onPress: () => void;
  // message from the last failed request, shown under the button
  error?: string | null;
};

export function SessionButton({ status, onPress, error }: SessionButtonProps) {
  const { label, accessibilityLabel, color, icon } = appearance[status];
  // a start/stop request is in flight, so block further presses
  const isPending = status === "starting" || status === "stopping";

  return (
    <View style={styles.container}>
      <Pressable
        role="button"
        accessibilityLabel={accessibilityLabel}
        aria-busy={isPending}
        disabled={isPending}
        onPress={onPress}
        style={({ pressed }) => [styles.button, { backgroundColor: color }, pressed && styles.pressed]}
      >
        <View style={styles.iconSlot}>
          <SessionButtonIcon name={icon} color="white" />
        </View>
        <Text style={styles.label}>{label}</Text>
      </Pressable>
      {/* ternary, not &&: an empty string would be rendered outside <Text> and crash */}
      {error ? <Text style={styles.error}>{error}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignSelf: "stretch",
    gap: 12,
  },
  button: {
    minHeight: 56,
    paddingHorizontal: 20,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  pressed: {
    opacity: 0.85,
  },
  // pinned to the left so the label stays centred in the whole button
  iconSlot: {
    position: "absolute",
    top: 0,
    bottom: 0,
    left: 20,
    justifyContent: "center",
  },
  label: {
    color: "white",
    fontSize: 18,
    fontWeight: "600",
  },
  error: {
    color: colors.stop,
    fontSize: 14,
    textAlign: "center",
  },
});
