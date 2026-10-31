import { useEffect, type RefObject } from 'react';
import { animate } from 'animejs/animation';

export function useHomeNoteAnimation(root: RefObject<HTMLDivElement | null>, active: boolean) {
  useEffect(() => {
    const stage = root.current;
    if (!active || !stage) return;
    const notes = [...stage.querySelectorAll<HTMLElement>('.studio-drifting-note')];
    const waves = [...stage.querySelectorAll<SVGRectElement>('.studio-wave rect')];
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    let animations: ReturnType<typeof animate>[] = [];
    let stageWidth = stage.clientWidth;
    const visibility = () => animations.forEach(animation => document.hidden ? animation.pause() : animation.resume());
    const reset = () => {
      animations.forEach(animation => animation.revert());
      animations = [];
      if (reducedMotion.matches) return;
      const width = stage.clientWidth;
      notes.filter(note => getComputedStyle(note).display !== 'none').forEach((note, index, visibleNotes) => {
        const duration = 16500 + index % 5 * 1700;
        const drift = animate(note, { x: [-90, width + 90], duration, loop: true, ease: 'linear' });
        drift.seek(duration * index / visibleNotes.length);
        animations.push(drift);
      });
      const glyphs = notes.filter(note => getComputedStyle(note).display !== 'none')
        .map(note => note.querySelector<HTMLElement>('i')).filter((glyph): glyph is HTMLElement => !!glyph);
      if (glyphs.length) animations.push(animate(glyphs, {
        y: [-8, 8], rotate: [-8, 8], duration: (_, index) => 1600 + (index ?? 0) % 6 * 240,
        delay: (_, index) => (index ?? 0) * 35, alternate: true, loop: true, ease: 'inOutSine',
      }));
      if (waves.length) animations.push(animate(waves, {
        scaleY: [0.55, 1.16], duration: (_, index) => 1100 + (index ?? 0) % 7 * 110,
        delay: (_, index) => (index ?? 0) * 35, alternate: true, loop: true, ease: 'inOutSine',
      }));
      visibility();
    };
    reset();
    const resize = new ResizeObserver(() => {
      if (stage.clientWidth !== stageWidth) { stageWidth = stage.clientWidth; reset(); }
    });
    resize.observe(stage);
    reducedMotion.addEventListener('change', reset);
    document.addEventListener('visibilitychange', visibility);
    return () => {
      resize.disconnect();
      animations.forEach(animation => animation.revert());
      reducedMotion.removeEventListener('change', reset);
      document.removeEventListener('visibilitychange', visibility);
    };
  }, [root, active]);
}
