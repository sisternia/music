import { Stack } from 'expo-router';
import Constants from 'expo-constants';
import { Platform, StyleSheet, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import HomeWorkspace, { type WorkspaceView } from './HomeWorkspace';

const screenTitles: Record<WorkspaceView, string> = {
  new: 'New transcription | Harmony Auralis',
  piano: 'Piano | Harmony Auralis',
  projects: 'Projects | Harmony Auralis',
  collections: 'Collections | Harmony Auralis',
};

export default function HomeWeb({ initialView = 'new' }: { initialView?: WorkspaceView }) {
  const insets = useSafeAreaInsets();
  const nativeHost = Platform.OS !== 'web';
  const devHost = Constants.expoConfig?.hostUri?.split(':')[0];
  const apiUrl = process.env.EXPO_PUBLIC_PIANO_API_URL || (nativeHost && devHost ? `http://${devHost}:8001` : undefined);

  return (
    <View style={[styles.screen, nativeHost && {
      paddingTop: insets.top,
      paddingBottom: insets.bottom,
      paddingLeft: insets.left,
      paddingRight: insets.right,
    }]}>
      <Stack.Screen options={{ title: screenTitles[initialView], headerShown: false }} />
      <HomeWorkspace
        apiUrl={apiUrl}
        nativeHost={nativeHost}
        initialView={initialView}
        dom={nativeHost ? {
          useExpoDOMWebView: false,
          style: { flex: 1 },
          scrollEnabled: false,
          mediaPlaybackRequiresUserAction: false,
          allowsInlineMediaPlayback: true,
          allowFileAccess: true,
          allowFileAccessFromFileURLs: true,
        } : undefined}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    minHeight: 0,
    backgroundColor: '#faf8f3',
    overflow: 'hidden',
  },
});
