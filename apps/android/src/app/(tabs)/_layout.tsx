/** Expo Router layout for the tab group: the steward's three screens. */
import { Tabs } from "expo-router";

import { StyleSheet, View } from "react-native";

import TabBar from "@/components/TabBar";

/**
 * Render the three tabs without headers, using {@link TabBar} instead of the
 * default bar.
 *
 * The titles set here are not shown; the tab bar uses them as accessibility
 * labels.
 */
export default function TabLayout() {
  return (
    <View style={styles.tabsContainer}>
      <Tabs
        screenOptions={{ headerShown: false }}
        tabBar={(props) => <TabBar {...props} />}
      >
        <Tabs.Screen name="dataTransparency" options={{ title: "Data Gennemsigtighed" }} />
        <Tabs.Screen name="index" options={{ title: "Stationskontrol" }} />
        <Tabs.Screen name="patrolHistory" options={{ title: "Patruljehistorik" }} />
      </Tabs>
    </View>
  );
}

const styles = StyleSheet.create({
  // White backdrop for the whole tab layout, so the pinned strip behind the
  // red tab bar (its margins and the OS-navbar inset) is white, not grey.
  tabsContainer: {
    flex: 1,
    backgroundColor: "#ffffff",
  },
});
