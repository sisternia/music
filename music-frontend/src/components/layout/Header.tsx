import { Image, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

export default function Header() {
  return (
    <View style={styles.header}>
      <View style={styles.left}>
        <Image
          source={require('@/assets/images/Harmony Auralis Logo.png')}
          style={styles.logo}
          resizeMode="contain"
          accessibilityLabel="Harmony Auralis Logo"
        />
      </View>

      <View style={styles.center}>
        <View style={styles.searchWrap}>
          <Text style={styles.searchIcon}>⌕</Text>
          <TextInput
            style={styles.searchInput}
            placeholder="Tìm kiếm"
            placeholderTextColor="#8e8e87"
            accessibilityLabel="Tìm kiếm"
          />
        </View>
      </View>

      <View style={styles.right}>
        <Pressable style={({ pressed }) => [styles.loginButton, pressed && styles.pressed]}>
          <Text style={styles.loginText}>Đăng nhập</Text>
        </Pressable>
        <Pressable style={({ pressed }) => [styles.signupButton, pressed && styles.pressed]}>
          <Text style={styles.signupText}>Đăng ký</Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    width: '100%',
    minHeight: 92,
    paddingHorizontal: 28,
    backgroundColor: '#f7f7f4',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 20,
  },
  left: {
    flex: 1,
    minWidth: 180,
    alignItems: 'flex-start',
    justifyContent: 'center',
  },
  logo: {
    width: 158,
    height: 46,
  },
  center: {
    flex: 2,
    minWidth: 360,
    alignItems: 'center',
    justifyContent: 'center',
  },
  searchWrap: {
    width: '100%',
    maxWidth: 760,
    height: 46,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#d9d3c8',
    backgroundColor: '#ffffff',
    paddingHorizontal: 14,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  searchIcon: {
    fontSize: 17,
    color: '#8e8e87',
    lineHeight: 17,
  },
  searchInput: {
    flex: 1,
    fontSize: 15,
    color: '#202020',
    paddingVertical: 0,
  },
  right: {
    flex: 1,
    minWidth: 260,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-end',
    gap: 10,
  },
  loginButton: {
    height: 42,
    width: 122,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#202020',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#f7f7f4',
  },
  signupButton: {
    height: 42,
    width: 122,
    borderRadius: 12,
    backgroundColor: '#202020',
    alignItems: 'center',
    justifyContent: 'center',
  },
  loginText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#202020',
  },
  signupText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#ffffff',
  },
  pressed: {
    opacity: 0.82,
  },
});
