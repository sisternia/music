import { Redirect, useLocalSearchParams } from 'expo-router';

import HomeWeb from '@/features/user/home/screen/HomeWeb';
import type { WorkspaceView } from '@/features/user/home/screen/HomeWorkspace';

const studioRoutes: Record<string, WorkspaceView> = {
  'new-transcription': 'new',
  piano: 'piano',
  projects: 'projects',
  collections: 'collections',
};

export default function StudioPage() {
  const { studio } = useLocalSearchParams<{ studio: string }>();
  const view = studioRoutes[studio];
  return view ? <HomeWeb initialView={view} /> : <Redirect href="/new-transcription" />;
}
