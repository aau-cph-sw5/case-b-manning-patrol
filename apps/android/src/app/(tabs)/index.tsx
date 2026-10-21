// the steward's patrol screen. the session slider drives everything below it: swiping
// start opens the patrol session and starts the mock beacon scan at once; swiping stop ends both.
// every event the scanner produces prints in the terminal and is forwarded to the
// backend as it arrives.
import { useEffect, useMemo, useState } from "react";
import { ScrollView, StyleSheet, View } from "react-native";

import Station, { StationListHeader } from "@/components/Station";
import { SessionSlider } from "@/components/SessionSlider";
import TopNavBar from "@/components/TopNavBar";
import { MOCK_ANDROID_ID, MOCK_BEACON_IDS } from "@/fixtures/mockBeacons";
import { MOCK_STATIONS } from "@/fixtures/mockStations";
import { useBeaconScanner } from "@/hooks/useBeaconScanner";
import { usePatrolSession } from "@/hooks/usePatrolSession";
import { createMockBeaconScanner } from "@/services/beacon/MockBeaconScanner";
import type { LineGroup } from "@/types/station";
import { LINE_GROUPS } from "@/types/station";
import { stationServesLineGroup } from "@/utils/stationLineGroup";

export default function Index() {
  // one scanner for the lifetime of the screen, so start/stop always talks to the same one
  
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

  // the selected line-group filter; starts on the first group and never clears
  const [lineGroup, setLineGroup] = useState<LineGroup>(LINE_GROUPS[0]);
  const visibleStations = useMemo(
    () => MOCK_STATIONS.filter((station) => stationServesLineGroup(station, lineGroup)),
    [lineGroup],
  );

  // the scan is the session's: it runs exactly while the patrol session is active (AC 1). the patrol session
  // is only active once the backend accepted the start, so a rejected start scans nothing.
  useEffect(() => {
    if (patrolSession.status === "active") {
      startScan();
    } else {
      stopScan();
    }
  }, [patrolSession.status, startScan, stopScan]);

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
          {visibleStations.map((station) => (
            <Station key={station.id} station={station} startedAt={patrolSession.startedAt} />
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
    gap: 12,
    backgroundColor: '#3333',
  },
});
