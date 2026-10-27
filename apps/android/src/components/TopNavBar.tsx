import { StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import StationFilter from "@/components/StationFilter";
import type { LineGroup } from "@/types/station";

type TopNavBarProps = {
  selected: LineGroup;
  onSelect: (lineGroup: LineGroup) => void;
};

export default function TopNavBar({ selected, onSelect }: TopNavBarProps) {
  return (
    <SafeAreaView edges={["top"]} style={styles.bar}>
      <View style={styles.card}>
        <View style={styles.logo}>
          <Text style={styles.logoText}>M</Text>
        </View>
        <View style={styles.titles}>
          <Text style={styles.title}>Stationskontrol</Text>
          <Text style={styles.subtitle}>Metrodrift</Text>
        </View>
        <StationFilter selected={selected} onSelect={onSelect} />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  bar: {
    backgroundColor: "#940024",
  },
  card: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    margin: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 16,
    backgroundColor: "#ffffff",
  },
  logo: {
    width: 34,
    height: 34,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 17,
    backgroundColor: "#E40037",
  },
  logoText: {
    color: "#ffffff",
    fontSize: 18,
    fontWeight: "700",
  },
  titles: {
    flex: 1,
    minWidth: 0,
  },
  title: {
    color: "#252525",
    fontSize: 15,
    fontWeight: "700",
  },
  subtitle: {
    color: "#666666",
    fontSize: 11,
  },
});
