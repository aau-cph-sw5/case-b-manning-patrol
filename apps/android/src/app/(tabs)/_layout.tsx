import { Tabs } from "expo-router";

import TabBar from "@/components/TabBar";

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{ headerShown: false }}
      tabBar={(props) => <TabBar {...props} />}
    >
      <Tabs.Screen name="dataTransparency" options={{ title: "Data Transparency" }} />
      <Tabs.Screen name="index" options={{ title: "Patrol" }} />
      <Tabs.Screen name="patrolHistory" options={{ title: "Patrol History" }} />
    </Tabs>
  );
}
