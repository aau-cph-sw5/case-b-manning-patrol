/** Closed-connections section of the patrol history: a fixed-height box that scrolls its own cards. */

import { ScrollView, StyleSheet, Text, View } from "react-native";

import { ClosedRecordCard } from "@/components/ClosedRecordCard";
import { SectionHeading } from "@/components/patrolHistory/SectionHeading";

import { useVisibleListHeight } from "@/hooks/useVisibleListHeight";

import type { HistoryEntry } from "@/types/patrol_records/record";

/** How many closed-connection cards the grey box shows before scrolling internally. */
const VISIBLE_CLOSED_CARDS = 6;

type ClosedConnectionsSectionProps = {
  /** Closed records, most recent first. */
  records: HistoryEntry[];
  /** Current time in epoch ms, forwarded to the cards. */
  now: number;
};

/**
 * Render the "Lukkede forbindelser" heading and the grey box with one card per
 * closed connection.
 *
 * The box keeps a fixed height of at most {@link VISIBLE_CLOSED_CARDS} cards
 * (measured from the first card) and scrolls internally with
 * `nestedScrollEnabled`, so it stays visible no matter how far the open box
 * pushes it down the page.
 */
export function ClosedConnectionsSection({ records, now }: ClosedConnectionsSectionProps) {
  const { maxHeight, onFirstCardLayout } = useVisibleListHeight(VISIBLE_CLOSED_CARDS);

  return (
    <>
      <SectionHeading
        title="Lukkede forbindelser"
        badge={records.length === 1 ? "1 afsluttet" : `${records.length} afsluttede`}
        badgeStyle={styles.closedCount}
        headingStyle={styles.closedHeading}
      />
      <View style={styles.closedList}>
        <ScrollView
          style={[styles.closedScroll, { maxHeight }]}
          contentContainerStyle={styles.listContent}
          nestedScrollEnabled
        >
          {records.length === 0 ? (
            <Text style={styles.empty}>Ingen lukkede forbindelser.</Text>
          ) : (
            records.map((record, index) => (
              <View
                key={`${record.beaconId}-${record.startedAt.getTime()}`}
                onLayout={index === 0 ? onFirstCardLayout : undefined}
              >
                <ClosedRecordCard record={record} now={now} />
              </View>
            ))
          )}
        </ScrollView>
      </View>
    </>
  );
}

const styles = StyleSheet.create({
  closedHeading: {
    marginTop: 24,
  },
  closedCount: {
    color: "#656865",
    fontSize: 12,
  },
  closedList: {
    padding: 8,
    borderRadius: 20,
    overflow: "hidden",
    backgroundColor: "#d8d8d8",
  },
  closedScroll: {
    flexGrow: 0,
  },
  listContent: {
    gap: 8,
  },
  empty: {
    padding: 6,
    color: "#656865",
    fontSize: 13,
  },
});
