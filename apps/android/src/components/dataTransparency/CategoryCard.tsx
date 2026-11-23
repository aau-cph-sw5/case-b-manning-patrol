/** Card of one data category on the data transparency screen. */

import { StyleSheet, Text, View } from "react-native";

import { RETENTION_RULE, type DataCategory } from "@/data/dataTransparency";

type CategoryCardProps = {
  /** The category to render: its plain-language title and description. */
  category: DataCategory;
};

/**
 * Render one grey panel with the category's plain-language title, what is
 * stored, and the retention rule that every category carries.
 */
export function CategoryCard({ category }: CategoryCardProps) {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>{category.title}</Text>
      <Text style={styles.description}>{category.description}</Text>
      <Text style={styles.retention}>{RETENTION_RULE}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: 8,
    padding: 16,
    borderRadius: 16,
    backgroundColor: "#f0f0ee",
  },
  title: {
    color: "#202220",
    fontSize: 16,
    fontWeight: "700",
  },
  description: {
    color: "#3c3c3c",
    fontSize: 14,
    lineHeight: 20,
  },
  retention: {
    color: "#656865",
    fontSize: 12,
    fontWeight: "700",
  },
});
