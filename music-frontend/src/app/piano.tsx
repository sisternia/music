import { PianoKeyboard } from '@/features/user/piano/screen/PianoKeyboard';
import { Stack } from 'expo-router';
import { StyleSheet, View } from 'react-native';

import Header from '@/components/layout/Header';
import Navbar from '@/components/layout/Navbar';

export default function PianoScreen() {
  return (
    <View style={styles.screen}>
      <Stack.Screen options={{ title: 'Piano', headerShown: false }} />
      <Header />
      <View style={styles.content}>
        <Navbar />
        <View style={styles.stage}>
          <PianoKeyboard />
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: '#fcfcfb',
    overflow: 'hidden',
  },
  content: {
    flex: 1,
    minHeight: 0,
    flexDirection: 'row',
  },
  stage: {
    flex: 1,
    minWidth: 0,
    minHeight: 0,
    overflow: 'hidden',
  },
});
