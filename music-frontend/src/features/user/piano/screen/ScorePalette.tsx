import { useState, type CSSProperties } from 'react';
import { paletteDurations as durations, usePaletteSelection, voiceColors } from '../hooks/usePaletteSelection';
import type { useScoreEditor } from '../hooks/useScoreEditor';
import PaletteSymbol from './PaletteSymbol';

type Props = { editor: ReturnType<typeof useScoreEditor> };
const accidentals = [
  { value: 'double-flat', glyph: '𝄫', label: 'Giáng kép' },
  { value: 'flat', glyph: '♭', label: 'Giáng' },
  { value: 'natural', glyph: '♮', label: 'Bình' },
  { value: 'sharp', glyph: '♯', label: 'Thăng' },
  { value: 'double-sharp', glyph: '𝄪', label: 'Thăng kép' },
  { value: 'sharp-sharp', glyph: '♯♯', label: 'Hai dấu thăng' },
];
const graceDurations = [8, 16, 32, 64, 128, 256, 512];

export default function ScorePalette({ editor }: Props) {
  const [durationStart, setDurationStart] = useState(2);
  const [accidentalStart, setAccidentalStart] = useState(1);
  const [graceIndex, setGraceIndex] = useState(0);
  const [voicePage, setVoicePage] = useState(0);
  const selection = usePaletteSelection(editor);
  const { active, action } = selection;
  const pressed = (value: boolean) => ({ 'aria-pressed': value, className: value ? 'selected' : '' });
  const graceDuration = graceDurations[graceIndex];

  return (
    <aside className="score-palette" aria-label="Selection palette" style={{ '--palette-accent': selection.color } as CSSProperties}>
      <div className="palette-heading"><span>‹ {active.length ? 'Selection' : 'Nhập nốt'}</span><b aria-hidden="true">⠿</b></div>
      <fieldset disabled={editor.busy}>
        <section className="palette-section" aria-label="Trường độ">
          <button className="palette-step palette-step-vertical" aria-label="Trường độ dài hơn" disabled={durationStart === 0} onClick={() => setDurationStart(start => start - 2)}>⌃</button>
          <div className="palette-grid palette-durations">{durations.slice(durationStart, durationStart + 6).map(({ value, label }) => <button key={value} title={`${label} · 1/${value}`} aria-label={`Trường độ 1/${value}`} {...pressed(selection.duration === value)} onClick={() => action('duration', String(value))}>
            <PaletteSymbol kind={selection.rest ? 'rest' : 'note'} denominator={value} dotted={selection.dotted} />{(value >= 64 || (selection.rest && value <= 2)) && <span className="palette-denominator">{value === 2 ? '1/2' : value}</span>}
          </button>)}</div>
          <button className="palette-step palette-step-vertical" aria-label="Trường độ ngắn hơn" disabled={durationStart >= durations.length - 6} onClick={() => setDurationStart(start => start + 2)}>⌄</button>
        </section>
        <div className="palette-grid"><button title="Bật/tắt dấu lặng" aria-label="Dấu lặng" {...pressed(selection.rest)} onClick={() => action('rest')}><PaletteSymbol kind="rest" denominator={selection.duration ?? 4} /></button><button title="Thêm/bỏ chấm dôi" aria-label="Chấm dôi" {...pressed(selection.dotted)} onClick={() => action('dot')}><PaletteSymbol kind={selection.rest ? 'rest' : 'note'} denominator={selection.duration ?? 4} dotted /></button></div>
        <section className="palette-carousel" aria-label="Dấu hóa">
          <button className="palette-step" aria-label="Dấu hóa trước" disabled={accidentalStart === 0} onClick={() => setAccidentalStart(start => start - 1)}>‹</button>
          <div className="palette-grid palette-three">{accidentals.slice(accidentalStart, accidentalStart + 3).map(({ value, glyph, label }) => <button key={value} title={label} aria-label={label} {...pressed(selection.accidental === value)} onClick={() => action('accidental', value)}><span className="palette-accidental">{glyph}</span></button>)}</div>
          <button className="palette-step" aria-label="Dấu hóa tiếp theo" disabled={accidentalStart === accidentals.length - 3} onClick={() => setAccidentalStart(start => start + 1)}>›</button>
        </section>
        <div className="palette-grid"><button title="Dấu luyến · chọn ít nhất hai nốt" aria-label="Dấu luyến" {...pressed(selection.slur)} onClick={() => action('slur')}><PaletteSymbol kind="slur" /></button><button title="Nối hai nốt cùng cao độ" aria-label="Dấu nối" {...pressed(selection.tie)} onClick={() => action('tie')}><PaletteSymbol kind="tie" /></button></div>
        <div className="palette-grid"><button title="Accent" aria-label="Accent" {...pressed(selection.articulations.includes('accent'))} onClick={() => action('articulation', 'accent')}><span className="palette-articulation">&gt;</span></button><button title="Marcato" aria-label="Marcato" {...pressed(selection.articulations.includes('strong-accent'))} onClick={() => action('articulation', 'strong-accent')}><span className="palette-articulation">∧</span></button><button title="Staccato" aria-label="Staccato" {...pressed(selection.articulations.includes('staccato'))} onClick={() => action('articulation', 'staccato')}><span className="palette-articulation">•</span></button><button title="Tenuto" aria-label="Tenuto" {...pressed(selection.articulations.includes('tenuto'))} onClick={() => action('articulation', 'tenuto')}><span className="palette-articulation">−</span></button></div>
        <section className="palette-carousel" aria-label="Nốt hoa mỹ">
          <button className="palette-step" aria-label="Nốt hoa mỹ trước" disabled={graceIndex === 0} onClick={() => setGraceIndex(index => index - 1)}>‹</button>
          <div className="palette-grid">{[false, true].map(slash => <button key={String(slash)} title={`Thêm nốt hoa mỹ 1/${graceDuration}${slash ? ' có gạch' : ''} trước nốt đã chọn`} aria-label={`Nốt hoa mỹ 1/${graceDuration}${slash ? ' có gạch' : ''}`} {...pressed(selection.grace === `${graceDuration}:${slash ? 'yes' : 'no'}`)} onClick={() => action('grace', `${graceDuration}:${slash ? 'yes' : 'no'}`)}><PaletteSymbol denominator={graceDuration} grace slash={slash} /></button>)}</div>
          <button className="palette-step" aria-label="Nốt hoa mỹ tiếp theo" disabled={graceIndex === graceDurations.length - 1} onClick={() => setGraceIndex(index => index + 1)}>›</button>
        </section>
        <div className="palette-grid"><button title="Tăng một quãng tám" aria-label="Tăng quãng tám" onClick={() => action('transpose', 12)}><PaletteSymbol kind="up" /></button><button title="Giảm một quãng tám" aria-label="Giảm quãng tám" onClick={() => action('transpose', -12)}><PaletteSymbol kind="down" /></button></div>
        <section className="palette-carousel" aria-label="Bè">
          <button className="palette-step" aria-label="Bè 1 đến 4" disabled={voicePage === 0} onClick={() => setVoicePage(0)}>‹</button>
          <div className="palette-grid palette-voices">{[1, 3, 2, 4].map(offset => {
            const voice = offset + voicePage * 4;
            return <button key={voice} style={{ color: voiceColors[voice - 1], '--voice-color': voiceColors[voice - 1] } as CSSProperties} title={`Chuyển sang bè ${voice}`} aria-label={`Bè ${voice}`} {...pressed(selection.voice === voice)} onClick={() => action('voice', voice)}><PaletteSymbol /><span>{voice}</span></button>;
          })}</div>
          <button className="palette-step" aria-label="Bè 5 đến 8" disabled={voicePage === 1} onClick={() => setVoicePage(1)}>›</button>
        </section>
      </fieldset>
      <details className="palette-more"><summary title="Thao tác bổ sung">Thêm</summary><div className="palette-grid"><button title="Tăng nửa cung" aria-label="Tăng nửa cung" onClick={() => action('transpose', 1)}>♯↑</button><button title="Giảm nửa cung" aria-label="Giảm nửa cung" onClick={() => action('transpose', -1)}>♭↓</button><button title="Thêm nốt C4 vào dấu lặng được chọn" aria-label="Thêm nốt" onClick={() => action('insert', 60)}>＋♪</button><button title="Xóa nốt · giữ trường độ bằng dấu lặng" aria-label="Xóa nốt" onClick={() => action('delete')}>⌫</button></div></details>
      <div className="palette-status" role="status">{editor.busy ? 'Đang lưu…' : active.length ? `${active.length} đã chọn` : 'Chọn trên phổ để áp dụng'}</div>
    </aside>
  );
}
