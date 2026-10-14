// slide-to-start / slide-to-stop control for a session. ui only: it draws the status it's given
// and reports a completed slide through onStart / onStop.
import { useState } from "react";
import {
  StyleSheet,
  Text,
  View,
  type AccessibilityActionEvent,
  type LayoutChangeEvent,
} from "react-native";
import { GestureDetector } from "react-native-gesture-handler";
import Animated from "react-native-reanimated";

import { SliderLabel } from "@/components/SliderLabel";
import { SliderThumb, THUMB_SIZE } from "@/components/SliderThumb";
import { useSlideGesture } from "@/hooks/useSlideGesture";
import type { PatrolSessionStatus } from "@/types/patrol_session/patrolSession";

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
};

type Side = "left" | "right";

type Appearance = {
  // null shows the elapsed time instead of a label
  label: string | null;
  // what a screen reader announces
  accessibilityLabel: string;
  // where the thumb rests. the label sits on the other side.
  thumbSide: Side;
  thumbColor: string;
  // green track while a session is running
  filled: boolean;
};

const appearance: Record<PatrolSessionStatus, Appearance> = {
  stopped: {
    label: "Slide to start",
    accessibilityLabel: "Start session",
    thumbSide: "left",
    thumbColor: colors.green,
    filled: false,
  },
  starting: {
    label: "Starting...",
    accessibilityLabel: "Starting session",
    thumbSide: "right",
    thumbColor: colors.green,
    filled: false,
  },
  active: {
    label: null,
    accessibilityLabel: "Stop session",
    thumbSide: "right",
    thumbColor: colors.red,
    filled: true,
  },
  stopping: {
    label: "Stopping...",
    accessibilityLabel: "Stopping session",
    thumbSide: "left",
    thumbColor: colors.red,
    filled: true,
  },
};

type SessionSliderProps = {
  status: PatrolSessionStatus;
  // when the current session started (ms since epoch), shown as elapsed time while active
  startedAt: number | null;
  // message from the last failed request, shown under the slider
  error?: string | null;
  // called when the steward slides right while stopped, or activates the slider with a screen reader
  onStart: () => void;
  // called when the steward slides left while active, or activates the slider with a screen reader
  onStop: () => void;
};

export function SessionSlider({ status, startedAt, error, onStart, onStop }: SessionSliderProps) {
  const [trackWidth, setTrackWidth] = useState(0);
  const { label, accessibilityLabel, thumbSide, thumbColor, filled } = appearance[status];
  // the label sits opposite the thumb, and the chevron points towards it
  const otherSide = thumbSide === "left" ? "right" : "left";
  // a start/stop request is in flight, so the slider is locked
  const isPending = status === "starting" || status === "stopping";
  // distance between the thumb's left and right resting positions
  const travel = Math.max(0, trackWidth - 2 * (TRACK_BORDER + THUMB_INSET) - THUMB_SIZE);
  // only used while not pending, i.e. when the status is "stopped" or "active"
  const handleSlideComplete = status === "stopped" ? onStart : onStop;

  const { gesture, thumbStyle } = useSlideGesture({
    restSide: thumbSide,
    travel,
    enabled: !isPending,
    onComplete: handleSlideComplete,
  });

  function handleTrackLayout(event: LayoutChangeEvent) {
    setTrackWidth(event.nativeEvent.layout.width);
  }

  // screen reader users can't drag, so a double tap ("activate") does the same as a full slide
  function handleAccessibilityAction(event: AccessibilityActionEvent) {
    if (event.nativeEvent.actionName === "activate" && !isPending) {
      handleSlideComplete();
    }
  }

  return (
    <View style={styles.container}>
      <View
        style={[styles.track, filled ? styles.trackFilled : styles.trackEmpty]}
        onLayout={handleTrackLayout}
        accessible
        role="button"
        accessibilityLabel={accessibilityLabel}
        accessibilityActions={[{ name: "activate" }]}
        onAccessibilityAction={handleAccessibilityAction}
        aria-busy={isPending}
        aria-disabled={isPending}
      >
        <SliderLabel text={label} startedAt={startedAt} side={otherSide} onFilledTrack={filled} />
        {/* the thumb's position depends on the track width, so wait for the first layout */}
        {trackWidth > 0 && (
          <GestureDetector gesture={gesture}>
            <Animated.View style={thumbStyle}>
              <SliderThumb color={thumbColor} pointing={otherSide} loading={isPending} />
            </Animated.View>
          </GestureDetector>
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
  error: {
    color: colors.red,
    fontSize: 14,
    textAlign: "center",
  },
});
