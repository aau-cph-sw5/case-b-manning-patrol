import { ScrollView, StyleSheet } from "react-native";
import { SessionSlider } from "@/components/SessionSlider";

// temporary preview of every slider state, replaced by a working demo once the slider can be dragged
export default function Index() {
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <SessionSlider status="stopped" />
      <SessionSlider status="starting" />
      <SessionSlider status="active" />
      <SessionSlider status="stopping" />
      <SessionSlider status="stopped" error="Could not start the session. Try again." />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    justifyContent: "center",
    gap: 32,
    padding: 16,
    backgroundColor: "white",
  },
});
