/**
 * The patrol history tab ("Patruljehistorik").
 *
 * Lists the steward's connections for the current shift in two sections: open
 * connections with a live countdown to their patrol requirement, and closed
 * connections with their duration. Records come from {@link usePatrolRecords}
 * and are re-fetched every time the tab regains focus; the screen re-renders
 * each second via {@link useNow} so the open records' timers stay honest.
 * Connections the backend has not acknowledged yet are merged in as pending
 * placeholders (state/pendingRecords) at render time, so an offline connect
 * or disconnect still shows in the matching section until a fetch reconciles it.
 *
 * Layout: the screen itself never scrolls. The open-connections box (green
 * panel) sits at the top and grows with its cards — up to five open
 * connections are shown at a glance without any scrolling — so the box is
 * flexible rather than fixed. The closed-connections box (grey panel) is
 * pushed down as the open box expands and fills all remaining space; it
 * scrolls its own cards internally, so thumb-scrolling inside it never
 * moves the main screen.
 */

import { Stack, useFocusEffect } from "expo-router";

import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { ClosedRecordCard } from "@/components/ClosedRecordCard";
import { OpenRecordCard } from "@/components/OpenRecordCard";
import PatrolHistoryHeader from "@/components/PatrolHistoryHeader";
import { useNow } from "@/hooks/useNow";
import { usePatrolRecords } from "@/hooks/usePatrolRecords";
import { getPendingRecords } from "@/state/pendingRecords";
import type { HistoryEntry } from "@/types/patrol_records/record";
import { formatDayLabel, mergeWithPending, splitRecords } from "@/utils/patrolRecord";

/**
 * Render the patrol history screen.
 *
 * While the first fetch is in flight a loading indicator is shown; a failed
 * fetch renders the hook's Danish error with a retry button, and previously
 * fetched records stay on screen while a refetch fails. Once records are
 * shown, the open box grows flexibly with its cards (no internal scrolling,
 * so all open connections are visible at a glance) and pushes the closed box
 * down; the closed box fills the remaining space and scrolls its cards
 * internally.
 */
export default function PatrolHistoryScreen() {
  const { records, loading, error, refetch } = usePatrolRecords();
  const now = useNow();

  useFocusEffect(() => {
    void refetch();
  });

  // merge at render time: the useNow tick above re-reads the pending store
  // every second, so a pending added on the patrol tab shows up here within
  // one tick, and a successful fetch retires it via the hook
  const entries = mergeWithPending(records, getPendingRecords());
  const { open, closed } = splitRecords(entries);
  const connectionCount =
    entries.length === 1 ? "1 forbindelse" : `${entries.length} forbindelser`;
  const statusOnly = entries.length === 0 && (loading || error !== null);

  return (
    <View style={styles.screen}>
      <Stack.Screen options={{ title: "Patruljehistorik" }} />
      <PatrolHistoryHeader />
      {statusOnly ? (
        <HistoryStatus loading={loading} error={error} onRetry={refetch} />
      ) : (
        <View style={styles.content}>
          <StatusArea
            error={error}
            connectionCount={connectionCount}
            now={now}
            onRetry={refetch}
          />
          <OpenRecordsSection records={open} now={now} />
          <ClosedRecordsSection records={closed} now={now} />
          <Text style={listStyles.listNote}>Seneste forbindelser vises først.</Text>
        </View>
      )}
    </View>
  );
}

type StatusAreaProps = {
  error: string | null;
  connectionCount: string;
  now: number;
  onRetry: () => Promise<void>;
};

/** Error banner (on a failed refetch) above the date row. */
function StatusArea({ error, connectionCount, now, onRetry }: StatusAreaProps) {
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

/** The green open-connections box; grows with its cards, no internal scroll. */
function OpenRecordsSection({ records, now }: { records: HistoryEntry[]; now: number }) {
  return (
    <>
      <View style={listStyles.sectionHeading}>
        <Text style={listStyles.sectionTitle}>Åbne forbindelser</Text>
        <Text style={listStyles.openCount}>
          {records.length === 1 ? "1 åben" : `${records.length} åbne`}
        </Text>
      </View>
      <View style={listStyles.openList}>
        {records.length === 0 ? (
          <Text style={listStyles.empty}>Ingen åbne forbindelser.</Text>
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

/** The grey closed-connections box; fills the remaining space, scrolls internally. */
function ClosedRecordsSection({ records, now }: { records: HistoryEntry[]; now: number }) {
  return (
    <>
      <View style={[listStyles.sectionHeading, listStyles.closedHeading]}>
        <Text style={listStyles.sectionTitle}>Lukkede forbindelser</Text>
        <Text style={listStyles.closedCount}>
          {records.length === 1 ? "1 afsluttet" : `${records.length} afsluttede`}
        </Text>
      </View>
      <View style={listStyles.closedList}>
        <ScrollView
          style={listStyles.closedScroll}
          contentContainerStyle={listStyles.listContent}
        >
          {records.length === 0 ? (
            <Text style={listStyles.empty}>Ingen lukkede forbindelser.</Text>
          ) : (
            records.map((record) => (
              <ClosedRecordCard
                key={`${record.beaconId}-${record.startedAt.getTime()}`}
                record={record}
                now={now}
              />
            ))
          )}
        </ScrollView>
      </View>
    </>
  );
}

type HistoryStatusProps = {
  loading: boolean;
  error: string | null;
  onRetry: () => Promise<void>;
};

/** Loading spinner or the steward-facing fetch error with a retry button. */
function HistoryStatus({ loading, error, onRetry }: HistoryStatusProps) {
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
  screen: {
    flex: 1,
    backgroundColor: "#ffffff",
  },
  statusContent: {
    flex: 1,
    justifyContent: "center",
    paddingHorizontal: 16,
    paddingVertical: 20,
  },
  content: {
    flex: 1,
    minHeight: 0,
    paddingHorizontal: 16,
    paddingTop: 20,
    paddingBottom: 22,
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
  errorBanner: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12,
    padding: 12,
    borderRadius: 12,
    backgroundColor: "#fdecec",
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
  statusArea: {
    gap: 12,
    marginBottom: 24,
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

// list and card styles, kept in a separate sheet so each stays small
const listStyles = StyleSheet.create({
  sectionHeading: {
    marginBottom: 10,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  closedHeading: {
    marginTop: 24,
  },
  sectionTitle: {
    color: "#202220",
    fontSize: 18,
    fontWeight: "700",
  },
  openCount: {
    paddingHorizontal: 9,
    paddingVertical: 3,
    borderRadius: 999,
    backgroundColor: "#eaf4ef",
    color: "#216b51",
    fontSize: 12,
    fontWeight: "700",
  },
  closedCount: {
    color: "#656865",
    fontSize: 12,
  },
  openList: {
    padding: 8,
    gap: 8,
    borderRadius: 20,
    backgroundColor: "#d9f0e3",
  },
  closedList: {
    flex: 1,
    minHeight: 0,
    padding: 8,
    borderRadius: 20,
    overflow: "hidden",
    backgroundColor: "#d8d8d8",
  },
  closedScroll: {
    flex: 1,
  },
  listContent: {
    gap: 8,
  },
  empty: {
    padding: 6,
    color: "#656865",
    fontSize: 13,
  },
  listNote: {
    marginTop: 10,
    color: "#656865",
    fontSize: 11,
  },
});
