// the steward's patrol screen, laid out per the figma template. the session slider
// drives everything below it: swiping start opens the patrol session and starts the
// mock beacon scan at once; swiping stop ends both. every event the scanner produces
// prints in the terminal and is forwarded to the backend as it arrives.
import { useEffect, useMemo, useState } from "react";
import { SafeAreaView, StyleSheet, Text, View } from "react-native";

import { BottomNav } from "@/components/BottomNav";
import { SessionSlider } from "@/components/SessionSlider";
import { StationHeader } from "@/components/StationHeader";
import { StationList } from "@/components/StationList";
import { MOCK_ANDROID_ID, MOCK_BEACON_IDS } from "@/fixtures/mockBeacons";
import { MODE_LINES, stations, type StationMode } from "@/fixtures/mockStations";
import { useBeaconScanner } from "@/hooks/useBeaconScanner";
import { useElapsedTime } from "@/hooks/useElapsedTime";
import { usePatrolSession } from "@/hooks/usePatrolSession";
import { createMockBeaconScanner } from "@/services/beacon/MockBeaconScanner";

export default function Index() {
  const [mode, setMode] = useState<StationMode>("m1/m2");

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

  // station timers advance with the live session; startedAt is null while stopped,
  // so they fall back to the seeded mock times
  const sessionElapsed = useElapsedTime(patrolSession.startedAt);
  const elapsedSeconds = Math.floor(sessionElapsed / 1000);

  const visibleStations = useMemo(
    () =>
      stations.filter((station) =>
        station.lines.some((line) => MODE_LINES[mode].includes(line)),
      ),
    [mode],
  );

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.screen}>
        <StationHeader mode={mode} onModeChange={setMode} />

        <View style={styles.body}>
          <View style={styles.sliderCard}>
            <SessionSlider
              status={patrolSession.status}
              startedAt={patrolSession.startedAt}
              error={patrolSession.error}
              onStart={start}
              onStop={stop}
            />
            <Text style={styles.scanStatus}>
              {scan.scanning ? "Scanning (mock)" : "Not scanning"}
            </Text>
          </View>

          <StationList stations={visibleStations} elapsedSeconds={elapsedSeconds} />
        </View>

        <BottomNav />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: "#f3f1ef",
  },
  screen: {
    flex: 1,
  },
  body: {
    flex: 1,
    minHeight: 0,
    paddingHorizontal: 14,
    paddingTop: 14,
    gap: 14,
  },
  sliderCard: {
    borderRadius: 22,
    backgroundColor: "#ffffff",
    padding: 10,
    elevation: 4,
  },
  scanStatus: {
    marginTop: 8,
    textAlign: "center",
    fontSize: 10,
    color: "#777174",
  },
});
