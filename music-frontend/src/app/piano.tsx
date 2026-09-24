import { PianoKeyboard } from '@/features/user/piano/components/PianoKeyboard';
import { Stack } from 'expo-router';

export default function PianoScreen() {
  return (
    <>
      <Stack.Screen options={{ title: 'Piano', headerShown: false }} />
      <PianoKeyboard />
    </>
  );
}
