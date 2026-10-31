import { useEffect, useRef, useState, type FormEvent } from 'react';
import { type ContactKind } from '../components/fields';
import { LoginScreen } from './LoginScreen';
import { RegisterScreen } from './RegisterScreen';
import { RecoverScreen } from './RecoverScreen';
import { VerifyScreen } from './VerifyScreen';
import { ResetScreen } from './ResetScreen';
import '../auth.css';

type AuthStep = 'login' | 'register' | 'recover' | 'verify' | 'reset';
type Props = { open: boolean; onClose: () => void; logo: string };

const headings: Record<AuthStep, { title: string; subtitle: string }> = {
  login: { title: 'Chào mừng trở lại', subtitle: 'Đăng nhập để tiếp tục hành trình âm nhạc của bạn.' },
  register: { title: 'Tạo tài khoản', subtitle: 'Bắt đầu lưu lại những bản nhạc của riêng bạn.' },
  recover: { title: 'Quên mật khẩu?', subtitle: 'Chọn email hoặc số điện thoại để xác thực tài khoản.' },
  verify: { title: 'Xác thực tài khoản', subtitle: 'Nhập mã xác thực gồm 6 chữ số.' },
  reset: { title: 'Đổi mật khẩu', subtitle: 'Chọn mật khẩu mới cho tài khoản của bạn.' },
};

function validContact(value: string, kind: ContactKind) {
  return kind === 'email'
    ? /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim())
    : /^\+?[\d\s().-]{8,}$/.test(value.trim()) && value.replace(/\D/g, '').length >= 8;
}

