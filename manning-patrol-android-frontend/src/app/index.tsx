import { View, StyleSheet } from "react-native";
import { SessionButton } from "@/components/SessionButton";

export default function Index() {
  return (
    <View style={styles.container}>
      <SessionButton status="stopped" onPress={() => console.log("pressed")} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },
});
