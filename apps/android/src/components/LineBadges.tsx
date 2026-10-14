// metro line badges, drawn per the figma: a small circle per line, stacked as a
// triangle when a station serves three lines.
import { StyleSheet, Text, View } from "react-native";

import type { MetroLine } from "@/fixtures/mockStations";

const lineColors: Record<MetroLine, { bg: string; fg: string }> = {
  M1: { bg: "#009f68", fg: "#ffffff" },
  M2: { bg: "#f5c400", fg: "#211e20" },
  M3: { bg: "#e40037", fg: "#ffffff" },
  M4: { bg: "#1681c4", fg: "#ffffff" },
};

function Badge({ line }: { line: MetroLine }) {
  const { bg, fg } = lineColors[line];
  return (
    <View style={[styles.badge, { backgroundColor: bg }]}>
      <Text style={[styles.badgeText, { color: fg }]}>{line}</Text>
    </View>
  );
}

export function LineBadges({ lines }: { lines: MetroLine[] }) {
  const label = `Linjer: ${lines.join(", ")}`;

  if (lines.length === 3) {
    return (
      <View style={styles.triangle} accessible accessibilityLabel={label}>
        <View style={styles.triangleRow}>
          <Badge line={lines[0]} />
          <Badge line={lines[1]} />
        </View>
        <View style={styles.triangleBottom}>
          <Badge line={lines[2]} />
        </View>
      </View>
    );
  }

  return (
    <View style={[styles.row, lines.length === 1 && styles.rowSingle]} accessible accessibilityLabel={label}>
      {lines.map((line) => (
        <Badge key={line} line={line} />
      ))}
    </View>
  );
}

const BADGE_SIZE = 24;

const styles = StyleSheet.create({
  badge: {
    width: BADGE_SIZE,
    height: BADGE_SIZE,
    borderRadius: BADGE_SIZE / 2,
    alignItems: "center",
    justifyContent: "center",
    elevation: 2,
  },
  badgeText: {
    fontSize: 8,
    fontWeight: "900",
  },
  row: {
    flexDirection: "row",
    gap: 4,
  },
  rowSingle: {
    justifyContent: "center",
  },
  triangle: {
    alignItems: "center",
    gap: 2,
  },
  triangleRow: {
    flexDirection: "row",
    gap: 4,
  },
  triangleBottom: {
    alignItems: "center",
  },
});
