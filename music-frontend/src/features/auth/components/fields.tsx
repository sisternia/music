import { useId, useState, type ChangeEvent, type InputHTMLAttributes, type Ref } from 'react';

type FieldProps = Omit<InputHTMLAttributes<HTMLInputElement>, 'onChange' | 'value' | 'placeholder'> & {
  label: string;
  value: string;
  onChange: (value: string) => void;
  inputRef?: Ref<HTMLInputElement>;
};

export function FloatingField({ label, value, onChange, inputRef, type = 'text', ...props }: FieldProps) {
  const id = useId();
  const [visible, setVisible] = useState(false);
  const isPassword = type === 'password';
  const change = (event: ChangeEvent<HTMLInputElement>) => onChange(event.target.value);

  return <div className="auth-field">
    <input
      {...props}
      ref={inputRef}
      id={id}
      type={isPassword && visible ? 'text' : type}
      placeholder=" "
      value={value}
      onChange={change}
    />
    <label htmlFor={id}>{label}</label>
    {isPassword && <button
      type="button"
      className="auth-eye"
      onClick={() => setVisible(current => !current)}
      aria-label={visible ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
      aria-pressed={visible}
      title={visible ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M2.5 12s3.3-5.5 9.5-5.5 9.5 5.5 9.5 5.5-3.3 5.5-9.5 5.5S2.5 12 2.5 12Z" />
        <circle cx="12" cy="12" r="2.5" />
        {!visible && <path d="M3 21 21 3" />}
      </svg>
    </button>}
  </div>;
}

export type ContactKind = 'email' | 'phone';

export function ContactSelector({ value, onChange }: { value: ContactKind; onChange: (kind: ContactKind) => void }) {
  return <div className="auth-contact-selector" role="group" aria-label="Phương thức liên hệ">
    <button type="button" aria-pressed={value === 'email'} className={value === 'email' ? 'active' : ''} onClick={() => onChange('email')}>Email</button>
    <button type="button" aria-pressed={value === 'phone'} className={value === 'phone' ? 'active' : ''} onClick={() => onChange('phone')}>Số điện thoại</button>
  </div>;
}
