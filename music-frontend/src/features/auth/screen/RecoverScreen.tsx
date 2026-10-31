import type { FormEvent, Ref } from 'react';
import { ContactSelector, FloatingField, type ContactKind } from '../components/fields';

export function RecoverScreen({ contact, contactKind, setContact, setContactKind, onSubmit, firstField }: {
  contact: string; contactKind: ContactKind; setContact: (value: string) => void; setContactKind: (kind: ContactKind) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void; firstField: Ref<HTMLInputElement>;
}) {
  return <form className="auth-form" onSubmit={onSubmit} noValidate>
    <ContactSelector value={contactKind} onChange={setContactKind} />
    <FloatingField label={contactKind === 'email' ? 'Email' : 'Số điện thoại'} type={contactKind === 'email' ? 'email' : 'tel'} inputMode={contactKind === 'email' ? 'email' : 'tel'} autoComplete={contactKind === 'email' ? 'email' : 'tel'} value={contact} onChange={setContact} inputRef={firstField} required />
    <button className="auth-submit" type="submit">Tiếp tục</button>
  </form>;
}
