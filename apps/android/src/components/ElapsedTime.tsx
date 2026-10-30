import { Text, type StyleProp, type TextStyle } from "react-native";

import { useElapsedTime } from "@/hooks/useElapsedTime";
import { formatDuration } from "@/utils/formatDuration";

type ElapsedTimeProps = {
  startedAt: number | null;
  style?: StyleProp<TextStyle>;
};

/**
 * Show live HH:MM:SS since `startedAt`, or 00:00:00 while it is null.
 *
 * Kept in its own component so only this text re-renders every second.
 */
export function ElapsedTime({ startedAt, style }: ElapsedTimeProps) {
  const elapsed = useElapsedTime(startedAt);

  return <Text style={style}>{formatDuration(elapsed)}</Text>;
}
