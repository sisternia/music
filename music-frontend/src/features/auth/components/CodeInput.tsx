import { useRef, type ClipboardEvent, type KeyboardEvent } from 'react';

export function CodeInput({ value, onChange, firstField }: {
  value: string[];
  onChange: (value: string[]) => void;
  firstField?: (element: HTMLInputElement | null) => void;
}) {
  const fields = useRef<(HTMLInputElement | null)[]>([]);
  const fill = (index: number, input: string) => {
    const digits = input.replace(/\D/g, '').slice(0, 6 - index);
    const next = [...value];
    if (!digits) next[index] = '';
    else [...digits].forEach((digit, offset) => { next[index + offset] = digit; });
    onChange(next);
    if (digits) fields.current[Math.min(index + digits.length, 5)]?.focus();
  };
  const paste = (event: ClipboardEvent<HTMLInputElement>, index: number) => {
    event.preventDefault();
    fill(index, event.clipboardData.getData('text'));
  };
  const keyDown = (event: KeyboardEvent<HTMLInputElement>, index: number) => {
    if (event.key === 'Backspace' && !value[index] && index > 0) fields.current[index - 1]?.focus();
    if (event.key === 'ArrowLeft' && index > 0) fields.current[index - 1]?.focus();
    if (event.key === 'ArrowRight' && index < 5) fields.current[index + 1]?.focus();
  };
  return <div className="auth-code-row" role="group" aria-label="Mã xác thực gồm 6 số">
    {value.map((digit, index) => <input
      key={index}
      ref={element => { fields.current[index] = element; if (index === 0) firstField?.(element); }}
      aria-label={`Chữ số ${index + 1}`}
      type="text"
      inputMode="numeric"
      pattern="[0-9]*"
      autoComplete={index === 0 ? 'one-time-code' : 'off'}
      maxLength={6}
      value={digit}
      onChange={event => fill(index, event.target.value)}
      onPaste={event => paste(event, index)}
      onKeyDown={event => keyDown(event, index)}
    />)}
  </div>;
}
