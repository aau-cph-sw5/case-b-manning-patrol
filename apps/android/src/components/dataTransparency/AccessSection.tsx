/** Access section of the data transparency screen: who may see the data. */

import { StyleSheet, Text, View } from "react-native";

import { ACCESS_RULES } from "@/data/dataTransparency";

/**
 * Render the "Hvem kan se dine data?" heading and one row per role of the
 * five-role access model, which applies to every category on the screen.
 */
export function AccessSection() {
  return (
    <View>
      <Text style={styles.heading}>Hvem kan se dine data?</Text>
      <Text style={styles.note}>Gælder alle kategorier ovenfor.</Text>
      <View style={styles.list}>
        {ACCESS_RULES.map((rule) => (
          <View key={rule.role} style={styles.row}>
            <Text style={styles.role}>{rule.role}</Text>
            <Text style={styles.access}>{rule.access}</Text>
          </View>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  heading: {
    color: "#202220",
    fontSize: 18,
    fontWeight: "700",
  },
  note: {
    marginTop: 2,
    marginBottom: 10,
    color: "#656865",
    fontSize: 12,
  },
  list: {
    padding: 8,
    gap: 8,
    borderRadius: 20,
    backgroundColor: "#f0f0ee",
  },
  row: {
    gap: 2,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  role: {
    color: "#202220",
    fontSize: 14,
    fontWeight: "700",
  },
  access: {
    color: "#3c3c3c",
    fontSize: 13,
    lineHeight: 18,
  },
});
