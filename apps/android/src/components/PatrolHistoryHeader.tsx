/** Burgundy page header of the patrol history tab. */

import { StyleSheet, Text, View } from "react-native";

import { SafeAreaView } from "react-native-safe-area-context";

/**
 * Render the metro mark, the "METRO · PATRULJE" eyebrow and the
 * "Patruljehistorik" title below the status bar.
 */
export default function PatrolHistoryHeader() {
  return (
    <SafeAreaView edges={["top"]} style={styles.bar}>
      <View style={styles.identity} accessibilityRole="header">
        <View
          style={styles.mark}
          accessibilityElementsHidden
          importantForAccessibility="no"
        >
          <Text style={styles.markText}>M</Text>
        </View>
        <View style={styles.titles}>
          <Text style={styles.eyebrow}>METRO · PATRULJE</Text>
          <Text style={styles.title}>Patruljehistorik</Text>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  bar: {
    paddingHorizontal: 24,
    paddingVertical: 22,
    backgroundColor: "#940024",
  },
  identity: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },
  mark: {
    width: 42,
    height: 42,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 21,
    backgroundColor: "#E40037",
  },
  markText: {
    color: "#ffffff",
    fontSize: 25,
    fontWeight: "800",
  },
  titles: {
    flex: 1,
    minWidth: 0,
  },
  eyebrow: {
    color: "#ffffff",
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 1.3,
  },
  title: {
    marginTop: 3,
    color: "#ffffff",
    fontSize: 26,
    fontWeight: "700",
    lineHeight: 30,
  },
});
