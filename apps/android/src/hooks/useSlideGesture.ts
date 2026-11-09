/** Drag-to-confirm gesture for a slider thumb. */
import { useEffect } from "react";
import { Gesture } from "react-native-gesture-handler";
import {
  clamp,
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  withTiming,
} from "react-native-reanimated";
import { scheduleOnRN } from "react-native-worklets";

/** Share of the way the thumb must be dragged before the slide counts. */
const COMPLETE_AT = 0.8;

type SlideGestureOptions = {
  /** Side the thumb rests on; a change animates the thumb there. */
  restSide: "left" | "right";
  /** Distance in points between the left and right ends; 0 disables the gesture. */
  travel: number;
  enabled: boolean;
  /** Called on the JS thread when a slide completes. */
  onComplete: () => void;
};

/**
 * Build the pan gesture and animated style for a slider thumb.
 *
 * The thumb rests on one side; dragging it far enough towards the other side
 * completes the slide, anything less springs it back. Position is tracked as
 * progress (0 = left end, 1 = right end) so it does not depend on the track
 * width. The gesture only activates after a clear sideways move, so vertical
 * scrolling still works.
 *
 * After a completed slide the thumb stays at the far end until `restSide`
 * changes, which the caller does by moving to the next status.
 *
 * @returns The gesture for a `GestureDetector` and the style for the thumb's
 *   `Animated.View`.
 */
export function useSlideGesture({ restSide, travel, enabled, onComplete }: SlideGestureOptions) {
  const restProgress = restSide === "left" ? 0 : 1;
  const progress = useSharedValue(restProgress);
  const dragStart = useSharedValue(restProgress);

  // move the thumb when the resting side changes, e.g. a failed start sends it back to the left
  useEffect(() => {
    progress.set(withTiming(restProgress, { duration: 250 }));
  }, [progress, restProgress]);

  // callbacks run on the ui thread, so react callbacks go through scheduleOnRN
  const gesture = Gesture.Pan()
    .enabled(enabled && travel > 0)
    // only start after a clear sideways move, so vertical scrolling still works
    .activeOffsetX([-10, 10])
    .failOffsetY([-15, 15])
    .onStart(() => {
      dragStart.set(progress.get());
    })
    .onUpdate((event) => {
      progress.set(clamp(dragStart.get() + event.translationX / travel, 0, 1));
    })
    .onEnd(() => {
      const moved = Math.abs(progress.get() - restProgress);
      if (moved < COMPLETE_AT) {
        progress.set(withSpring(restProgress));
        return;
      }
      progress.set(withTiming(1 - restProgress, { duration: 120 }));
      scheduleOnRN(onComplete);
    });

  const thumbStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: progress.get() * travel }],
  }));

  return { gesture, thumbStyle };
}
