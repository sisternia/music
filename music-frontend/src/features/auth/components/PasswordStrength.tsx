export const passwordRules = [
  { label: 'Có ký tự đặc biệt', test: (value: string) => /[^\p{L}\p{N}\s]/u.test(value) },
  { label: 'Trên 8 ký tự', test: (value: string) => value.length > 8 },
  { label: 'Có số', test: (value: string) => /\d/.test(value) },
  { label: 'Có chữ', test: (value: string) => /\p{L}/u.test(value) },
  { label: 'Có chữ in hoa', test: (value: string) => /\p{Lu}/u.test(value) },
] as const;

export function PasswordStrength({ password }: { password: string }) {
  const passed = passwordRules.filter(rule => rule.test(password)).length;
  const level = password ? Math.max(1, passed) : 0;
  return <div className="auth-strength" role="meter" aria-valuemin={0} aria-valuemax={5} aria-valuenow={level} aria-label="Độ mạnh mật khẩu">
    <div className="auth-strength-track" aria-hidden="true">
      {passwordRules.map((rule, index) => <span key={rule.label} className={index < level ? `filled strength-${level}` : ''} />)}
    </div>
  </div>;
}
