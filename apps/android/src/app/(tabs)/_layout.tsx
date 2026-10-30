import { Tabs } from "expo-router";

import TabBar from "@/components/TabBar";

/** Lay out the three tabs with the custom TabBar; the patrol screen (index) sits in the middle. */
export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{ headerShown: false }}
      tabBar={(props) => <TabBar {...props} />}
    >
      <Tabs.Screen name="dataTransparency" options={{ title: "Data Gennemsigtighed" }} />
      <Tabs.Screen name="index" options={{ title: "Stationskontrol" }} />
      <Tabs.Screen name="patrolHistory" options={{ title: "Patruljehistorik" }} />
    </Tabs>
  );
}
