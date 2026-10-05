// the text inside the session slider: a label, or the elapsed time while a session runs.
import { StyleSheet, Text, View } from "react-native";

import { ElapsedTime } from "@/components/ElapsedTime";

type SliderLabelProps = {
  // null shows the elapsed time instead
  text: string | null;
  // when the session started, used for the elapsed time
  startedAt: number | null;
  side: "left" | "right";
  // white text on the green track, dark text on the grey one
  onFilledTrack: boolean;
};

export function SliderLabel({ text, startedAt, side, onFilledTrack }: SliderLabelProps) {
  const color = onFilledTrack ? styles.lightText : styles.darkText;

  return (
    <View style={[StyleSheet.absoluteFill, styles.area, side === "left" ? styles.left : styles.right]}>
      {text === null ? (
        <ElapsedTime startedAt={startedAt} style={[styles.timer, color]} />
      ) : (
        <Text style={[styles.label, color]}>{text}</Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  area: {
    justifyContent: "center",
    paddingHorizontal: 28,
  },
  left: {
    alignItems: "flex-start",
  },
  right: {
    alignItems: "flex-end",
  },
  label: {
    fontSize: 20,
    fontWeight: "600",
  },
  timer: {
    fontSize: 24,
    fontWeight: "500",
    // equal-width digits so the text doesn't jitter every second
    fontVariant: ["tabular-nums"],
  },
  darkText: {
    color: "#262626",
  },
  lightText: {
    color: "white",
  },
});
