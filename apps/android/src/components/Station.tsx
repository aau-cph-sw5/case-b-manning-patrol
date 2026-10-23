import { StyleSheet, Text, View } from "react-native";

import {
  areaStatus,
  formatCountdown,
  mostUrgentArea,
  remainingMs,
  type AreaStatus,
} from "@/utils/areaStatus";
import type { Area, Station as StationData } from "@/types/station";

type StationProps = {
  station: StationData;
  now: number;
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

export default function Station({ station, now }: StationProps) {
  const lines = [...new Set(station.areas.map((area) => area.line))];

  return (
    <View style={styles.row} accessibilityLabel={station.name}>
      <View style={styles.details}>
        {lines.length ? (
          <View style={styles.routes}>
            {lines.map((line) => (
              <View
                key={line}
                style={[styles.routeBadge, routeColors[line] ?? styles.routeDefault]}
              >
                <Text style={styles.routeText}>{line}</Text>
              </View>
            ))}
          </View>
        ) : null}
        <Text style={styles.name} numberOfLines={1} ellipsizeMode="tail">
          {station.name}
        </Text>
      </View>
      <View style={styles.timerPanel}>
        <AreaTimer area={mostUrgentArea(station.areas, "platform")} now={now} />
        <View style={styles.timerDivider} />
        <AreaTimer area={mostUrgentArea(station.areas, "concourse")} now={now} />
      </View>
    </View>
  );
}

// one deadline cell. the colour carries the risk (AC 1) and the caption says why
// a level needs no round right now: someone else is patrolling it (AC 2). an
// area with no deadline yet renders the same placeholder as a missing one.
function AreaTimer({ area, now }: { area: Area | undefined; now: number }) {
  if (!area || area.overdueAt === null) {
    return (
      <View style={[styles.timerCell, styles.missing]}>
        <Text style={styles.timer}>--</Text>
      </View>
    );
  }

  const remaining = remainingMs(area.overdueAt, now);

  if (area.coveredNow) {
    return (
      <View style={[styles.timerCell, styles.covered]}>
        <Text style={styles.timer}>{formatCountdown(remaining)}</Text>
        <Text style={styles.caption}>Patrolled</Text>
      </View>
    );
  }

  return (
    <View
      style={[styles.timerCell, statusColors[areaStatus(remaining)]]}
      accessibilityLabel={`${area.name} ${formatCountdown(remaining)}`}
    >
      <Text style={styles.timer} accessibilityLiveRegion="polite">
        {formatCountdown(remaining)}
      </Text>
      {areaStatus(remaining) === "overdue" ? (
        <Text style={styles.caption}>Overdue</Text>
      ) : null}
    </View>
  );
}

export const routeColors: Record<string, object> = {
  M1: { backgroundColor: "#2ecc71" },
  M2: { backgroundColor: "#f1c40f" },
  M3: { backgroundColor: "#e91e63" },
  M4: { backgroundColor: "#3498db" },
};

const statusColors: Record<AreaStatus, object> = {
  fresh: { backgroundColor: "#159f72" },
  due: { backgroundColor: "#e5a800" },
  overdue: { backgroundColor: "#d90b36" },
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
    color: "#000000",
    fontSize: 15,
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
    alignItems: "stretch",
    justifyContent: "center",
    backgroundColor: "#f0f0f0",
  },
  timerCell: {
    flex: 1,
    minWidth: 0,
    alignItems: "center",
    justifyContent: "center",
    gap: 4,
  },
  covered: {
    backgroundColor: "#686868",
  },
  missing: {
    backgroundColor: "#d8d8d8",
  },
  timerDivider: {
    width: 1,
    backgroundColor: "rgba(255, 255, 255, 0.45)",
  },
  timer: {
    color: "#ffffff",
    fontSize: 14,
    fontWeight: "700",
    fontVariant: ["tabular-nums"],
  },
  caption: {
    color: "#ffffff",
    fontSize: 8,
    fontWeight: "700",
  },
});
