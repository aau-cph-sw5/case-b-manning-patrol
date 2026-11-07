/**
 * The patrol history tab ("Patruljehistorik").
 *
 * Lists the steward's connections for the current shift in two sections: open
 * connections with a live countdown to their patrol requirement, and closed
 * connections with their duration. Records come from {@link usePatrolRecords}
 * and are re-fetched every time the tab regains focus; the screen re-renders
 * each second via {@link useNow} so the open records' timers stay honest.
 *
 * Layout: the header and date row stay pinned at the top; everything below
 * lives on a scrollable page, so the screen itself scrolls like a document
 * when the open box pushes content off-screen. The open-connections box
 * (green panel) grows and shrinks with its cards and never scrolls. The
 * closed-connections box (grey panel) has a fixed height of at most six
 * cards and scrolls its own records internally — nested scrolling: the box
 * scrolls first, then the page takes over — so hundreds of records stay
 * reachable without stretching the page.
 */

import { Stack, useFocusEffect } from "expo-router";

import { useState } from "react";

import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
  type LayoutChangeEvent,
} from "react-native";

import { ClosedRecordCard } from "@/components/ClosedRecordCard";
import { OpenRecordCard } from "@/components/OpenRecordCard";
import PatrolHistoryHeader from "@/components/PatrolHistoryHeader";
import { useNow } from "@/hooks/useNow";
import { usePatrolRecords } from "@/hooks/usePatrolRecords";
import type { Record } from "@/types/patrol_records/record";
import { formatDayLabel, splitRecords } from "@/utils/patrolRecord";

/** How many closed-connection cards the grey box shows before scrolling internally. */
const CLOSED_CARDS_VISIBLE = 6;
/** Gap between cards (matches listContent) — used to size the closed box. */
const LIST_GAP = 8;
/** Padding of the list boxes — used to size the closed box. */
const BOX_PADDING = 8;
/** Height of the closed box until the first card has been measured. */
const CLOSED_LIST_FALLBACK_HEIGHT = 520;

/**
 * Render the patrol history screen.
 *
 * While the first fetch is in flight a loading indicator is shown; a failed
 * fetch renders the hook's Danish error with a retry button, and previously
 * fetched records stay on screen while a refetch fails. Once records are
 * shown, the header and date row stay pinned and the rest of the screen is a
 * scrollable page: the open box grows with its cards (no internal scroll)
 * and pushes the closed box down, while the closed box keeps a fixed height
 * of at most {@link CLOSED_CARDS_VISIBLE} cards and scrolls internally.
 */
export default function PatrolHistoryScreen() {
  const { records, loading, error, refetch } = usePatrolRecords();
  const now = useNow();
  useFocusEffect(() => {
    void refetch();
  });

  const { open, closed } = splitRecords(records);
  const statusOnly = records.length === 0 && (loading || error !== null);

  return (
    <View style={styles.screen}>
      <Stack.Screen options={{ title: "Patruljehistorik" }} />
      <PatrolHistoryHeader />
      {statusOnly ? (
        <HistoryStatus loading={loading} error={error} onRetry={refetch} />
      ) : (
        <HistoryRecords
          open={open}
          closed={closed}
          now={now}
          error={error}
          recordCount={records.length}
          onRetry={refetch}
        />
      )}
    </View>
  );
}

type HistoryStatusProps = {
  loading: boolean;
  error: string | null;
  onRetry: () => Promise<void>;
};

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

type HistoryRecordsProps = {
  open: Record[];
  closed: Record[];
  now: number;
  error: string | null;
  recordCount: number;
  onRetry: () => Promise<void>;
};

function HistoryRecords({
  open,
  closed,
  now,
  error,
  recordCount,
  onRetry,
}: HistoryRecordsProps) {
  const connectionCount =
    recordCount === 1 ? "1 forbindelse" : `${recordCount} forbindelser`;

  return (
    <View style={styles.body}>
      <HistoryStatusArea
        error={error}
        connectionCount={connectionCount}
        now={now}
        onRetry={onRetry}
      />
      <ScrollView
        style={styles.page}
        contentContainerStyle={styles.pageContent}
        keyboardDismissMode="on-drag"
      >
        <OpenRecordsSection records={open} now={now} />
        <ClosedRecordsSection records={closed} now={now} />
        <Text style={recordStyles.listNote}>Seneste forbindelser vises først.</Text>
      </ScrollView>
    </View>
  );
}

type HistoryStatusAreaProps = {
  error: string | null;
  connectionCount: string;
  now: number;
  onRetry: () => Promise<void>;
};

function HistoryStatusArea({
  error,
  connectionCount,
  now,
  onRetry,
}: HistoryStatusAreaProps) {
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

function OpenRecordsSection({ records, now }: { records: Record[]; now: number }) {
  return (
    <>
      <View style={recordStyles.sectionHeading}>
        <Text style={recordStyles.sectionTitle}>Åbne forbindelser</Text>
        <Text style={recordStyles.openCount}>
          {records.length === 1 ? "1 åben" : `${records.length} åbne`}
        </Text>
      </View>
      <View style={recordStyles.openList}>
        {records.length === 0 ? (
          <Text style={recordStyles.empty}>Ingen åbne forbindelser.</Text>
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

function ClosedRecordsSection({ records, now }: { records: Record[]; now: number }) {
  const [closedCardHeight, setClosedCardHeight] = useState(0);
  const closedListMaxHeight =
    closedCardHeight > 0
      ? CLOSED_CARDS_VISIBLE * closedCardHeight +
        (CLOSED_CARDS_VISIBLE - 1) * LIST_GAP +
        2 * BOX_PADDING
      : CLOSED_LIST_FALLBACK_HEIGHT;

  const handleClosedCardLayout = (event: LayoutChangeEvent) => {
    setClosedCardHeight(event.nativeEvent.layout.height);
  };

  return (
    <>
      <View style={[recordStyles.sectionHeading, recordStyles.closedHeading]}>
        <Text style={recordStyles.sectionTitle}>Lukkede forbindelser</Text>
        <Text style={recordStyles.closedCount}>
          {records.length === 1 ? "1 afsluttet" : `${records.length} afsluttede`}
        </Text>
      </View>
      <View style={recordStyles.closedList}>
        <ScrollView
          style={[recordStyles.closedScroll, { maxHeight: closedListMaxHeight }]}
          contentContainerStyle={recordStyles.listContent}
          nestedScrollEnabled
        >
          {records.length === 0 ? (
            <Text style={recordStyles.empty}>Ingen lukkede forbindelser.</Text>
          ) : (
            records.map((record, index) => (
              <View
                key={`${record.beaconId}-${record.startedAt.getTime()}`}
                onLayout={index === 0 ? handleClosedCardLayout : undefined}
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
  body: {
    flex: 1,
    minHeight: 0,
  },
  page: {
    flex: 1,
    minHeight: 0,
  },
  pageContent: {
    paddingHorizontal: 16,
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
    marginBottom: 16,
    paddingHorizontal: 16,
    paddingTop: 20,
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

const recordStyles = StyleSheet.create({
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
  listNote: {
    marginTop: 10,
    color: "#656865",
    fontSize: 11,
  },
});
