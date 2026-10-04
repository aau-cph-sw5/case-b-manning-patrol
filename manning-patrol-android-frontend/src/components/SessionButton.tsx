// the session start/stop button. ui only: it shows the status it's given and reports presses.
import type { SessionStatus } from "@/types/session";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";

type SessionButtonProps = {
  status: SessionStatus;
  onPress: () => void;
  // message from the last failed request, shown under the button
  error?: string | null;
};


const appearance: Record<SessionStatus, { label: string; color: string }> = {
  stopped: { label: "Start session", color: "#2563eb" },
  starting: { label: "Starting...", color: "#2563eb" },
  active: { label: "Stop session", color: "#dc2626" },
  stopping: { label: "Stopping...", color: "#dc2626" },
};

export function SessionButton({ status, onPress, error }: SessionButtonProps) {
  const { label, color } = appearance[status];
  // a start/stop request is in flight, so block further presses
  const isPending = status === "starting" || status === "stopping";

  return (
    <View style={styles.container}>
      <Pressable
        role="button"
        aria-busy={isPending}
        disabled={isPending}
        onPress={onPress}
        style={({ pressed }) => [
          styles.button,
          { backgroundColor: color },
          pressed && styles.pressed,
          isPending && styles.pending,
        ]}
      >
        {isPending && <ActivityIndicator color="white" />}
        <Text style={styles.label}>{label}</Text>
      </Pressable>
      {error ? <Text style={styles.error}>{error}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: "center",
    gap: 12,
  },
  button: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    // fixed minimum so the button doesn't change width when the label changes
    minWidth: 220,
    paddingVertical: 14,
    paddingHorizontal: 28,
    borderRadius: 12,
  },
  pressed: {
    opacity: 0.85,
  },
  pending: {
    opacity: 0.7,
  },
  label: {
    color: "white",
    fontSize: 18,
    fontWeight: "600",
  },
  error: {
    color: "#dc2626",
    fontSize: 14,
    textAlign: "center",
  },
});
