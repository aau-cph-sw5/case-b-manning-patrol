// slide-to-start / slide-to-stop control for a session. ui only: it draws the status it's given.
import { useState } from "react";
import { StyleSheet, Text, View, type LayoutChangeEvent } from "react-native";

import { SliderThumb, THUMB_SIZE } from "@/components/SliderThumb";
import type { SessionStatus } from "@/types/session";

const TRACK_HEIGHT = 76;
const TRACK_BORDER = 4;
// gap between the inside of the track border and the thumb
const THUMB_INSET = (TRACK_HEIGHT - 2 * TRACK_BORDER - THUMB_SIZE) / 2;

const colors = {
  green: "#3f9e7c",
  red: "#c8313b",
  trackEmpty: "#e5e7eb",
  trackEmptyBorder: "#f3f4f6",
  trackFilled: "#6fbfa6",
  trackFilledBorder: "#4caf8c",
  text: "#262626",
};

type Side = "left" | "right";

type Appearance = {
  // null shows the elapsed time instead of a label
  label: string | null;
  // where the thumb rests. the label sits on the other side.
  thumbSide: Side;
  thumbColor: string;
  // green track while a session is running
  filled: boolean;
};

const appearance: Record<SessionStatus, Appearance> = {
  stopped: { label: "Slide to start", thumbSide: "left", thumbColor: colors.green, filled: false },
  starting: { label: "Starting...", thumbSide: "right", thumbColor: colors.green, filled: false },
  active: { label: null, thumbSide: "right", thumbColor: colors.red, filled: true },
  stopping: { label: "Stopping...", thumbSide: "left", thumbColor: colors.red, filled: true },
};

type SessionSliderProps = {
  status: SessionStatus;
  // message from the last failed request, shown under the slider
  error?: string | null;
};

export function SessionSlider({ status, error }: SessionSliderProps) {
  const [trackWidth, setTrackWidth] = useState(0);
  const { label, thumbSide, thumbColor, filled } = appearance[status];
  // a start/stop request is in flight
  const isPending = status === "starting" || status === "stopping";
  // distance between the thumb's left and right resting positions
  const travel = Math.max(0, trackWidth - 2 * (TRACK_BORDER + THUMB_INSET) - THUMB_SIZE);

  function handleTrackLayout(event: LayoutChangeEvent) {
    setTrackWidth(event.nativeEvent.layout.width);
  }

  return (
    <View style={styles.container}>
      <View
        style={[styles.track, filled ? styles.trackFilled : styles.trackEmpty]}
        onLayout={handleTrackLayout}
        aria-busy={isPending}
      >
        <View
          style={[
            StyleSheet.absoluteFill,
            styles.labelArea,
            thumbSide === "left" ? styles.labelRight : styles.labelLeft,
          ]}
        >
          {label === null ? (
            <Text style={[styles.timer, styles.textOnFilled]}>00:00:00</Text>
          ) : (
            <Text style={[styles.label, filled && styles.textOnFilled]}>{label}</Text>
          )}
        </View>
        {/* the thumb's position depends on the track width, so wait for the first layout */}
        {trackWidth > 0 && (
          <View style={{ transform: [{ translateX: thumbSide === "right" ? travel : 0 }] }}>
            <SliderThumb
              color={thumbColor}
              pointing={thumbSide === "left" ? "right" : "left"}
              loading={isPending}
            />
          </View>
        )}
      </View>
      {/* ternary, not &&: an empty string would be rendered outside <Text> and crash */}
      {error ? <Text style={styles.error}>{error}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignSelf: "stretch",
    gap: 12,
  },
  track: {
    height: TRACK_HEIGHT,
    borderRadius: TRACK_HEIGHT / 2,
    borderWidth: TRACK_BORDER,
    paddingHorizontal: THUMB_INSET,
    flexDirection: "row",
    alignItems: "center",
  },
  trackEmpty: {
    backgroundColor: colors.trackEmpty,
    borderColor: colors.trackEmptyBorder,
  },
  trackFilled: {
    backgroundColor: colors.trackFilled,
    borderColor: colors.trackFilledBorder,
  },
  labelArea: {
    justifyContent: "center",
    paddingHorizontal: 28,
  },
  labelLeft: {
    alignItems: "flex-start",
  },
  labelRight: {
    alignItems: "flex-end",
  },
  label: {
    color: colors.text,
    fontSize: 20,
    fontWeight: "600",
  },
  timer: {
    fontSize: 24,
    fontWeight: "500",
    // equal-width digits so the text doesn't jitter every second
    fontVariant: ["tabular-nums"],
  },
  textOnFilled: {
    color: "white",
  },
  error: {
    color: colors.red,
    fontSize: 14,
    textAlign: "center",
  },
});
