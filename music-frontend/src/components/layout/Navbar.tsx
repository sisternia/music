import { useState } from "react";
import { usePathname, useRouter } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";

import Icon, { type IconName } from "@/components/ui/Icon";

type NavItem = {
  key: string;
  label: string;
  icon: IconName;
  href?: "/";
};

const NAV_ITEMS: NavItem[] = [
  { key: "home", label: "Trang chủ", icon: "home", href: "/" },
  { key: "community", label: "Cộng đồng yêu nhạc", icon: "community" },
  { key: "news", label: "Bản tin", icon: "news" },
  { key: "piano", label: "Piano", icon: "piano", href: "/piano" as any },
  { key: "ai", label: "AI", icon: "ai" },
  { key: "settings", label: "Cài đặt", icon: "settings" },
];

export default function Navbar() {
  const router = useRouter();
  const pathname = usePathname();
  const [hoveredKey, setHoveredKey] = useState<string | null>(null);

  return (
    <View style={styles.shell}>
      <View style={styles.mainItems}>
        {NAV_ITEMS.map((item) => {
          const active = item.href === "/" ? pathname === "/" : false;
          const hovered = hoveredKey === item.key;

          return (
            <Pressable
              key={item.key}
              accessibilityRole="button"
              accessibilityLabel={item.label}
              onPress={() => {
                if (item.href) {
                  router.push(item.href);
                }
              }}
              onHoverIn={() => setHoveredKey(item.key)}
              onHoverOut={() =>
                setHoveredKey((current) => (current === item.key ? null : current))
              }
              style={({ pressed }) => [
                styles.item,
                active && styles.itemActive,
                hovered && !active && styles.itemHover,
                pressed && styles.itemPressed,
              ]}
            >
              <Icon
                name={item.icon}
                color={active ? "#ffffff" : hovered ? "#202020" : "#aaa59b"}
                size={21}
              />

              {hovered ? (
                <View style={styles.tooltip}>
                  <Text numberOfLines={1} style={styles.tooltipText}>
                    {item.label}
                  </Text>
                </View>
              ) : null}
            </Pressable>
          );
        })}
      </View>

      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Hướng dẫn"
        onHoverIn={() => setHoveredKey("help")}
        onHoverOut={() => setHoveredKey((current) => (current === "help" ? null : current))}
        style={({ pressed }) => [styles.help, pressed && styles.itemPressed]}
      >
        <Text style={styles.helpIcon}>?</Text>
        {hoveredKey === "help" ? (
          <View style={styles.tooltip}>
            <Text numberOfLines={1} style={styles.tooltipText}>
              Hướng dẫn
            </Text>
          </View>
        ) : null}
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  shell: {
    width: 72,
    borderRightWidth: 1,
    borderRightColor: "#efeee9",
    backgroundColor: "rgba(255,255,255,0.68)",
    paddingVertical: 24,
    alignItems: "center",
    justifyContent: "space-between",
    zIndex: 40,
  },
  mainItems: {
    width: "100%",
    alignItems: "center",
    gap: 16,
  },
  item: {
    width: 46,
    height: 46,
    borderRadius: 16,
    alignItems: "center",
    justifyContent: "center",
    position: "relative",
  },
  itemActive: {
    backgroundColor: "#202020",
    shadowColor: "#000",
    shadowOpacity: 0.18,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 5 },
    elevation: 4,
    transform: [{ scale: 1.04 }],
  },
  itemHover: {
    backgroundColor: "#f4f3ef",
  },
  itemPressed: {
    opacity: 0.75,
  },
  tooltip: {
    position: "absolute",
    left: 58,
    top: 10,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: "#202020",
    shadowColor: "#000",
    shadowOpacity: 0.18,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 4 },
    zIndex: 99,
    alignSelf: "flex-start",
  },
  tooltipText: {
    color: "#fff",
    fontSize: 11,
    lineHeight: 13,
    fontWeight: "800",
  },
  help: {
    width: 40,
    height: 40,
    borderRadius: 13,
    alignItems: "center",
    justifyContent: "center",
    position: "relative",
  },
  helpIcon: {
    color: "#aaa59b",
    fontSize: 19,
    fontWeight: "900",
  },
});
