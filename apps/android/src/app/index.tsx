// the steward's patrol screen. the session slider drives everything below it: swiping
// start opens the patrol session and starts the mock beacon scan at once; swiping stop ends both.
// every event the scanner produces prints in the terminal and is forwarded to the
// backend as it arrives.
import { useEffect, useMemo } from "react";
import { ScrollView, StyleSheet, Text } from "react-native";

import { SessionSlider } from "@/components/SessionSlider";
import { MOCK_ANDROID_ID, MOCK_BEACON_IDS } from "@/fixtures/mockBeacons";
import { useBeaconScanner } from "@/hooks/useBeaconScanner";
import { usePatrolSession } from "@/hooks/usePatrolSession";
import { createMockBeaconScanner } from "@/services/beacon/MockBeaconScanner";

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
  const { state: scan, start: startScan, stop: stopScan } = useBeaconScanner(scanner);

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
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <SessionSlider
        status={patrolSession.status}
        startedAt={patrolSession.startedAt}
        error={patrolSession.error}
        onStart={start}
        onStop={stop}
      />

      <Text style={styles.section}>
        {scan.scanning ? "Scanning (mock)" : "Not scanning"}
      </Text>

      <Text style={styles.subsection}>Connected beacons</Text>
      {scan.connectedBeaconIds.length === 0 ? (
        <Text style={styles.empty}>None</Text>
      ) : (
        scan.connectedBeaconIds.map((beaconId) => (
          <Text key={beaconId} style={styles.beacon}>
            {beaconId}
          </Text>
        ))
      )}

      <Text style={styles.subsection}>Recent events</Text>
      {scan.recentEvents.map((event) => (
        <Text key={`${event.timestamp}-${event.beacon_id}`} style={styles.event}>
          {event.event === "CONNECTED" ? "+" : "-"} {event.beacon_id} at {event.timestamp}
        </Text>
      ))}
    </ScrollView>
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
  section: {
    fontSize: 16,
    fontWeight: "bold",
  },
  subsection: {
    fontSize: 14,
    fontWeight: "bold",
  },
  empty: {
    fontSize: 14,
    color: "gray",
  },
  beacon: {
    fontSize: 14,
  },
  event: {
    fontSize: 12,
    fontFamily: undefined,
  },
});
