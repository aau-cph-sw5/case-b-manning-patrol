/** Card for one open (still running) connection in the patrol history. */

import { StyleSheet, Text, View } from "react-native";

import { StatusBadge } from "@/components/StatusBadge";

import { isPendingRecord, type HistoryEntry } from "@/types/patrol_records/record";

import {
  formatDurationSecs,
  formatTimeOfDay,
  isPatrolled,
  openRecordElapsedMs,
  remainingToPatrolMs,
  shortBeaconId,
} from "@/utils/patrolRecord";

type OpenRecordCardProps = {
  record: HistoryEntry;
  /** Current time in epoch ms; the status and progress are computed from it. */
  now: number;
};

/**
 * Render one open connection: the area name, the live patrol status, the
 * start time, the patrol requirement and a progress bar counting down to it.
 *
 * A pending placeholder has no resolved area or patrol requirement yet, so it
 * shows the beacon id, an "Afventer…" badge and only the elapsed time. The
 * countdown is recomputed from `now` on every render, so it stays honest
 * between fetches. Once the requirement is met the bar is full and the
 * countdown label is hidden.
 */
export function OpenRecordCard({ record, now }: OpenRecordCardProps) {
  if (isPendingRecord(record)) {
    return (
      <View style={styles.card}>
        <View style={styles.heading}>
          <Text style={styles.title} numberOfLines={1} ellipsizeMode="tail">
            Beacon {shortBeaconId(record.beaconId)}
          </Text>
          <StatusBadge patrolled={false} pending />
        </View>
        <View style={styles.meta}>
          <Text style={styles.metaText}>Start kl. {formatTimeOfDay(record.startedAt)}</Text>
          <Text style={styles.requirement}>
            Varighed: {formatDurationSecs(openRecordElapsedMs(record, now) / 1000)}
          </Text>
        </View>
      </View>
    );
  }

  const patrolled = isPatrolled(record, now);
  const remainingMs = remainingToPatrolMs(record, now);
  const requirementMs = record.minPatrolDurationSecs * 1000;
  const complete = remainingMs === 0;
  const progress = complete ? 1 : Math.max(0, 1 - remainingMs / requirementMs);

  return (
    <View style={styles.card}>
      <View style={styles.heading}>
        <Text style={styles.title} numberOfLines={1} ellipsizeMode="tail">
          {record.area.name}
        </Text>
        <StatusBadge patrolled={patrolled} />
      </View>
      <View style={styles.meta}>
        <Text style={styles.metaText}>Start kl. {formatTimeOfDay(record.startedAt)}</Text>
        <Text style={styles.requirement}>
          Patruljekrav: {record.minPatrolDurationSecs} sek
        </Text>
      </View>
      <View style={styles.progressRow}>
        <View style={styles.track}>
          <View style={[styles.value, { width: `${progress * 100}%` }]} />
        </View>
        {complete ? null : (
          <Text style={styles.progressLabel}>
            {Math.ceil(remainingMs / 1000)} sek tilbage
          </Text>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    padding: 14,
    gap: 9,
    borderWidth: 1,
    borderColor: "#292c29",
    borderRadius: 14,
    backgroundColor: "#ffffff",
  },
  heading: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  title: {
    flex: 1,
    minWidth: 0,
    color: "#202220",
    fontSize: 16,
    fontWeight: "700",
  },
  meta: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12,
  },
  metaText: {
    color: "#656865",
    fontSize: 13,
  },
  requirement: {
    color: "#202220",
    fontSize: 13,
    fontWeight: "600",
  },
  progressRow: {
    minHeight: 15,
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  track: {
    flex: 1,
    height: 5,
    overflow: "hidden",
    borderRadius: 3,
    backgroundColor: "#d8d8d8",
  },
  value: {
    height: "100%",
    borderRadius: 3,
    backgroundColor: "#30916e",
  },
  progressLabel: {
    color: "#202220",
    fontSize: 12,
    fontWeight: "600",
    fontVariant: ["tabular-nums"],
  },
});
