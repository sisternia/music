import { getStaffPosition } from '../hooks/staff-notation';

type Props = { pressedKeys: Set<string>; showBass: boolean };

export default function PianoStaff({ pressedKeys, showBass }: Props) {
  const notes = [...pressedKeys].map(note => ({
    note,
    ...getStaffPosition(note, showBass),
  })).sort((a, b) => a.x - b.x);
  const top = Math.min(16, ...notes.map(note => note.y - 18));
  const bottom = Math.max(showBass ? 190 : 110, ...notes.map(note => note.y + 18));

  return (
    <svg
      className="piano-staff"
      viewBox={`0 ${top} 280 ${bottom - top}`}
      role="img"
      aria-label={`Piano staff: ${notes.map(note => note.note).join(', ') || 'no notes'}`}
    >
      {[40, ...(showBass ? [120] : [])].map(staffTop => (
        <g key={staffTop}>
          {Array.from({ length: 5 }, (_, index) => (
            <line key={index} x1="40" x2="270" y1={staffTop + index * 12} y2={staffTop + index * 12} stroke="#666" />
          ))}
          <text x="4" y={staffTop + (staffTop === 40 ? 38 : 15)} fontFamily="Bravura" fontSize="48" fill="#333">
            {staffTop === 40 ? '\uE050' : '\uE062'}
          </text>
        </g>
      ))}
      {notes.map(({ note, x, y, sharp, ledgerLines }) => {
        return (
          <g key={note} data-note={note}>
            <title>{note}</title>
            {ledgerLines.map(lineY => (
              <line key={lineY} x1={x - 12} x2={x + 12} y1={lineY} y2={lineY} stroke="#666" />
            ))}
            {sharp && <text x={x - 20} y={y + 5} fontSize="18" fill="#222">♯</text>}
            <ellipse cx={x} cy={y} rx="7" ry="4" transform={`rotate(-20 ${x} ${y})`} fill="var(--staff-paper-background, #f0f0f0)" stroke="#111" strokeWidth="2" />
          </g>
        );
      })}
    </svg>
  );
}
