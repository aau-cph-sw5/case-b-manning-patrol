import { useEffect, useMemo, useState } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";

import Station, { StationListHeader } from "@/components/Station";
import { SessionSlider } from "@/components/SessionSlider";
import TopNavBar from "@/components/TopNavBar";
import { MOCK_ANDROID_ID, MOCK_BEACON_IDS } from "@/fixtures/mockBeacons";
import { useBeaconScanner } from "@/hooks/useBeaconScanner";
import { useNow } from "@/hooks/useNow";
import { usePatrolSession } from "@/hooks/usePatrolSession";
import { useStationUpdates } from "@/hooks/useStationUpdates";
import { createMockBeaconScanner } from "@/services/beacon/MockBeaconScanner";
import { sortStationsByUrgency } from "@/utils/areaStatus";
import { LINE_GROUPS, type LineGroup } from "@/types/station";
import { stationServesLineGroup } from "@/utils/stationLineGroup";


/** Format a timestamp in ms since epoch as local HH:MM. */
function formatClock(timestamp: number): string {
  const date = new Date(timestamp);
  return [date.getHours(), date.getMinutes()]
    .map((part) => String(part).padStart(2, "0"))
    .join(":");
}

/**
 * Show the steward's patrol screen.
 *
 * The session slider drives the beacon scan: once the session is active the
 * mock beacon scan (first two mock beacons) starts, and it stops in every
 * other status. Confirmed connects and disconnects are logged in the terminal
 * and POSTed to the backend. Below the slider, the stations stream in over SSE,
 * are filtered by the selected line group and ordered into the round. The
 * list is empty until the first SSE event arrives.
 */
export default function Index() {
  const scanner = useMemo(
    () =>
      createMockBeaconScanner({
        android_id: MOCK_ANDROID_ID,
        beacon_ids: MOCK_BEACON_IDS.slice(0, 2),
      }),
    [],
  );
  const { state: patrolSession, start, stop } = usePatrolSession();
  const { start: startScan, stop: stopScan } = useBeaconScanner(scanner);
  const { stations, lastUpdatedAt } = useStationUpdates();
  const now = useNow();

  const [lineGroup, setLineGroup] = useState<LineGroup>(LINE_GROUPS[0]);
  const visibleStations = useMemo(
    () => stations.filter((station) => stationServesLineGroup(station, lineGroup)),
    [stations, lineGroup],
  );

  useEffect(() => {
    if (patrolSession.status === "active") {
      startScan();
    } else {
      stopScan();
    }
  }, [patrolSession.status, startScan, stopScan]);

  const round = sortStationsByUrgency(visibleStations, now);

  return (
    <View style={styles.screen}>
      <TopNavBar selected={lineGroup} onSelect={setLineGroup} />
      <ScrollView contentContainerStyle={styles.content}>
        <SessionSlider
          status={patrolSession.status}
          startedAt={patrolSession.startedAt}
          error={patrolSession.error}
          onStart={start}
          onStop={stop}
        />

        <View style={styles.stationList}>
          <StationListHeader />
          <Text style={styles.lastUpdated}>
            {lastUpdatedAt === null
              ? "Sidst opdateret..."
              : `Sidst opdateret ${formatClock(lastUpdatedAt)}`}
          </Text>
          {round.map((station) => (
            <Station key={station.name} station={station} now={now} />
          ))}
      </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: "white",
  },
  content: {
    gap: 12,
    padding: 16,
  },
  stationList: {
    borderRadius: 17,
    padding: 12,
    gap: 12,
    backgroundColor: '#e1e1e1',
  },
  lastUpdated: {
    color: "#666666",
    fontSize: 12,
  },
});
