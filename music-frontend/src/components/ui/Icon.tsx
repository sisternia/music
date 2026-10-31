import { useMemo } from 'react';
import { Image } from 'expo-image';
import type { ImageStyle, StyleProp } from 'react-native';

export type IconName =
  | 'home' | 'community' | 'news' | 'ai' | 'settings' | 'play' | 'pause'
  | 'previous' | 'next' | 'volumeMute' | 'volumeLow' | 'volumeMedium'
  | 'volumeHigh' | 'layers' | 'piano';

type IconProps = { name: IconName; color?: string; size?: number; style?: StyleProp<ImageStyle> };

const shapes: Record<IconName, string> = {
  home: '<path d="M4 10.5 12 4l8 6.5M6.5 9.5V20h11V9.5M10 20v-5h4v5"/>',
  community: '<circle cx="9" cy="8" r="2.2"/><circle cx="16.2" cy="9.2" r="1.8"/><path d="M4.8 18c.7-2.7 2.8-4.5 5.2-4.5s4.5 1.8 5.2 4.5M13.4 18c.5-1.8 1.8-3 3.5-3 1.5 0 2.8 1 3.3 3"/>',
  news: '<path d="M5 5h13a1 1 0 0 1 1 1v11.5A1.5 1.5 0 0 1 17.5 19H6.5A1.5 1.5 0 0 1 5 17.5V5zM8 8h6M8 11h6M8 14h4M18 7.5V17"/>',
  ai: '<rect x="6" y="6" width="12" height="12" rx="2.5"/><path d="M9 3v3M15 3v3M9 18v3M15 18v3M3 9h3M3 15h3M18 9h3M18 15h3M10.5 14 12 8l1.5 6M10.9 11.8h2.2"/>',
  settings: '<circle cx="12" cy="12" r="3.5"/><path d="M10 2h4l.7 2.2 1.7.7 2-.9 2.8 2.8-.9 2  .7 1.7L23 11v2l-2.2.7-.7 1.7.9 2-2.8 2.8-2-.9-1.7.7L14 22h-4l-.7-2.2-1.7-.7-2 .9-2.8-2.8.9-2-.7-1.7L1 13v-2l2.2-.7.7-1.7-.9-2L5.8 3.8l2 .9 1.7-.7L10 2z"/>',
  play: '<path d="M8 5.2v13.6L18.8 12 8 5.2z" fill="currentColor" stroke="none"/>',
  pause: '<path d="M7 5h4v14H7V5zm6 0h4v14h-4V5z" fill="currentColor" stroke="none"/>',
  previous: '<path d="M6 5h2v14H6V5zm3.5 7L19 5v14l-9.5-7z" fill="currentColor" stroke="none"/>',
  next: '<path d="M16 5h2v14h-2V5zM5 19V5l9.5 7L5 19z" fill="currentColor" stroke="none"/>',
  volumeMute: '<path d="M4 9v6h4l5 4V5L8 9H4zm13 0 4 4m0-4-4 4"/>',
  volumeLow: '<path d="M4 9v6h4l5 4V5L8 9H4z"/>',
  volumeMedium: '<path d="M4 9v6h4l5 4V5L8 9H4zM16 9.5a4 4 0 0 1 0 5"/>',
  volumeHigh: '<path d="M4 9v6h4l5 4V5L8 9H4zM16 9.5a4 4 0 0 1 0 5M18.5 7a7 7 0 0 1 0 10"/>',
  layers: '<path d="m12 3 8 4.5-8 4.5-8-4.5L12 3zM4 12l8 4.5 8-4.5M4 16.5l8 4.5 8-4.5"/>',
  piano: '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="M6 4v8M10 4v8M14 4v8M18 4v8M8 12v8M12 12v8M16 12v8"/>',
};

export default function Icon({ name, color = '#a8a8a0', size = 22, style }: IconProps) {
  const source = useMemo(() => {
    const safeColor = /^#[0-9a-fA-F]{3,8}$/.test(color) ? color : '#a8a8a0';
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="${safeColor}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${shapes[name].replaceAll('currentColor', safeColor)}</svg>`;
    return { uri: `data:image/svg+xml,${encodeURIComponent(svg)}` };
  }, [name, color]);

  return <Image source={source} contentFit="contain" style={[{ width: size, height: size }, style]} accessibilityLabel={name} accessible={false} />;
}
