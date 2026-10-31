import type { FormEvent, Ref } from 'react';
import { FloatingField } from '../components/fields';

export function LoginScreen({ identity, password, setIdentity, setPassword, onSubmit, onForgot, firstField }: {
  identity: string; password: string;
  setIdentity: (value: string) => void; setPassword: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void; onForgot: () => void;
  firstField: Ref<HTMLInputElement>;
}) {
  return <form className="auth-form" onSubmit={onSubmit} noValidate>
    <FloatingField label="Tên đăng nhập hoặc Email" value={identity} onChange={setIdentity} inputRef={firstField} autoComplete="username" required />
    <FloatingField label="Mật khẩu" type="password" value={password} onChange={setPassword} autoComplete="current-password" required />
    <button className="auth-text-link auth-forgot" type="button" onClick={onForgot}>Quên mật khẩu?</button>
    <button className="auth-submit" type="submit">Đăng nhập</button>
  </form>;
}
