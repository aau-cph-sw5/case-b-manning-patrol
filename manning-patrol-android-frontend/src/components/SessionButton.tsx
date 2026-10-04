// the session start/stop button. ui only: it shows the status it's given and reports presses.
import { Pressable, StyleSheet, Text, View } from "react-native";

import { ElapsedTime } from "@/components/ElapsedTime";
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
  // show how long the session has been running
  showsTimer: boolean;
};

// how the button looks in each status. Record makes the compiler demand an entry for every status.
const appearance: Record<SessionStatus, Appearance> = {
  stopped: {
    label: "Start",
    accessibilityLabel: "Start session",
    color: colors.start,
    icon: "play",
    showsTimer: false,
  },
  starting: {
    label: "Starting...",
    accessibilityLabel: "Starting session",
    color: colors.pending,
    icon: "spinner",
    showsTimer: false,
  },
  active: {
    label: "Stop",
    accessibilityLabel: "Stop session",
    color: colors.stop,
    icon: "stop",
    showsTimer: true,
  },
  stopping: {
    label: "Stopping...",
    accessibilityLabel: "Stopping session",
    color: colors.pending,
    icon: "spinner",
    showsTimer: false,
  },
};

type SessionButtonProps = {
  status: SessionStatus;
  // when the current session started (ms since epoch), shown as elapsed time while active
  startedAt: number | null;
  onPress: () => void;
  // message from the last failed request, shown under the button
  error?: string | null;
};

export function SessionButton({ status, startedAt, onPress, error }: SessionButtonProps) {
  const { label, accessibilityLabel, color, icon, showsTimer } = appearance[status];
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
        {showsTimer && (
          <View style={styles.timerSlot}>
            <ElapsedTime startedAt={startedAt} style={styles.timer} />
          </View>
        )}
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
  // icon and timer are pinned to the sides so the label stays centred in the whole button
  iconSlot: {
    position: "absolute",
    top: 0,
    bottom: 0,
    left: 20,
    justifyContent: "center",
  },
  timerSlot: {
    position: "absolute",
    top: 0,
    bottom: 0,
    right: 20,
    justifyContent: "center",
  },
  label: {
    color: "white",
    fontSize: 18,
    fontWeight: "600",
  },
  timer: {
    color: "white",
    fontSize: 18,
    fontWeight: "700",
    // equal-width digits so the text doesn't jitter every second
    fontVariant: ["tabular-nums"],
  },
  error: {
    color: colors.stop,
    fontSize: 14,
    textAlign: "center",
  },
});
