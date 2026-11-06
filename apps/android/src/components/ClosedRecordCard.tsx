/** Card for one closed connection in the patrol history. */

import { StyleSheet, Text, View } from "react-native";

import { StatusBadge } from "@/components/StatusBadge";

import { isPendingRecord, type HistoryEntry } from "@/types/patrol_records/record";

import {
  formatDurationSecs,
  formatTimeOfDay,
  isPatrolled,
  pendingDurationSecs,
  recordDurationSecs,
  shortBeaconId,
} from "@/utils/patrolRecord";

type ClosedRecordCardProps = {
  record: HistoryEntry;
  /** Current time in epoch ms; only the status computation reads it. */
  now: number;
};

/**
 * Render one closed connection: the area name, the server's final patrol
 * status, the start time and how long the visit lasted.
 *
 * A pending placeholder has no resolved area or server status yet, so it
 * shows the beacon id, an "Afventer…" badge and the duration computed from
 * its own connect/disconnect timestamps.
 */
export function ClosedRecordCard({ record, now }: ClosedRecordCardProps) {
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
          <Text style={styles.metaText}>
            Varighed: {formatDurationSecs(pendingDurationSecs(record))}
          </Text>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.card}>
      <View style={styles.heading}>
        <Text style={styles.title} numberOfLines={1} ellipsizeMode="tail">
          {record.area.name}
        </Text>
        <StatusBadge patrolled={isPatrolled(record, now)} />
      </View>
      <View style={styles.meta}>
        <Text style={styles.metaText}>Start kl. {formatTimeOfDay(record.startedAt)}</Text>
        <Text style={styles.metaText}>
          Varighed: {formatDurationSecs(recordDurationSecs(record))}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    padding: 14,
    gap: 8,
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
    fontSize: 15,
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
});
