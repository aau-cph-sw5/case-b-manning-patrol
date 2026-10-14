// stations due for patrol, per the figma: one row per station, timer colored by how
// long ago it was last patrolled (green under 30 min, yellow under 45, red beyond),
// most urgent first.
import { memo } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";

import { LineBadges } from "@/components/LineBadges";
import type { Station } from "@/fixtures/mockStations";

// the patrol-compliance window is one hour, so the timers stop there
const MAX_SECONDS = 60 * 60;
const GREEN_UNTIL = 30 * 60;
const YELLOW_UNTIL = 45 * 60;

const STATION_AREA_TEXT = "Perron og stationsområde";
const TIMER_COLUMN_WIDTH = 116;

type StationListProps = {
  stations: Station[];
  // seconds the current patrol session has been running
  elapsedSeconds: number;
};

function formatMinutes(totalSeconds: number) {
  return `${String(Math.floor(totalSeconds / 60)).padStart(2, "0")} min`;
}

function timerColor(totalSeconds: number) {
  if (totalSeconds < GREEN_UNTIL) {
    return { fill: "#168c4c", text: "#ffffff" };
  }
  if (totalSeconds < YELLOW_UNTIL) {
    return { fill: "#f0b51e", text: "#28220f" };
  }
  return { fill: "#dd2e2a", text: "#ffffff" };
}

// overdue first, and within a band the longest-waiting station first
function priority(totalSeconds: number) {
  if (totalSeconds >= YELLOW_UNTIL) return 2;
  if (totalSeconds >= GREEN_UNTIL) return 1;
  return 0;
}

const StationRow = memo(function StationRow({ station, elapsedSeconds }: { station: Station; elapsedSeconds: number }) {
  const rowSeconds = Math.min(station.initialSeconds + elapsedSeconds, MAX_SECONDS);
  const colors = timerColor(rowSeconds);

  return (
    <View style={[styles.row, { borderColor: colors.fill }]}>
      <View style={styles.rowStation}>
        <View style={styles.rowBadges}>
          <LineBadges lines={station.lines} />
        </View>
        <View style={styles.rowName}>
          <Text numberOfLines={1} style={styles.name}>
            {station.name}
          </Text>
          <Text numberOfLines={1} style={styles.area}>
            {STATION_AREA_TEXT}
          </Text>
        </View>
      </View>
      <View style={[styles.timer, { backgroundColor: colors.fill, borderLeftColor: colors.fill }]}>
        <Text style={[styles.timerText, { color: colors.text }]}>{formatMinutes(rowSeconds)}</Text>
      </View>
    </View>
  );
});

export function StationList({ stations, elapsedSeconds }: StationListProps) {
  const prioritized = [...stations].sort((a, b) => {
    const aTime = Math.min(a.initialSeconds + elapsedSeconds, MAX_SECONDS);
    const bTime = Math.min(b.initialSeconds + elapsedSeconds, MAX_SECONDS);
    return priority(bTime) - priority(aTime) || bTime - aTime;
  });

  return (
    <View style={styles.card}>
      <View style={styles.columnHeader}>
        <Text style={styles.columnHeaderStation}>Station</Text>
        <Text style={styles.columnHeaderTimer}>Tid siden kontrol</Text>
      </View>
      <ScrollView contentContainerStyle={styles.rows}>
        {prioritized.map((station) => (
          <StationRow key={station.name} station={station} elapsedSeconds={elapsedSeconds} />
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    minHeight: 0,
    borderRadius: 22,
    backgroundColor: "#ffffff",
    overflow: "hidden",
    elevation: 4,
  },
  columnHeader: {
    flexDirection: "row",
    backgroundColor: "#f5f3f1",
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  columnHeaderStation: {
    flex: 1,
    paddingLeft: 8,
    fontSize: 9,
    fontWeight: "700",
    letterSpacing: 1,
    color: "#746e70",
    textTransform: "uppercase",
  },
  columnHeaderTimer: {
    width: TIMER_COLUMN_WIDTH,
    textAlign: "center",
    fontSize: 9,
    fontWeight: "700",
    letterSpacing: 1,
    color: "#746e70",
    textTransform: "uppercase",
  },
  rows: {
    gap: 8,
    padding: 10,
  },
  row: {
    minHeight: 82,
    flexDirection: "row",
    borderWidth: 2,
    borderRadius: 16,
    overflow: "hidden",
  },
  rowStation: {
    flex: 1,
    minWidth: 0,
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#ffffff",
    paddingHorizontal: 14,
  },
  rowBadges: {
    width: 52,
    marginRight: 12,
    alignItems: "center",
  },
  rowName: {
    flex: 1,
    minWidth: 0,
  },
  name: {
    fontSize: 16,
    fontWeight: "700",
    color: "#211e20",
  },
  area: {
    marginTop: 2,
    fontSize: 10,
    color: "#777174",
  },
  timer: {
    width: TIMER_COLUMN_WIDTH,
    borderLeftWidth: 2,
    alignItems: "center",
    justifyContent: "center",
  },
  timerText: {
    fontFamily: "monospace",
    fontSize: 21,
    fontWeight: "700",
    fontVariant: ["tabular-nums"],
  },
});
