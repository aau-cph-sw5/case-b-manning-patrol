/** Open-connections section of the patrol history: a box that grows with its cards and never scrolls. */

import { StyleSheet, Text, View } from "react-native";

import { OpenRecordCard } from "@/components/OpenRecordCard";
import { SectionHeading } from "@/components/patrolHistory/SectionHeading";

import type { HistoryEntry } from "@/types/patrol_records/record";

type OpenConnectionsSectionProps = {
  /** Open records, most recent first. */
  records: HistoryEntry[];
  /** Current time in epoch ms, forwarded to the cards' countdowns. */
  now: number;
};

/**
 * Render the "Åbne forbindelser" heading and the green box with one card per
 * open connection.
 *
 * The box is a plain view, so all open connections stay visible at a glance
 * and push the rest of the page down as they grow.
 */
export function OpenConnectionsSection({ records, now }: OpenConnectionsSectionProps) {
  return (
    <>
      <SectionHeading
        title="Åbne forbindelser"
        badge={records.length === 1 ? "1 åben" : `${records.length} åbne`}
        badgeStyle={styles.openCount}
      />
      <View style={styles.openList}>
        {records.length === 0 ? (
          <Text style={styles.empty}>Ingen åbne forbindelser.</Text>
        ) : (
          records.map((record) => (
            <OpenRecordCard
              key={`${record.beaconId}-${record.startedAt.getTime()}`}
              record={record}
              now={now}
            />
          ))
        )}
      </View>
    </>
  );
}

const styles = StyleSheet.create({
  openCount: {
    paddingHorizontal: 9,
    paddingVertical: 3,
    borderRadius: 999,
    backgroundColor: "#eaf4ef",
    color: "#216b51",
    fontSize: 12,
    fontWeight: "700",
  },
  openList: {
    padding: 8,
    gap: 8,
    borderRadius: 20,
    backgroundColor: "#d9f0e3",
  },
  empty: {
    padding: 6,
    color: "#656865",
    fontSize: 13,
  },
});
