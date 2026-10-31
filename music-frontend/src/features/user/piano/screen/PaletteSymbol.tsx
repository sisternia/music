type Props = {
  kind?: 'note' | 'rest' | 'slur' | 'tie' | 'up' | 'down';
  denominator?: number;
  dotted?: boolean;
  grace?: boolean;
  slash?: boolean;
};

// Fixed SVG bounds keep the symbols independent of the platform's music fonts.
export default function PaletteSymbol({ kind = 'note', denominator = 4, dotted, grace, slash }: Props) {
  const flags = Math.max(0, Math.log2(denominator) - 2);
  const restFlags = Math.max(1, Math.log2(denominator) - 2);
  const note = (x = 0) => (
    <g transform={`translate(${x} 0)`}>
      {denominator < 1 ? <g fill="none" stroke="currentColor" strokeWidth="2">{denominator === 0.25 ? <path d="M10 17h18v10H10zM7 14v16M31 14v23" /> : <><ellipse cx="20" cy="22" rx="9" ry="5" /><path d="M7 14v16M33 14v16" /></>}</g> : <>
        <ellipse cx="17" cy={denominator === 1 ? 22 : 35} rx={denominator === 1 ? 8 : 6} ry="4" transform={denominator === 1 ? undefined : 'rotate(-22 17 35)'} fill={denominator <= 2 ? 'none' : 'currentColor'} stroke="currentColor" strokeWidth={denominator <= 2 ? 2 : 1} />
        {denominator !== 1 && <path d="M22.5 33V5" fill="none" stroke="currentColor" strokeWidth="1.8" />}
      </>}
      {Array.from({ length: flags }, (_, index) => <path key={index} d={`M23 ${5 + index * 3.7}c1 6 13 6 8 16 2-8-7-7-8-10z`} fill="currentColor" />)}
      {slash && <path d="m15 22 17-10" stroke="currentColor" strokeWidth="1.8" />}
      {dotted && <circle cx={denominator === 1 ? 29 : 37} cy={denominator <= 1 ? 23 : 34} r="2.2" fill="currentColor" />}
    </g>
  );
  return (
    <svg className={`palette-symbol${grace ? ' palette-symbol-grace' : ''}`} viewBox="0 0 48 44" aria-hidden="true" focusable="false">
      {kind === 'note' && note(denominator === 1 ? 5 : 0)}
      {kind === 'rest' && <g fill="currentColor">
        {denominator <= 2 && <><rect x={denominator < 1 ? 20 : 14} y={denominator === 1 ? 20 : 17} width={denominator < 1 ? 7 : 19} height={denominator < 1 ? 18 : 7} /><path d={denominator === 1 ? 'M12 20h23' : denominator === 2 ? 'M12 24h23' : 'M17 35h13'} fill="none" stroke="currentColor" strokeWidth="1.5" /></>}
        {denominator === 4 && <path d="m22 5 7 8-7 8 7 9c-13-6-15 3-7 9-14-5-14-17-2-16l-6-6 7-8-5-7z" />}
        {denominator >= 8 && <><path d={`M30 6 20 ${Math.min(39, 27 + restFlags * 2)}`} fill="none" stroke="currentColor" strokeWidth="2.5" />{Array.from({ length: restFlags }, (_, index) => <path key={index} d={`M${30 - index * .8} ${7 + index * 4}q-5 7-10 3c-5-6 5-10 6-3 2 0 3-1 4-3z`} />)}</>}
        {dotted && <circle cx="37" cy="23" r="2.2" />}
      </g>}
      {(kind === 'slur' || kind === 'tie') && <>
        {[8, 22, 36].slice(0, kind === 'slur' ? 3 : 2).map((x, index) => <g key={x} transform={`translate(${kind === 'tie' ? index * 19 + 5 : x} 0)`}><ellipse cx="0" cy="27" rx="4" ry="2.8" transform="rotate(-22 0 27)" fill="currentColor" /><path d="M3 26V12" stroke="currentColor" strokeWidth="1.5" /></g>)}
        <path d={kind === 'slur' ? 'M5 11Q22-1 40 11Q22 4 5 11' : 'M7 33Q17 41 28 33Q17 45 7 33'} fill="currentColor" />
      </>}
      {(kind === 'up' || kind === 'down') && <g transform={kind === 'down' ? 'translate(0 44) scale(1 -1)' : undefined} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 9h26M11 35h26M24 29V15m-6 6 6-6 6 6" /></g>}
    </svg>
  );
}
