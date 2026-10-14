// top bar per the figma: metro branding plus the M1/M2 vs M3/M4 mode switch.
import { Pressable, StyleSheet, Text, View } from "react-native";

import { LineBadges } from "@/components/LineBadges";
import { MODE_LINES, type StationMode } from "@/fixtures/mockStations";

type StationHeaderProps = {
  mode: StationMode;
  onModeChange: (mode: StationMode) => void;
};

export function StationHeader({ mode, onModeChange }: StationHeaderProps) {
  return (
    <View style={styles.banner}>
      <View style={styles.card}>
        <View style={styles.identity}>
          <View style={styles.logo}>
            <Text style={styles.logoText}>M</Text>
          </View>
          <View>
            <Text style={styles.title}>Stationskontrol</Text>
            <Text style={styles.subtitle}>Metrodrift</Text>
          </View>
        </View>
        <View style={styles.toggle}>
          {(["m1/m2", "m3/m4"] as const).map((item) => (
            <Pressable
              key={item}
              onPress={() => onModeChange(item)}
              style={[styles.toggleOption, mode === item && styles.toggleOptionActive]}
              accessibilityState={{ selected: mode === item }}
              accessibilityLabel={item === "m1/m2" ? "Vis M1 og M2" : "Vis M3 og M4"}
            >
              <LineBadges lines={MODE_LINES[item]} />
            </Pressable>
          ))}
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  banner: {
    backgroundColor: "#6e021c",
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  card: {
    minHeight: 54,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    borderRadius: 16,
    backgroundColor: "#ffffff",
    paddingHorizontal: 14,
    paddingVertical: 8,
    elevation: 6,
  },
  identity: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },
  logo: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: "#e40037",
    alignItems: "center",
    justifyContent: "center",
  },
  logoText: {
    fontSize: 18,
    fontWeight: "900",
    color: "#ffffff",
  },
  title: {
    fontSize: 13,
    fontWeight: "700",
    color: "#e40037",
  },
  subtitle: {
    marginTop: 2,
    fontSize: 10,
    color: "#797477",
  },
  toggle: {
    flexDirection: "row",
    backgroundColor: "#efedeb",
    borderRadius: 999,
    padding: 4,
  },
  toggleOption: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 999,
    opacity: 0.5,
  },
  toggleOptionActive: {
    backgroundColor: "#ffffff",
    opacity: 1,
    elevation: 2,
  },
});
