/** Live elapsed-time text for the session slider. */
import { Text, type StyleProp, type TextStyle } from "react-native";

import { useElapsedTime } from "@/hooks/useElapsedTime";
import { formatDuration } from "@/utils/formatDuration";

type ElapsedTimeProps = {
  /** When the session started (epoch ms); null shows 00:00:00 and runs no timer. */
  startedAt: number | null;
  style?: StyleProp<TextStyle>;
};

/**
 * Show the time since `startedAt` as live HH:MM:SS.
 *
 * Kept in its own component so only this text re-renders every second.
 */
export function ElapsedTime({ startedAt, style }: ElapsedTimeProps) {
  const elapsed = useElapsedTime(startedAt);

  return <Text style={style}>{formatDuration(elapsed)}</Text>;
}
