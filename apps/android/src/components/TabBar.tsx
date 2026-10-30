import { Feather } from "@expo/vector-icons";
import type { BottomTabBarProps } from "expo-router/build/react-navigation/bottom-tabs";
import { Pressable, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

const TAB_ICONS: Record<string, React.ComponentProps<typeof Feather>["name"]> = {
  dataTransparency: "settings",
  index: "home",
  patrolHistory: "folder",
};

/** Render the bottom tab bar with icon-only buttons; screen readers get each screen's title as the label. */
export default function TabBar({ state, descriptors, navigation }: BottomTabBarProps) {
  return (
    <SafeAreaView edges={["bottom"]} style={styles.bar}>
      <View style={styles.row}>
        {state.routes.map((route, index) => {
          const active = state.index === index;
          const icon = TAB_ICONS[route.name] ?? "square";
          const label = descriptors[route.key].options.title ?? route.name;

          return (
            <Pressable
              key={route.key}
              onPress={() => navigation.navigate(route.name, route.params)}
              style={styles.item}
              accessibilityRole="tab"
              accessibilityLabel={label}
              accessibilityState={{ selected: active }}
            >
              <View style={[styles.iconButton, active && styles.iconButtonActive]}>
                <Feather name={icon} size={20} color="#ffffff" />
              </View>
            </Pressable>
          );
        })}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  bar: {
    marginHorizontal: 12,
    marginBottom: 8,
    borderRadius: 24,
    backgroundColor: "#940024",
  },
  row: {
    height: 60,
    flexDirection: "row",
    alignItems: "center",
  },
  item: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  iconButton: {
    width: 44,
    height: 44,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 14,
  },
  iconButtonActive: {
    backgroundColor: "#ed2224",
  },
});
