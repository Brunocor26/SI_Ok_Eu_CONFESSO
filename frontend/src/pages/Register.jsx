import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, TriangleAlert, CheckCircle, Copy, Check, ArrowRight, Download } from 'lucide-react';
import { api } from '../services/api';

const downloadFile = (content, filename) => {
  const blob = new Blob([content], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};

export default function Register() {
  const [generatedPassword, setGeneratedPassword] = useState('');
  const [keys, setKeys] = useState(null); // { publicKey, privateKey }
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    try {
      const data = await api.auth.register();
      setGeneratedPassword(data.password);
      setKeys({ publicKey: data.public_key, privateKey: data.private_key });
      setCopied(false);
    } catch (err) {
      setError(err.message || 'Erro ao criar registo.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(generatedPassword);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-background text-on-background min-h-screen flex flex-col items-center justify-center p-6 font-[Inter,sans-serif] selection:bg-primary-container selection:text-on-primary-container">
      <main className="w-full max-w-[640px] flex flex-col gap-[18px]">
        <article className="bg-surface border border-outline-variant p-[28px] rounded flex flex-col gap-6">
          {/* Header */}
          <header className="flex flex-col items-start gap-4">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded bg-surface-container border border-outline-variant text-on-surface-variant text-[12px] font-medium uppercase tracking-widest">
              <Lock size={14} />
              Novo Acesso
            </div>
            <div>
              <h1 className="text-[24px] font-semibold text-on-background tracking-tight">Criar Acesso</h1>
              <p className="text-[14px] text-outline mt-1">O sistema gera a tua password. Não usamos nome de utilizador.</p>
            </div>
          </header>

          <hr className="border-outline-variant" />

          {!generatedPassword ? (
            <form onSubmit={handleRegister} className="flex flex-col gap-4">
              <div className="flex items-start gap-3 p-4 rounded bg-surface-container-high border border-outline-variant">
                <CheckCircle size={18} className="text-primary shrink-0 mt-0.5" />
                <p className="text-[14px] text-on-surface">
                  Não precisas de nome de utilizador. Será gerada uma password única que serve como única credencial.
                </p>
              </div>

              {error && (
                <div className="flex items-center gap-2 text-error text-[13px] bg-error-container/20 border border-error/30 rounded px-3 py-2">
                  <TriangleAlert size={14} />
                  {error}
                </div>
              )}

              <button
                type="submit"
                className="bg-on-surface text-surface w-full py-4 rounded text-[12px] font-medium uppercase tracking-widest flex items-center justify-center gap-2 hover:bg-surface-bright hover:text-on-surface transition-colors active:scale-[0.99] disabled:opacity-60"
                disabled={isLoading}
              >
                {isLoading ? 'A gerar...' : 'Gerar Password e Chaves'}
                <ArrowRight size={16} />
              </button>
            </form>
          ) : (
            <div className="flex flex-col gap-5">
              {/* Success notice */}
              <div className="flex items-start gap-3 p-4 rounded bg-surface-container-high border border-outline-variant">
                <CheckCircle size={18} className="text-primary shrink-0 mt-0.5" />
                <p className="text-[14px] text-on-surface pt-0.5">Registo efetuado. Guarda esta password.</p>
              </div>

              {/* Warning notice */}
              <div className="flex items-start gap-3 p-4 rounded bg-surface-container-lowest border border-outline">
                <TriangleAlert size={18} className="text-tertiary shrink-0 mt-0.5" />
                <p className="text-[13px] text-on-surface-variant pt-0.5">
                  Esta password é a tua única credencial. Guarda-a num local seguro — não é recuperável.
                </p>
              </div>

              {/* Password display */}
              <div className="flex items-center justify-between p-4 rounded bg-background border border-outline-variant group hover:border-outline transition-colors">
                <code className="font-[JetBrains_Mono,monospace] text-[14px] tracking-[0.05em] text-on-background select-all">
                  {generatedPassword}
                </code>
                <button
                  type="button"
                  onClick={handleCopy}
                  className="text-outline group-hover:text-on-background transition-colors focus:outline-none rounded"
                  aria-label="Copiar password"
                >
                  {copied ? <Check size={16} className="text-[#4ade80]" /> : <Copy size={16} />}
                </button>
              </div>

              {/* Key download buttons */}
              {keys && (
                <div className="flex flex-col gap-2">
                  <p className="text-[11px] text-outline uppercase tracking-wider">Chaves RSA</p>
                  <div className="flex flex-col sm:flex-row gap-3">
                    <button
                      type="button"
                      onClick={() => downloadFile(keys.publicKey, 'chave_publica.pem')}
                      className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded border border-outline-variant bg-transparent text-on-background text-[12px] font-medium hover:bg-surface-container transition-colors"
                    >
                      <Download size={14} />
                      Chave Pública
                    </button>
                    <button
                      type="button"
                      onClick={() => downloadFile(keys.privateKey, 'chave_privada.pem')}
                      className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded border border-outline-variant bg-transparent text-on-background text-[12px] font-medium hover:bg-surface-container transition-colors"
                    >
                      <Download size={14} />
                      Chave Privada
                    </button>
                  </div>
                  <p className="text-[11px] text-outline">
                    A chave privada só pode ser descarregada agora. Guarda-a num local seguro.
                  </p>
                </div>
              )}

              <button
                type="button"
                className="bg-on-surface text-surface w-full py-4 rounded text-[12px] font-medium uppercase tracking-widest flex items-center justify-center gap-2 hover:bg-surface-bright hover:text-on-surface transition-colors active:scale-[0.99]"
                onClick={() => navigate('/login')}
              >
                Ir para Login
                <ArrowRight size={16} />
              </button>
            </div>
          )}
        </article>

        <footer className="text-center">
          <p className="text-[13px] text-outline">
            Já tem acesso?{' '}
            <button className="text-on-background hover:text-primary underline hover:no-underline transition-colors ml-1" onClick={() => navigate('/login')}>
              Entrar
            </button>
          </p>
        </footer>
      </main>
    </div>
  );
}
