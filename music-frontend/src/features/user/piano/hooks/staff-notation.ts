export function getStaffPosition(note: string, showBass: boolean) {
  const match = /^([A-G])(#?)(\d)$/.exec(note);
  if (!match) throw new Error(`Invalid piano note: ${note}`);

  const step = Number(match[3]) * 7 + 'CDEFGAB'.indexOf(match[1]);
  const semitone = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 }[match[1] as 'C' | 'D' | 'E' | 'F' | 'G' | 'A' | 'B'];
  const midi = (Number(match[3]) + 1) * 12 + semitone + (match[2] ? 1 : 0);
  // Keep each of the 88 keys at a fixed horizontal position, from A0 to C8.
  const x = 70 + ((midi - 21) / 87) * 188;
  const bass = showBass && step < 28;
  const bottomStep = bass ? 18 : 30;
  const bottomY = bass ? 168 : 88;
  const y = bottomY - (step - bottomStep) * 6;
  const ledgerLines: number[] = [];

  for (let line = bottomStep - 2; line >= step; line -= 2) {
    ledgerLines.push(bottomY - (line - bottomStep) * 6);
  }
  for (let line = bottomStep + 10; line <= step; line += 2) {
    ledgerLines.push(bottomY - (line - bottomStep) * 6);
  }

  return { x, y, bass, sharp: match[2] === '#', ledgerLines };
}
