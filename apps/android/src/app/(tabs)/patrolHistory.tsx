/**
 * The patrol history tab ("Patruljehistorik").
 *
 * Lists the steward's connections for the current shift in two sections: open
 * connections with a live countdown to their patrol requirement, and closed
 * connections with their duration. Records come from {@link usePatrolRecords}
 * and are re-fetched every time the tab regains focus; the screen re-renders
 * each second via {@link useNow} so the open records' timers stay honest.
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
import { formatDayLabel, splitRecords } from "@/utils/patrolRecord";

/**
 * Render the patrol history screen.
 *
 * While the first fetch is in flight a loading indicator is shown; a failed
 * fetch renders the hook's Danish error with a retry button, and previously
 * fetched records stay on screen while a refetch fails.
 */
export default function PatrolHistoryScreen() {
  const { records, loading, error, refetch } = usePatrolRecords();
  const now = useNow();

  useFocusEffect(() => {
    void refetch();
  });

  const { open, closed } = splitRecords(records);
  const connectionCount =
    records.length === 1 ? "1 forbindelse" : `${records.length} forbindelser`;

  return (
    <View style={styles.screen}>
      <Stack.Screen options={{ title: "Patruljehistorik" }} />
      <PatrolHistoryHeader />
      <ScrollView contentContainerStyle={styles.content}>
        {loading && records.length === 0 ? (
          <View style={styles.center}>
            <ActivityIndicator color="#940024" />
            <Text style={styles.muted}>Henter historik...</Text>
          </View>
        ) : error !== null && records.length === 0 ? (
          <View style={styles.center}>
            <Text style={styles.errorText}>{error}</Text>
            <Pressable
              style={styles.retry}
              onPress={() => void refetch()}
              accessibilityRole="button"
            >
              <Text style={styles.retryText}>Prøv igen</Text>
            </Pressable>
          </View>
        ) : (
          <>
            {error !== null ? (
              <View style={styles.errorBanner}>
                <Text style={styles.errorText}>{error}</Text>
                <Pressable
                  onPress={() => void refetch()}
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
            <View style={styles.section}>
              <View style={styles.sectionHeading}>
                <Text style={styles.sectionTitle}>Åbne forbindelser</Text>
                <Text style={styles.openCount}>
                  {open.length === 1 ? "1 åben" : `${open.length} åbne`}
                </Text>
              </View>
              <View style={styles.openList}>
                {open.length === 0 ? (
                  <Text style={styles.empty}>Ingen åbne forbindelser.</Text>
                ) : (
                  open.map((record) => (
                    <OpenRecordCard
                      key={`${record.beaconId}-${record.startedAt.getTime()}`}
                      record={record}
                      now={now}
                    />
                  ))
                )}
              </View>
            </View>
            <View style={styles.section}>
              <View style={styles.sectionHeading}>
                <Text style={styles.sectionTitle}>Lukkede forbindelser</Text>
                <Text style={styles.closedCount}>
                  {closed.length === 1 ? "1 afsluttet" : `${closed.length} afsluttede`}
                </Text>
              </View>
              <View style={styles.closedList}>
                {closed.length === 0 ? (
                  <Text style={styles.empty}>Ingen lukkede forbindelser.</Text>
                ) : (
                  closed.map((record) => (
                    <ClosedRecordCard
                      key={`${record.beaconId}-${record.startedAt.getTime()}`}
                      record={record}
                      now={now}
                    />
                  ))
                )}
              </View>
              <Text style={styles.listNote}>Seneste forbindelser vises først.</Text>
            </View>
          </>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: "#ffffff",
  },
  content: {
    gap: 24,
    paddingHorizontal: 16,
    paddingTop: 20,
    paddingBottom: 22,
  },
  center: {
    alignItems: "center",
    gap: 12,
    paddingVertical: 40,
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
  section: {
    minWidth: 0,
  },
  sectionHeading: {
    marginBottom: 10,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
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
    gap: 8,
    padding: 8,
    borderRadius: 20,
    backgroundColor: "#d9f0e3",
  },
  closedList: {
    gap: 8,
    padding: 8,
    borderRadius: 20,
    backgroundColor: "#d8d8d8",
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
