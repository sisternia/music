import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { MaxContentWidth, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

const HIGHLIGHTS = [
  'Giao dien nay da duoc don gon de tranh loi do file bi xoa.',
  'Khong con phu thuoc vao cac component mau khong ton tai.',
  'Tap trung vao noi dung co ban de app chay on dinh hon.',
];

export default function TabTwoScreen() {
  const insets = useSafeAreaInsets();
  const theme = useTheme();

  return (
    <ScrollView
      style={[styles.scrollView, { backgroundColor: theme.background }]}
      contentContainerStyle={[
        styles.contentContainer,
        {
          paddingTop: insets.top + Spacing.five,
          paddingBottom: insets.bottom + Spacing.five,
        },
      ]}>
      <View style={[styles.card, { backgroundColor: theme.backgroundElement }]}>
        <Text style={[styles.kicker, { color: theme.textSecondary }]}>Explore</Text>
        <Text style={[styles.title, { color: theme.text }]}>
          Trang nay da duoc sua lai
        </Text>
        <Text style={[styles.description, { color: theme.textSecondary }]}>
          Minh da loai bo cac import cu cua template de ban khong con gap loi khi
          da xoa file du thua.
        </Text>

        <View style={styles.list}>
          {HIGHLIGHTS.map((item) => (
            <View
              key={item}
              style={[styles.bulletRow, { borderColor: theme.backgroundSelected }]}>
              <View
                style={[styles.bulletDot, { backgroundColor: theme.textSecondary }]}
              />
              <Text style={[styles.bulletText, { color: theme.text }]}>{item}</Text>
            </View>
          ))}
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scrollView: {
    flex: 1,
  },
  contentContainer: {
    alignItems: 'center',
    paddingHorizontal: Spacing.four,
  },
  card: {
    width: '100%',
    maxWidth: MaxContentWidth,
    borderRadius: 24,
    padding: Spacing.five,
    gap: Spacing.three,
  },
  kicker: {
    fontSize: 13,
    fontWeight: '700',
    letterSpacing: 1.2,
    textTransform: 'uppercase',
  },
  title: {
    fontSize: 28,
    lineHeight: 34,
    fontWeight: '800',
  },
  description: {
    fontSize: 16,
    lineHeight: 24,
  },
  list: {
    gap: Spacing.two,
    marginTop: Spacing.two,
  },
  bulletRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: Spacing.two,
    borderWidth: 1,
    borderRadius: 16,
    padding: Spacing.three,
  },
  bulletDot: {
    width: 8,
    height: 8,
    borderRadius: 999,
    marginTop: 8,
  },
  bulletText: {
    flex: 1,
    fontSize: 15,
    lineHeight: 22,
  },
});
