// live HH:MM:SS since startedAt. kept in its own component so only this text re-renders every second.
import { Text, type StyleProp, type TextStyle } from "react-native";

import { useElapsedTime } from "@/hooks/useElapsedTime";
import { formatDuration } from "@/utils/formatDuration";

type ElapsedTimeProps = {
  startedAt: number | null;
  style?: StyleProp<TextStyle>;
};

export function ElapsedTime({ startedAt, style }: ElapsedTimeProps) {
  const elapsed = useElapsedTime(startedAt);

  return <Text style={style}>{formatDuration(elapsed)}</Text>;
}
