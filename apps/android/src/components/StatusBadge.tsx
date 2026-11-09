/** Status pill shown on a patrol record card. */

import { StyleSheet, Text } from "react-native";

type StatusBadgeProps = {
  /** Whether the visit counts as patrolled at the time being shown. */
  patrolled: boolean;
  /** True for a pending placeholder the backend has not acknowledged yet. */
  pending?: boolean;
};

/**
 * Render the status pill: "Patruljeret" / "Ikke patruljeret", or "Afventer…"
 * for a pending placeholder.
 *
 * Green when the visit qualifies as patrolled, red when it does not, grey
 * while pending.
 */
export function StatusBadge({ patrolled, pending = false }: StatusBadgeProps) {
  if (pending) {
    return <Text style={[styles.badge, styles.pending]}>Afventer…</Text>;
  }
  return (
    <Text style={[styles.badge, patrolled ? styles.patrolled : styles.unpatrolled]}>
      {patrolled ? "Patruljeret" : "Ikke patruljeret"}
    </Text>
  );
}

const styles = StyleSheet.create({
  badge: {
    flexShrink: 0,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 999,
    fontSize: 11,
    fontWeight: "700",
  },
  patrolled: {
    backgroundColor: "#eaf4ef",
    color: "#216b51",
  },
  unpatrolled: {
    backgroundColor: "#fdecec",
    color: "#ff4d4d",
  },
  pending: {
    backgroundColor: "#ececea",
    color: "#656865",
  },
});
