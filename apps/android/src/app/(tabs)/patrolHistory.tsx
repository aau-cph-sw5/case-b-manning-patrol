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
 * Layout: the header and the date row stay pinned at the top; everything below
 * lives on a scrollable page, so the screen scrolls like a document when the
 * open box pushes content off-screen. The open-connections box (green panel)
 * grows and shrinks with its cards and never scrolls. The closed-connections
 * box (grey panel) keeps a fixed height of a few cards and scrolls its own
 * records internally, so it stays visible no matter how many connections are
 * open. Each section is its own component under components/patrolHistory.
 */

import { Stack, useFocusEffect } from "expo-router";

import { ScrollView, StyleSheet, Text, View } from "react-native";

import { ClosedConnectionsSection } from "@/components/patrolHistory/ClosedConnectionsSection";
import { HistoryStatus } from "@/components/patrolHistory/HistoryStatus";
import { OpenConnectionsSection } from "@/components/patrolHistory/OpenConnectionsSection";
import { StatusArea } from "@/components/patrolHistory/StatusArea";
import PatrolHistoryHeader from "@/components/PatrolHistoryHeader";

import { useNow } from "@/hooks/useNow";
import { usePatrolRecords } from "@/hooks/usePatrolRecords";

import { getPendingRecords } from "@/state/pendingRecords";

import { mergeWithPending, splitRecords } from "@/utils/patrolRecord";

/**
 * Render the patrol history screen.
 *
 * While the first fetch is in flight a loading indicator is shown; a failed
 * fetch renders the hook's Danish error with a retry button, and previously
 * fetched records stay on screen while a refetch fails. Once records are
 * shown, the header and date row stay pinned and the rest of the screen is a
 * scrollable page with the two sections on it.
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
        <>
          <StatusArea
            error={error}
            connectionCount={connectionCount}
            now={now}
            onRetry={refetch}
          />
          <ScrollView
            style={styles.page}
            contentContainerStyle={styles.pageContent}
            keyboardDismissMode="on-drag"
          >
            <OpenConnectionsSection records={open} now={now} />
            <ClosedConnectionsSection records={closed} now={now} />
            <Text style={styles.listNote}>Seneste forbindelser vises først.</Text>
          </ScrollView>
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: "#ffffff",
  },
  page: {
    flex: 1,
    minHeight: 0,
  },
  pageContent: {
    paddingHorizontal: 16,
    paddingBottom: 22,
  },
  listNote: {
    marginTop: 10,
    color: "#656865",
    fontSize: 11,
  },
});
