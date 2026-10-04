// the round handle of the session slider: a white ring around a coloured circle.
// shows a chevron in the slide direction, or a spinner while a request is in flight.
import { SymbolView } from "expo-symbols";
import bold from "expo-symbols/androidWeights/bold";
import { ActivityIndicator, StyleSheet, View } from "react-native";

export const THUMB_SIZE = 64;
const RING_WIDTH = 6;

type Direction = "left" | "right";

// sf symbols on ios, material symbols on android and web. a platform without a name renders nothing.
const chevrons = {
  left: { ios: "chevron.left", android: "chevron_left", web: "chevron_left" },
  right: { ios: "chevron.right", android: "chevron_right", web: "chevron_right" },
} as const satisfies Record<Direction, object>;

type SliderThumbProps = {
  color: string;
  // the direction the steward should slide
  pointing: Direction;
  loading: boolean;
};

export function SliderThumb({ color, pointing, loading }: SliderThumbProps) {
  return (
    <View style={styles.ring}>
      <View style={[styles.circle, { backgroundColor: color }]}>
        {loading ? (
          <ActivityIndicator color="white" />
        ) : (
          <SymbolView
            name={chevrons[pointing]}
            weight={{ ios: "bold", android: bold }}
            size={32}
            tintColor="white"
          />
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  ring: {
    width: THUMB_SIZE,
    height: THUMB_SIZE,
    borderRadius: THUMB_SIZE / 2,
    padding: RING_WIDTH,
    backgroundColor: "white",
    boxShadow: "0px 2px 6px rgba(0, 0, 0, 0.25)",
  },
  circle: {
    flex: 1,
    borderRadius: THUMB_SIZE / 2,
    alignItems: "center",
    justifyContent: "center",
  },
});
