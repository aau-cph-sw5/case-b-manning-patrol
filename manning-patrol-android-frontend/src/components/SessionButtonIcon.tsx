// the icon on the session button: play, stop, or a spinner while a request is in flight.
import { SymbolView } from "expo-symbols";
import { ActivityIndicator } from "react-native";

export type SessionButtonIconName = "play" | "stop" | "spinner";

const ICON_SIZE = 28;

// sf symbols on ios, material symbols on android and web. a platform without a name renders nothing.
const symbols = {
  play: { ios: "play", android: "play_arrow", web: "play_arrow" },
  stop: { ios: "stop", android: "stop", web: "stop" },
} as const;

type SessionButtonIconProps = {
  name: SessionButtonIconName;
  color: string;
};

export function SessionButtonIcon({ name, color }: SessionButtonIconProps) {
  if (name === "spinner") {
    return <ActivityIndicator color={color} />;
  }
  return <SymbolView name={symbols[name]} size={ICON_SIZE} tintColor={color} />;
}
