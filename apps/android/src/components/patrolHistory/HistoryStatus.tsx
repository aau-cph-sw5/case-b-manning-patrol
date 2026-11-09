/** Full-screen loading or fetch-error state of the patrol history tab. */

import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";

type HistoryStatusProps = {
  /** True while the first fetch is in flight. */
  loading: boolean;
  /** Steward-facing fetch error, or null while loading. */
  error: string | null;
  /** Re-fetches the records. */
  onRetry: () => Promise<void>;
};

/** Render the loading spinner, or the fetch error with a retry button. */
export function HistoryStatus({ loading, error, onRetry }: HistoryStatusProps) {
  return (
    <View style={styles.statusContent}>
      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator color="#940024" />
          <Text style={styles.muted}>Henter historik...</Text>
        </View>
      ) : (
        <View style={styles.center}>
          <Text style={styles.errorText}>{error}</Text>
          <Pressable
            style={styles.retry}
            onPress={() => void onRetry()}
            accessibilityRole="button"
          >
            <Text style={styles.retryText}>Prøv igen</Text>
          </Pressable>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  statusContent: {
    flex: 1,
    justifyContent: "center",
    paddingHorizontal: 16,
    paddingVertical: 20,
  },
  center: {
    alignItems: "center",
    gap: 12,
  },
  muted: {
    color: "#656865",
    fontSize: 13,
  },
  errorText: {
    color: "#ff4d4d",
    fontSize: 14,
    textAlign: "center",
  },
  retry: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 999,
    backgroundColor: "#940024",
  },
  retryText: {
    color: "#ffffff",
    fontSize: 13,
    fontWeight: "700",
  },
});
