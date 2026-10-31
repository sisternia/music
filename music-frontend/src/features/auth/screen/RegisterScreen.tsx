import type { FormEvent, Ref } from 'react';
import { ContactSelector, FloatingField, type ContactKind } from '../components/fields';
import { PasswordStrength } from '../components/PasswordStrength';

export function RegisterScreen({ username, contact, contactKind, password, confirmation, setUsername, setContact, setContactKind, setPassword, setConfirmation, onSubmit, firstField }: {
  username: string; contact: string; contactKind: ContactKind; password: string; confirmation: string;
  setUsername: (value: string) => void; setContact: (value: string) => void; setContactKind: (kind: ContactKind) => void;
  setPassword: (value: string) => void; setConfirmation: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void; firstField: Ref<HTMLInputElement>;
}) {
  return <form className="auth-form" onSubmit={onSubmit} noValidate>
    <FloatingField label="Tên đăng nhập" value={username} onChange={setUsername} inputRef={firstField} autoComplete="username" required />
    <ContactSelector value={contactKind} onChange={setContactKind} />
    <FloatingField label={contactKind === 'email' ? 'Email' : 'Số điện thoại'} type={contactKind === 'email' ? 'email' : 'tel'} inputMode={contactKind === 'email' ? 'email' : 'tel'} autoComplete={contactKind === 'email' ? 'email' : 'tel'} value={contact} onChange={setContact} required />
    <FloatingField label="Mật khẩu" type="password" value={password} onChange={setPassword} autoComplete="new-password" required />
    <PasswordStrength password={password} />
    <FloatingField label="Xác nhận mật khẩu" type="password" value={confirmation} onChange={setConfirmation} autoComplete="new-password" required />
    <button className="auth-submit" type="submit">Đăng ký</button>
  </form>;
}
