// demo of the mock beacon scanner: a steward's phone that "walks past" beacons. the real
// BLE scanner and the api calls that forward these events to the backend belong to other
// tickets; this screen shows the events the mock produces.
import { useMemo } from "react";
import { Button, ScrollView, StyleSheet, Text, View } from "react-native";

import { useBeaconScanner } from "@/hooks/useBeaconScanner";
import { MOCK_ANDROID_ID } from "@/services/beacon/mockBeacons";
import { createMockBeaconScanner } from "@/services/beacon/MockBeaconScanner";

export default function BeaconScreen() {
  // one scanner for the lifetime of the screen, so start/stop always talks to the same one
  const scanner = useMemo(() => createMockBeaconScanner({ android_id: MOCK_ANDROID_ID }), []);
  const { state, start, stop } = useBeaconScanner(scanner);

  return (
    <View style={styles.container}>
      <Text style={styles.heading}>Beacon scanner</Text>
      <Text style={styles.statusText}>
        {state.scanning ? "Scanning (mock)" : "Not scanning"}
      </Text>
      {state.scanning ? (
        <Button title="Stop scanning" onPress={stop} />
      ) : (
        <Button title="Start scanning" onPress={start} />
      )}

      <Text style={styles.section}>Connected beacons</Text>
      {state.connectedBeaconIds.length === 0 ? (
        <Text style={styles.empty}>None</Text>
      ) : (
        state.connectedBeaconIds.map((beaconId) => (
          <Text key={beaconId} style={styles.beacon}>
            {beaconId}
          </Text>
        ))
      )}

      <Text style={styles.section}>Recent events</Text>
      <ScrollView style={styles.log}>
        {state.recentEvents.map((event) => (
          <Text key={`${event.timestamp}-${event.beacon_id}`} style={styles.event}>
            {event.event === "CONNECTED" ? "+" : "-"} {event.beacon_id} at {event.timestamp}
          </Text>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    gap: 16,
    padding: 16,
    backgroundColor: "white",
  },
  heading: {
    fontSize: 24,
    fontWeight: "bold",
  },
  statusText: {
    fontSize: 16,
  },
  section: {
    fontSize: 16,
    fontWeight: "bold",
  },
  empty: {
    fontSize: 14,
    color: "gray",
  },
  beacon: {
    fontSize: 14,
  },
  log: {
    flex: 1,
  },
  event: {
    fontSize: 12,
    fontFamily: undefined,
  },
});
