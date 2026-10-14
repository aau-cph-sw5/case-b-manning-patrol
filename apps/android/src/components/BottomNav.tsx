// bottom navigation per the figma. the icons are drawn with views so the template
// needs no icon dependency; the labels live on the accessibility props.
import { useState } from "react";
import { Pressable, StyleSheet, View } from "react-native";

type NavId = "view" | "home" | "archive";

type NavItem = {
  id: NavId;
  label: string;
};

const NAV_ITEMS: NavItem[] = [
  { id: "view", label: "Oversigt" },
  { id: "home", label: "Hjem" },
  { id: "archive", label: "Patruljerede stationer" },
];

function EyeIcon({ color }: { color: string }) {
  return (
    <View style={[styles.eye, { borderColor: color }]}>
      <View style={[styles.eyePupil, { backgroundColor: color }]} />
    </View>
  );
}

function HomeIcon({ color }: { color: string }) {
  return (
    <View style={styles.home}>
      <View style={[styles.homeRoof, { borderBottomColor: color }]} />
      <View style={[styles.homeBody, { borderColor: color }]} />
    </View>
  );
}

function ArchiveIcon({ color }: { color: string }) {
  return (
    <View style={styles.archive}>
      <View style={[styles.archiveLid, { backgroundColor: color }]} />
      <View style={[styles.archiveBody, { borderColor: color }]}>
        <View style={[styles.archiveHandle, { backgroundColor: color }]} />
      </View>
    </View>
  );
}

function NavIcon({ name, color }: { name: NavId; color: string }) {
  if (name === "view") return <EyeIcon color={color} />;
  if (name === "home") return <HomeIcon color={color} />;
  return <ArchiveIcon color={color} />;
}

export function BottomNav() {
  const [active, setActive] = useState<NavId>("home");

  return (
    <View style={styles.nav} accessibilityLabel="Primær navigation">
      {NAV_ITEMS.map((item) => {
        const isActive = active === item.id;
        return (
          <Pressable
            key={item.id}
            onPress={() => setActive(item.id)}
            style={[styles.button, isActive && styles.buttonActive]}
            accessibilityLabel={item.label}
            accessibilityState={{ selected: isActive }}
          >
            <NavIcon name={item.id} color={isActive ? "#ffffff" : "rgba(255,255,255,0.7)"} />
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  nav: {
    flexDirection: "row",
    justifyContent: "space-around",
    height: 70,
    marginHorizontal: 14,
    marginBottom: 16,
    borderRadius: 24,
    backgroundColor: "rgba(110,2,28,0.95)",
    padding: 8,
    elevation: 8,
  },
  button: {
    width: 54,
    height: 54,
    borderRadius: 18,
    alignItems: "center",
    justifyContent: "center",
  },
  buttonActive: {
    backgroundColor: "#e40037",
    elevation: 4,
  },
  eye: {
    width: 26,
    height: 16,
    borderRadius: 8,
    borderWidth: 1.8,
    alignItems: "center",
    justifyContent: "center",
  },
  eyePupil: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  home: {
    alignItems: "center",
  },
  homeRoof: {
    width: 0,
    height: 0,
    borderLeftWidth: 11,
    borderRightWidth: 11,
    borderBottomWidth: 10,
    borderLeftColor: "transparent",
    borderRightColor: "transparent",
  },
  homeBody: {
    width: 14,
    height: 10,
    borderWidth: 1.8,
    borderRadius: 2,
    borderBottomLeftRadius: 0,
    borderBottomRightRadius: 0,
  },
  archive: {
    alignItems: "center",
  },
  archiveLid: {
    width: 20,
    height: 3,
    borderRadius: 1,
  },
  archiveBody: {
    width: 20,
    height: 12,
    borderWidth: 1.8,
    borderRadius: 2,
    borderTopWidth: 0,
    marginTop: -1,
    alignItems: "center",
  },
  archiveHandle: {
    width: 6,
    height: 2,
  },
});