export default function AuthDialog({ open, onClose, logo }: Props) {
  const [step, setStep] = useState<AuthStep>('login');
  const [source, setSource] = useState<'register' | 'recover'>('register');
  const [username, setUsername] = useState('');
  const [identity, setIdentity] = useState('');
  const [contact, setContact] = useState('');
  const [contactKind, setContactKind] = useState<ContactKind>('email');
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [code, setCode] = useState<string[]>(Array(6).fill(''));
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const firstField = useRef<HTMLInputElement>(null);
  const opener = useRef<HTMLElement | null>(null);
  const closeRef = useRef(onClose);

  useEffect(() => { closeRef.current = onClose; }, [onClose]);

  const changeStep = (next: AuthStep) => {
    setStep(next);
    setError('');
    setNotice('');
    setPassword('');
    setConfirmation('');
    setCode(Array(6).fill(''));
  };
  const changeContactKind = (next: ContactKind) => {
    setContactKind(next);
    setContact('');
    setError('');
  };

  useEffect(() => {
    if (!open) return;
    opener.current = document.activeElement as HTMLElement;
    const escape = (event: globalThis.KeyboardEvent) => { if (event.key === 'Escape') closeRef.current(); };
    document.addEventListener('keydown', escape);
    return () => {
      document.removeEventListener('keydown', escape);
      opener.current?.focus();
    };
  }, [open]);
  useEffect(() => {
    if (!open) return;
    const focus = requestAnimationFrame(() => firstField.current?.focus());
    return () => cancelAnimationFrame(focus);
  }, [open, step]);

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    setNotice('');
    if (step === 'login') {
      if (!identity.trim() || !password) { setError('Vui lòng nhập tài khoản và mật khẩu.'); return; }
      setNotice('Biểu mẫu đã sẵn sàng. Đăng nhập cần kết nối dịch vụ tài khoản.');
    } else if (step === 'register') {
      if (username.trim().length < 3) { setError('Tên đăng nhập cần ít nhất 3 ký tự.'); return; }
      if (!validContact(contact, contactKind)) { setError(`${contactKind === 'email' ? 'Email' : 'Số điện thoại'} chưa hợp lệ.`); return; }
      if (!password) { setError('Vui lòng nhập mật khẩu.'); return; }
      if (password !== confirmation) { setError('Mật khẩu xác nhận không khớp.'); return; }
      setSource('register');
      changeStep('verify');
      setNotice('Giao diện xác thực đã sẵn sàng; mã chưa được gửi đến liên hệ của bạn.');
    } else if (step === 'recover') {
      if (!validContact(contact, contactKind)) { setError(`${contactKind === 'email' ? 'Email' : 'Số điện thoại'} chưa hợp lệ.`); return; }
      setSource('recover');
      changeStep('verify');
      setNotice('Giao diện xác thực đã sẵn sàng; mã chưa được gửi đến liên hệ của bạn.');
    } else if (step === 'verify') {
      if (code.join('').length !== 6) { setError('Vui lòng nhập đủ 6 chữ số.'); return; }
      if (source === 'recover') {
        changeStep('reset');
        setNotice('Mã chưa được kiểm tra trên máy chủ. Đây là bước xem trước giao diện đổi mật khẩu.');
      } else {
        setNotice('Mã gồm đủ 6 số. Xác thực tài khoản cần kết nối dịch vụ tài khoản.');
      }
    } else {
      if (password.length < 8) { setError('Mật khẩu cần ít nhất 8 ký tự.'); return; }
      if (password !== confirmation) { setError('Mật khẩu xác nhận không khớp.'); return; }
      setNotice('Biểu mẫu đã sẵn sàng. Mật khẩu chưa được thay đổi trên máy chủ.');
    }
  };

  if (!open) return null;

  return <div className="auth-backdrop" onMouseDown={event => { if (event.target === event.currentTarget) onClose(); }}>
    <section className="auth-dialog" role="dialog" aria-modal="true" aria-labelledby="auth-title" aria-describedby="auth-subtitle">
      <button className="auth-close" type="button" onClick={onClose} aria-label="Đóng">×</button>
      <div className="auth-brand">
        <div className="auth-brand-inner">
          <img className="auth-logo" src={logo} alt="Harmony Auralis" />
          <span>Không gian âm nhạc của bạn</span>
        </div>
      </div>
      <div className="auth-content">
        <span className="auth-kicker">HARMONY AURALIS</span>
        <h2 id="auth-title">{headings[step].title}</h2>
        <p id="auth-subtitle" className="auth-subtitle">{headings[step].subtitle}</p>
        {step === 'login' && <LoginScreen identity={identity} password={password} setIdentity={setIdentity} setPassword={setPassword} onSubmit={submit} onForgot={() => changeStep('recover')} firstField={firstField} />}
        {step === 'register' && <RegisterScreen username={username} contact={contact} contactKind={contactKind} password={password} confirmation={confirmation} setUsername={setUsername} setContact={setContact} setContactKind={changeContactKind} setPassword={setPassword} setConfirmation={setConfirmation} onSubmit={submit} firstField={firstField} />}
        {step === 'recover' && <RecoverScreen contact={contact} contactKind={contactKind} setContact={setContact} setContactKind={changeContactKind} onSubmit={submit} firstField={firstField} />}
        {step === 'verify' && <VerifyScreen contact={contact} code={code} setCode={setCode} onSubmit={submit} firstField={element => { firstField.current = element; }} />}
        {step === 'reset' && <ResetScreen password={password} confirmation={confirmation} setPassword={setPassword} setConfirmation={setConfirmation} onSubmit={submit} firstField={firstField} />}
        {error && <p className="auth-message auth-error" role="alert">{error}</p>}
        {notice && <p className="auth-message auth-notice" role="status">{notice}</p>}
        <div className="auth-footer">
          {step === 'login' ? <>Chưa có tài khoản? <button type="button" onClick={() => changeStep('register')}>Đăng ký</button></> :
            step === 'register' ? <>Đã có tài khoản? <button type="button" onClick={() => changeStep('login')}>Đăng nhập</button></> :
            <button type="button" onClick={() => changeStep(step === 'reset' ? 'verify' : 'login')}>← Quay lại {step === 'reset' ? 'xác thực' : 'đăng nhập'}</button>}
        </div>
      </div>
    </section>
  </div>;
}
