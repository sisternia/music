import type { FormEvent } from 'react';
import { CodeInput } from '../components/CodeInput';

export function VerifyScreen({ contact, code, setCode, onSubmit, firstField }: {
  contact: string; code: string[]; setCode: (code: string[]) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  firstField: (element: HTMLInputElement | null) => void;
}) {
  return <form className="auth-form" onSubmit={onSubmit} noValidate>
    <p className="auth-code-caption">{contact ? `Mã xác thực cho ${contact}` : 'Nhập mã xác thực của bạn'}</p>
    <CodeInput value={code} onChange={setCode} firstField={firstField} />
    <button className="auth-submit" type="submit">Xác thực</button>
  </form>;
}
