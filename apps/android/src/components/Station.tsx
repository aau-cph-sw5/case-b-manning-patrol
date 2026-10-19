import { StyleSheet, Text, View } from "react-native";

import { useElapsedTime } from "@/hooks/useElapsedTime";
import type { StationRecord } from "@/types/station";

const MAX_STATION_TIME_MS = 60 * 60 * 1000;

type StationProps = {
  station: StationRecord;
  startedAt: number | null;
  platformResetAt?: number | null;
  concourseResetAt?: number | null;
};

export function StationListHeader() {
  return (
    <View style={styles.header} accessibilityRole="header">
      <View style={styles.headerDetails}>
        <Text style={[styles.headerLabel, styles.stationHeaderLabel]}>Station</Text>
      </View>
      <View style={styles.headerTimerPanel}>
        <Text style={styles.headerLabel}>Platform</Text>
        <Text style={styles.headerLabel}>Concourse</Text>
      </View>
    </View>
  );
}

export default function Station({
  station,
  startedAt,
  platformResetAt,
  concourseResetAt,
}: StationProps) {
  return (
    <View style={styles.row} accessibilityLabel={station.name}>
      <View style={styles.details}>
        {station.routeCodes?.length ? (
          <View style={styles.routes}>
            {station.routeCodes.map((routeCode) => (
              <View
                key={routeCode}
                style={[styles.routeBadge, routeColors[routeCode] ?? styles.routeDefault]}
              >
                <Text style={styles.routeText}>{routeCode}</Text>
              </View>
            ))}
          </View>
        ) : null}
        <Text style={styles.name} numberOfLines={1} ellipsizeMode="tail">
          {station.name}
        </Text>
      </View>
      <View style={styles.timerPanel}>
        <AreaTimer startedAt={platformResetAt ?? startedAt} />
        <View style={styles.timerDivider} />
        <AreaTimer startedAt={concourseResetAt ?? startedAt} />
      </View>
    </View>
  );
}

function AreaTimer({ startedAt }: { startedAt: number | null }) {
  const elapsed = useElapsedTime(startedAt);
  const minutes = Math.min(60, Math.floor(Math.min(elapsed, MAX_STATION_TIME_MS) / 60_000));

  return (
    <View style={styles.timerCell} accessibilityLabel={`${minutes} minutes`}>
      <Text style={styles.timer} accessibilityLiveRegion="polite">
        {String(minutes).padStart(2, "0")} min
      </Text>
    </View>
  );
}

const routeColors: Record<string, object> = {
  M1: { backgroundColor: "#159f72" },
  M2: { backgroundColor: "#e5b400" },
  M3: { backgroundColor: "#d90b36" },
};

const styles = StyleSheet.create({
  header: {
    height: 28,
    flexDirection: "row",
    alignItems: "center",
  },
  headerDetails: {
    flex: 1,
    minWidth: 0,
    paddingHorizontal: 10,
  },
  headerTimerPanel: {
    width: 164,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
  },
  headerLabel: {
    flex: 1,
    color: "#666666",
    fontSize: 11,
    fontWeight: "700",
    textAlign: "center",
  },
  stationHeaderLabel: {
    textAlign: "left",
  },
  row: {
    height: 84,
    flexDirection: "row",
    overflow: "hidden",
    borderWidth: 2,
    borderColor: "#ed2224",
    borderRadius: 17,
    backgroundColor: "#ffffff",
  },
  details: {
    flex: 1,
    minWidth: 0,
    justifyContent: "center",
    gap: 4,
    paddingHorizontal: 10,
  },
  routes: {
    flexDirection: "row",
    flexWrap: "wrap",
    alignItems: "center",
    gap: 3,
  },
  routeBadge: {
    minWidth: 18,
    height: 18,
    paddingHorizontal: 4,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 9,
  },
  routeDefault: {
    backgroundColor: "#686868",
  },
  routeText: {
    color: "#ffffff",
    fontSize: 7,
    fontWeight: "700",
  },
  name: {
    color: "#252525",
    fontSize: 16,
    fontWeight: "700",
  },
  timerPanel: {
    width: 164,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#e9282b",
  },
  timerCell: {
    flex: 1,
    minWidth: 0,
    alignItems: "center",
    justifyContent: "center",
    gap: 4,
  },
  timerDivider: {
    width: 1,
    height: 48,
    backgroundColor: "rgba(255, 255, 255, 0.45)",
  },
  timer: {
    color: "#ffffff",
    fontSize: 14,
    fontWeight: "700",
    fontVariant: ["tabular-nums"],
  },
});

