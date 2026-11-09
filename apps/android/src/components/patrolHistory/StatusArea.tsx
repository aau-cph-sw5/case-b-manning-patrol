/** Pinned status area above the scrollable history page: fetch-error banner and date row. */

import { Pressable, StyleSheet, Text, View } from "react-native";

import { formatDayLabel } from "@/utils/patrolRecord";

type StatusAreaProps = {
  /** Fetch error to banner, or null when the last fetch succeeded. */
  error: string | null;
  /** Connection count text for the date row, e.g. "4 forbindelser". */
  connectionCount: string;
  /** Current time in epoch ms; the date label is computed from it. */
  now: number;
  /** Re-fetches the records. */
  onRetry: () => Promise<void>;
};

/** Render the error banner (only on a failed refetch) above the date row. */
export function StatusArea({ error, connectionCount, now, onRetry }: StatusAreaProps) {
  return (
    <View style={styles.statusArea}>
      {error !== null ? (
        <View style={styles.errorBanner}>
          <Text style={styles.errorText}>{error}</Text>
          <Pressable
            onPress={() => void onRetry()}
            accessibilityRole="button"
            hitSlop={8}
          >
            <Text style={styles.retryText}>Prøv igen</Text>
          </Pressable>
        </View>
      ) : null}
      <View style={styles.dateRow}>
        <Text style={styles.dateLabel}>I dag · {formatDayLabel(new Date(now))}</Text>
        <Text style={styles.dateCount}>{connectionCount}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  statusArea: {
    gap: 12,
    marginBottom: 16,
    paddingHorizontal: 16,
    paddingTop: 20,
  },
  errorBanner: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12,
    padding: 12,
    borderRadius: 12,
    backgroundColor: "#fdecec",
  },
  errorText: {
    color: "#ff4d4d",
    fontSize: 14,
    textAlign: "center",
  },
  retryText: {
    color: "#940024",
    fontSize: 13,
    fontWeight: "700",
  },
  dateRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  dateLabel: {
    color: "#202220",
    fontSize: 14,
    fontWeight: "700",
  },
  dateCount: {
    color: "#656865",
    fontSize: 12,
  },
});
