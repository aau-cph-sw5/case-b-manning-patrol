import { useEffect } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withTiming,
} from "react-native-reanimated";

import { routeColors } from "@/components/Station";
import { LINE_GROUPS, type LineGroup } from "@/types/station";
import { LINE_GROUP_ROUTES } from "@/utils/stationLineGroup";

type StationFilterProps = {
  selected: LineGroup;
  onSelect: (lineGroup: LineGroup) => void;
};

const SEGMENT_WIDTH = 78;
const SEGMENT_HEIGHT = 40;

/** Render a segmented control for picking the line group; the highlight slides to the selected segment. */
export default function StationFilter({ selected, onSelect }: StationFilterProps) {
  const thumbX = useSharedValue(0);

  useEffect(() => {
    thumbX.set(withTiming(selected === "M1/M2" ? 0 : SEGMENT_WIDTH, { duration: 250 }));
  }, [selected, thumbX]);

  const thumbStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: thumbX.get() }],
  }));

  return (
    <View
      style={styles.track}
      accessibilityRole="tablist"
      accessibilityLabel="Filtrer efter metrolinje"
    >
      <Animated.View style={[styles.thumb, thumbStyle]} />
      {LINE_GROUPS.map((lineGroup) => (
        <Pressable
          key={lineGroup}
          onPress={() => onSelect(lineGroup)}
          style={styles.segment}
          accessibilityRole="tab"
          accessibilityState={{ selected: selected === lineGroup }}
        >
          {LINE_GROUP_ROUTES[lineGroup].map((routeCode) => (
            <View
              key={routeCode}
              style={[styles.badge, routeColors[routeCode] ?? styles.badgeDefault]}
            >
              <Text style={styles.badgeText}>{routeCode}</Text>
            </View>
          ))}
        </Pressable>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  track: {
    position: "relative",
    flexDirection: "row",
    alignItems: "center",
    padding: 4,
    borderRadius: 24,
    borderWidth: 2,
    borderColor: "#cccccc",
    backgroundColor: "#ffffff",
  },
  thumb: {
    position: "absolute",
    top: 4,
    left: 4,
    width: SEGMENT_WIDTH,
    height: SEGMENT_HEIGHT,
    borderRadius: 20,
    borderWidth: 2,
    borderColor: "#ed2224",
    backgroundColor: "rgba(237, 34, 36, 0.12)",
  },
  segment: {
    width: SEGMENT_WIDTH,
    height: SEGMENT_HEIGHT,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 4,
  },
  badge: {
    minWidth: 24,
    height: 24,
    paddingHorizontal: 5,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 12,
  },
  badgeDefault: {
    backgroundColor: "#686868",
  },
  badgeText: {
    color: "#ffffff",
    fontSize: 9,
    fontWeight: "700",
  },
});
