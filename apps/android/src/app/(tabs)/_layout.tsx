import { Tabs } from "expo-router";
import { StyleSheet } from "react-native";
import { GestureHandlerRootView } from "react-native-gesture-handler";

export default function TabLayout() {
  return (
    <GestureHandlerRootView style={styles.root}>
      <Tabs>
        <Tabs.Screen name="patrolHistory" options={{ title: "Patrol History" }} />
        <Tabs.Screen name="index" options={{ title: "Patrol" }} />
        <Tabs.Screen name="dataTransparency" options={{ title: "Data Transparency" }} />
      </Tabs>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
  },
});
