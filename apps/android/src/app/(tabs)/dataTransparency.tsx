/**
 * The data transparency tab ("Data om dig").
 *
 * A purely informational screen: it states what the system records about the
 * steward, how long it is kept and who can see it, from the static content of
 * the data module (data/dataTransparency). Nothing is fetched or computed —
 * the categories mirror what the backend's append-only event store inserts
 * per steward, so the screen never refetches and cannot go stale in a
 * session.
 *
 * Layout follows the patrol history tab: the burgundy header stays pinned at
 * the top, everything below scrolls as a document.
 */

import { Stack } from "expo-router";

import { ScrollView, StyleSheet, Text, View } from "react-native";

import { AccessSection } from "@/components/dataTransparency/AccessSection";
import { CategoryCard } from "@/components/dataTransparency/CategoryCard";
import DataTransparencyHeader from "@/components/dataTransparency/DataTransparencyHeader";
import { DATA_CATEGORIES } from "@/data/dataTransparency";

/**
 * Render the data transparency screen: one card per kind of stored data with
 * its retention rule, followed by the five-role access model.
 */
export default function DataTransparencyScreen() {
  return (
    <View style={styles.screen}>
      <Stack.Screen options={{ title: "Data Gennemsigtighed" }} />
      <DataTransparencyHeader />
      <ScrollView
        style={styles.page}
        contentContainerStyle={styles.pageContent}
        keyboardDismissMode="on-drag"
      >
        <Text style={styles.intro}>
          Systemet registrerer følgende om dig, når du er på vagt. Kortene
          fortæller hvad der gemmes, hvor længe det opbevares, og
          hvem der kan se det.
        </Text>
        <View style={styles.categories}>
          {DATA_CATEGORIES.map((category) => (
            <CategoryCard key={category.title} category={category} />
          ))}
        </View>
        <AccessSection />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: "#ffffff",
  },
  page: {
    flex: 1,
    minHeight: 0,
  },
  pageContent: {
    paddingHorizontal: 16,
    paddingTop: 18,
    paddingBottom: 22,
    gap: 18,
  },
  intro: {
    color: "#3c3c3c",
    fontSize: 14,
    lineHeight: 20,
  },
  categories: {
    gap: 10,
  },
});
