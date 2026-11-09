/**
 * The steward's patrol screen (the "Stationskontrol" tab).
 *
 * The session slider drives the beacon scan: sliding to start opens the patrol
 * session and starts the mock beacon scan; sliding to stop ends both. Every
 * event the scanner confirms is forwarded to the backend as it arrives. Below
 * the slider, the stations stream in over SSE, are filtered to the selected
 * line group and ordered into the round.
 */
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


/** Format an epoch-ms timestamp as "HH:MM" in the device's time zone. */
function formatClock(timestamp: number): string {
  const date = new Date(timestamp);
  return [date.getHours(), date.getMinutes()]
    .map((part) => String(part).padStart(2, "0"))
    .join(":");
}

/**
 * Render the patrol screen.
 *
 * The scan runs only while the session status is "active": it stops as soon
 * as a stop is requested and starts again if that stop fails. The mock scanner
 * is created once per mount and cycles through the first two mock beacons.
 * The screen re-renders every second through {@link useNow}, so the
 * countdowns and the urgency order stay current between stream events.
 */
export default function Index() {
  const scanner = useMemo(
    () =>
      createMockBeaconScanner({
        android_id: MOCK_ANDROID_ID,
        beacon_ids: MOCK_BEACON_IDS,
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
