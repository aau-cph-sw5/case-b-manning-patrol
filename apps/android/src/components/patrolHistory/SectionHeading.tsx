/** Heading row for one section of the patrol history screen. */

import {
  StyleSheet,
  Text,
  View,
  type StyleProp,
  type TextStyle,
  type ViewStyle,
} from "react-native";

type SectionHeadingProps = {
  /** Section title, e.g. "Åbne forbindelser". */
  title: string;
  /** Count badge text shown on the right, e.g. "3 åbne". */
  badge: string;
  /** Style of the count badge. */
  badgeStyle?: StyleProp<TextStyle>;
  /** Extra heading style, e.g. the top margin separating the closed section. */
  headingStyle?: StyleProp<ViewStyle>;
};

/** Render the section title on the left and the count badge on the right. */
export function SectionHeading({
  title,
  badge,
  badgeStyle,
  headingStyle,
}: SectionHeadingProps) {
  return (
    <View style={[styles.heading, headingStyle]}>
      <Text style={styles.title}>{title}</Text>
      <Text style={badgeStyle}>{badge}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  heading: {
    marginBottom: 10,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  title: {
    color: "#202220",
    fontSize: 18,
    fontWeight: "700",
  },
});
