/** Inline controls also work when a phone cannot reach an external icon CDN. */
export default function PianoControlIcon({ icon }: { icon: string }) {
  let content;
  switch (icon) {
    case 'mdi-piano':
    case 'mdi-keyboard-outline':
      content = <><rect x="3" y="3" width="18" height="18" rx="1" /><path d="M8 3v18M13 3v18M18 3v18" /><path d="M7 3v10M12 3v10M17 3v10" strokeWidth="3" /></>;
      break;
    case 'mdi-music-clef-treble':
      content = <>
        <path d="M8.5 6.5 19 4v12.2" strokeWidth="2.2" />
        <path d="M8.5 6.5v11.2" strokeWidth="2.2" />
        <ellipse cx="5.8" cy="18.2" rx="3.2" ry="2.2" transform="rotate(-18 5.8 18.2)" fill="currentColor" stroke="none" />
        <ellipse cx="16.3" cy="16.7" rx="3.2" ry="2.2" transform="rotate(-18 16.3 16.7)" fill="currentColor" stroke="none" />
      </>;
      break;
    case 'mdi-label-outline':
      content = <path d="M4 5h11l6 7-6 7H4z" />;
      break;
    case 'mdi-glass-stange':
      content = <><path d="M8 3h8v18H8z" /><path d="M10 11h4v8h-4z" fill="currentColor" stroke="none" /></>;
      break;
    case 'mdi-television-clean':
      content = <>
        <rect x="2.5" y="3.5" width="19" height="15" rx="2" />
        <path d="M8 21h8M12 18.5V21" />
        <path d="M8.2 7.2v5.6M5.4 10h5.6M16.2 9.8v4.8M13.8 12.2h4.8" strokeWidth="1.65" />
      </>;
      break;
    case 'mdi-record':
      content = <circle cx="12" cy="12" r="7" fill="currentColor" stroke="none" />;
      break;
    case 'mdi-play':
      content = <path d="m8 4 12 8-12 8z" fill="currentColor" stroke="none" />;
      break;
    default:
      content = <><path d="M3 9h4l5-5v16l-5-5H3z" fill="currentColor" stroke="none" />
        {icon === 'mdi-volume-mute' ? <path d="m16 9 6 6m0-6-6 6" /> : <>
          <path d="M15 8q5 4 0 8" />
          {icon === 'mdi-volume-high' && <path d="M18 5q8 7 0 14" />}
        </>}
      </>;
  }
  return <svg className="iconify" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{content}</svg>;
}
