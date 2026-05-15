import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, Eye, EyeOff, ArrowRight, AlertCircle } from 'lucide-react';
import { api } from '../services/api';

const deriveUsername = async (pwd) => {
  const encoder = new TextEncoder();
  const data = encoder.encode(pwd);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
};

export default function Login() {
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    if (password.length !== 16) {
      setError('A password deve ter exatamente 16 caracteres.');
      return;
    }
    setIsLoading(true);
    setError('');
    try {
      const username = await deriveUsername(password);
      await api.auth.login(username, password);
      navigate('/send');
    } catch (err) {
      setError(err.message || 'Credenciais inválidas ou erro no servidor.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-background min-h-screen flex flex-col font-[Inter,sans-serif] text-on-background selection:bg-primary-container selection:text-on-primary-container">
      <main className="flex-grow flex items-center justify-center p-4">
        <div className="w-full max-w-[640px] mx-auto bg-surface border border-outline-variant p-[28px] rounded flex flex-col gap-6">
          {/* Header */}
          <div className="flex flex-col items-center text-center gap-4">
            <div className="inline-flex items-center gap-2 bg-[#0d1f0d] border border-[#1a3a1a] text-[#4ade80] px-3 py-1.5 rounded-full">
              <Lock size={14} fill="currentColor" />
              <span className="text-[12px] font-medium uppercase tracking-widest">Autenticação</span>
            </div>
            <h1 className="text-[24px] font-semibold text-on-surface tracking-tight">Aceder ao Sistema</h1>
            <p className="text-[14px] text-on-surface-variant">Introduz a tua password de 16 caracteres.</p>
          </div>

          <hr className="border-outline-variant" />

          {/* Form */}
          <form onSubmit={handleLogin} className="flex flex-col gap-[18px]">
            <div className="flex flex-col gap-2">
              <label className="text-[12px] font-medium text-outline uppercase tracking-wider" htmlFor="password">
                Chave de Acesso
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  className="w-full bg-surface-container-highest border border-outline-variant rounded p-4 pr-12 font-[JetBrains_Mono,monospace] text-[14px] tracking-[0.05em] text-on-surface focus:border-on-surface focus:ring-0 outline-none transition-colors"
                  value={password}
                  onChange={(e) => { setPassword(e.target.value); setError(''); }}
                  placeholder="••••••••••••••••"
                  maxLength={16}
                  autoComplete="current-password"
                  spellCheck={false}
                />
                <button
                  type="button"
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-outline hover:text-on-surface transition-colors"
                  onClick={() => setShowPassword(!showPassword)}
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              <div className="flex justify-end">
                <span className={`font-[JetBrains_Mono,monospace] text-[13px] ${password.length === 16 ? 'text-[#4ade80]' : 'text-outline'}`}>
                  {password.length} / 16
                </span>
              </div>
            </div>

            {error && (
              <div className="flex items-center gap-2 text-error text-[13px] bg-error-container/20 border border-error/30 rounded px-3 py-2">
                <AlertCircle size={14} />
                {error}
              </div>
            )}

            <button
              type="submit"
              className="bg-on-surface text-surface w-full py-4 rounded text-[12px] font-medium uppercase tracking-widest flex items-center justify-center gap-2 hover:bg-surface-bright hover:text-on-surface transition-colors active:scale-[0.99] disabled:opacity-60"
              disabled={isLoading}
            >
              {isLoading ? 'A entrar...' : 'Entrar'}
              <ArrowRight size={16} />
            </button>
          </form>
        </div>
      </main>

      {/* Footer */}
      <footer className="py-8 flex flex-col items-center gap-3 w-full max-w-[640px] mx-auto text-center">
        <p className="text-[13px] text-on-surface-variant">
          Não tem conta?{' '}
          <button className="text-on-surface underline hover:text-primary transition-colors ml-1" onClick={() => navigate('/register')}>
            Criar acesso
          </button>
        </p>
        <p className="text-[12px] text-on-surface-variant opacity-60">© 2024 OK, Eu Confesso — Encriptação Ponta-a-Ponta</p>
        <div className="flex gap-4 text-[13px]">
          <span className="text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer">Privacidade</span>
          <span className="text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer">Termos</span>
          <span className="text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer">Segurança</span>
        </div>
      </footer>
    </div>
  );
}
