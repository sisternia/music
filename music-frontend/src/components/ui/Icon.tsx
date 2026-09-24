import type { ReactElement, SVGProps } from 'react';

export type IconName =
  | 'home'
  | 'community'
  | 'news'
  | 'ai'
  | 'settings'
  | 'play'
  | 'pause'
  | 'previous'
  | 'next'
  | 'volumeMute'
  | 'volumeLow'
  | 'volumeMedium'
  | 'volumeHigh'
  | 'layers'
  | 'piano';

type IconProps = {
  name: IconName;
  color?: string;
  size?: number;
  style?: SVGProps<SVGSVGElement>['style'];
};

function HomeIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M4 10.5 12 4l8 6.5" />
      <path d="M6.5 9.5V20h11V9.5" />
      <path d="M10 20v-5h4v5" />
    </svg>
  );
}

function CommunityIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <circle cx="9" cy="8" r="2.2" />
      <circle cx="16.2" cy="9.2" r="1.8" />
      <path d="M4.8 18c.7-2.7 2.8-4.5 5.2-4.5s4.5 1.8 5.2 4.5" />
      <path d="M13.4 18c.5-1.8 1.8-3 3.5-3 1.5 0 2.8 1 3.3 3" />
    </svg>
  );
}

function NewsIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M5 5h13a1 1 0 0 1 1 1v11.5A1.5 1.5 0 0 1 17.5 19H6.5A1.5 1.5 0 0 1 5 17.5V5z" />
      <path d="M8 8h6" />
      <path d="M8 11h6" />
      <path d="M8 14h4" />
      <path d="M18 7.5V17" />
    </svg>
  );
}

function AiIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <rect x="6" y="6" width="12" height="12" rx="2.5" />
      <path d="M9 3v3" />
      <path d="M15 3v3" />
      <path d="M9 18v3" />
      <path d="M15 18v3" />
      <path d="M3 9h3" />
      <path d="M3 15h3" />
      <path d="M18 9h3" />
      <path d="M18 15h3" />
      <path d="M10.5 14 12 8l1.5 6" />
      <path d="M10.9 11.8h2.2" />
    </svg>
  );
}

function SettingsIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z" />
      <path d="M19.4 15a1.7 1.7 0 0 0 .34 1.87l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06A1.7 1.7 0 0 0 15 19.36a1.7 1.7 0 0 0-1 .24 1.7 1.7 0 0 0-.82 1.46V21a2 2 0 0 1-4 0v-.09A1.7 1.7 0 0 0 8 19.36a1.7 1.7 0 0 0-1.87.34l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.7 1.7 0 0 0 3.64 15a1.7 1.7 0 0 0-.24-1 1.7 1.7 0 0 0-1.46-.82H2a2 2 0 0 1 0-4h.09A1.7 1.7 0 0 0 3.64 8a1.7 1.7 0 0 0-.34-1.87l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.7 1.7 0 0 0 8 3.64a1.7 1.7 0 0 0 1-.24A1.7 1.7 0 0 0 9.82 2h4a1.7 1.7 0 0 0 .82 1.4 1.7 1.7 0 0 0 1 .24 1.7 1.7 0 0 0 1.27-.34l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.7 1.7 0 0 0 20.36 8a1.7 1.7 0 0 0 .24 1 1.7 1.7 0 0 0 1.4.82V14a1.7 1.7 0 0 0-1.4.82 1.7 1.7 0 0 0-.24 1z" />
    </svg>
  );
}

function PlayIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" {...props}>
      <path d="M8 5.2v13.6L18.8 12 8 5.2z" />
    </svg>
  );
}

function PauseIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" {...props}>
      <path d="M7 5h4v14H7V5zm6 0h4v14h-4V5z" />
    </svg>
  );
}

function PreviousIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" {...props}>
      <path d="M6 5h2v14H6V5zm3.5 7L19 5v14l-9.5-7z" />
    </svg>
  );
}

function NextIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" {...props}>
      <path d="M16 5h2v14h-2V5zM5 19V5l9.5 7L5 19z" />
    </svg>
  );
}

function VolumeLowIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M4 9v6h4l5 4V5L8 9H4z" />
    </svg>
  );
}

function VolumeMediumIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M4 9v6h4l5 4V5L8 9H4z" />
      <path d="M16 9.5a4 4 0 0 1 0 5" />
    </svg>
  );
}

function VolumeHighIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M4 9v6h4l5 4V5L8 9H4z" />
      <path d="M16 9.5a4 4 0 0 1 0 5" />
      <path d="M18.5 7a7 7 0 0 1 0 10" />
    </svg>
  );
}

function VolumeMuteIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M4 9v6h4l5 4V5L8 9H4z" />
      <path d="m17 9 4 4" />
      <path d="m21 9-4 4" />
    </svg>
  );
}

function LayersIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="m12 3 8 4.5-8 4.5-8-4.5L12 3z" />
      <path d="m4 12 8 4.5 8-4.5" />
      <path d="m4 16.5 8 4.5 8-4.5" />
    </svg>
  );
}

function PianoIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <rect width="20" height="16" x="2" y="4" rx="2" />
      <path d="M6 4v8" />
      <path d="M10 4v8" />
      <path d="M14 4v8" />
      <path d="M18 4v8" />
      <path d="M8 12v8" />
      <path d="M12 12v8" />
      <path d="M16 12v8" />
    </svg>
  );
}

const ICONS: Record<IconName, (props: SVGProps<SVGSVGElement>) => ReactElement> = {
  home: HomeIcon,
  community: CommunityIcon,
  news: NewsIcon,
  ai: AiIcon,
  settings: SettingsIcon,
  play: PlayIcon,
  pause: PauseIcon,
  previous: PreviousIcon,
  next: NextIcon,
  volumeMute: VolumeMuteIcon,
  volumeLow: VolumeLowIcon,
  volumeMedium: VolumeMediumIcon,
  volumeHigh: VolumeHighIcon,
  layers: LayersIcon,
  piano: PianoIcon,
};

export default function Icon({ name, color = '#a8a8a0', size = 22, style }: IconProps) {
  const Svg = ICONS[name];

  return (
    <Svg
      aria-hidden="true"
      focusable="false"
      width={size}
      height={size}
      style={{ color, display: 'block', ...style }}
    />
  );
}
