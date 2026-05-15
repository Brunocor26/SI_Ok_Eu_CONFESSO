import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldCheck, Send, Mail, Lock, Check, Copy, ArrowRight, Plus, AlertCircle } from 'lucide-react';
import Layout from '../components/Layout';
import { api } from '../services/api';

export default function SendMessage() {
  const [recipientEmail, setRecipientEmail] = useState('');
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [sentCode, setSentCode] = useState(null);
  const [copied, setCopied] = useState(false);
  const navigate = useNavigate();

  const handleSend = async (e) => {
    e.preventDefault();
    if (!recipientEmail || !subject || !body.trim()) {
      setError('Preenche todos os campos.');
      return;
    }
    setIsLoading(true);
    setError('');
    try {
      const data = await api.messages.send(recipientEmail, subject, body);
      setSentCode(data.code);
    } catch (err) {
      setError(err.message || 'Erro ao enviar a mensagem.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(sentCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleLogout = async () => {
    await api.auth.logout().catch(() => {});
    navigate('/login');
  };

  const handleReset = () => {
    setSentCode(null);
    setRecipientEmail('');
    setSubject('');
    setBody('');
    setCopied(false);
  };

  return (
    <Layout activeTab="send">
      {/* Screen header */}
      <div className="flex flex-col w-full mb-6">
        <div className="flex items-center justify-between w-full mb-6">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-surface-container-high border border-outline-variant rounded-full">
            <ShieldCheck size={12} className="text-primary" fill="currentColor" />
            <span className="text-[10px] font-semibold text-on-surface uppercase tracking-widest">Envio Seguro</span>
          </div>
          <button
            className="text-[13px] text-on-surface-variant hover:text-on-surface transition-colors flex items-center gap-1 group"
            onClick={handleLogout}
          >
            Sair
            <ArrowRight size={14} className="group-hover:translate-x-0.5 transition-transform" />
          </button>
        </div>
        <h1 className="text-[24px] font-semibold text-on-surface tracking-tight">Enviar Mensagem</h1>
        <p className="text-[14px] text-on-surface-variant mt-2">A mensagem é cifrada com AES-256 antes do envio.</p>
      </div>

      <hr className="border-outline-variant w-full mb-6" />

      {/* Success state */}
      {sentCode && (
        <div className="bg-surface-container-high border border-outline-variant border-l-4 border-l-primary text-on-surface p-[28px] rounded flex flex-col gap-4 mb-6">
          <div className="flex items-center gap-3">
            <Check size={24} className="text-primary" fill="currentColor" />
            <h2 className="text-[18px] font-semibold text-on-surface">Mensagem Enviada</h2>
          </div>
          <div className="flex flex-col gap-2 mt-2">
            <label className="text-[12px] font-medium text-on-surface-variant uppercase tracking-wider">Código para o destinatário</label>
            <div className="bg-background border border-outline-variant rounded p-3 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <code className="font-[JetBrains_Mono,monospace] text-[13px] text-primary tracking-wider break-all bg-surface-container px-2 py-1 rounded">
                {sentCode}
              </code>
              <button
                className="text-on-surface-variant hover:text-on-surface transition-colors flex items-center gap-2 px-3 py-1.5 border border-outline-variant rounded hover:bg-surface-container self-end sm:self-auto shrink-0"
                onClick={handleCopy}
                title="Copiar"
              >
                {copied ? <Check size={14} className="text-[#4ade80]" /> : <Copy size={14} />}
                <span className="text-[12px] font-medium sm:hidden">Copiar</span>
              </button>
            </div>
            <p className="text-[13px] text-outline mt-1">Partilhe este código apenas através de um canal seguro (ex: Signal).</p>
          </div>
          <button
            className="mt-2 text-[12px] font-medium text-on-surface-variant hover:text-on-surface border border-dashed border-outline-variant hover:border-outline rounded py-3 px-6 w-full transition-all flex items-center justify-center gap-2 hover:bg-surface-container-low"
            onClick={handleReset}
          >
            <Plus size={16} />
            Enviar outra mensagem
          </button>
        </div>
      )}

      {/* Form */}
      <div className={`bg-surface-container-low border border-outline-variant p-[28px] rounded flex flex-col gap-[18px] ${sentCode ? 'opacity-50 grayscale-[50%] pointer-events-none' : ''}`}>
        {error && (
          <div className="flex items-center gap-2 text-error text-[13px] bg-error-container/20 border border-error/30 rounded px-3 py-2">
            <AlertCircle size={14} />
            {error}
          </div>
        )}

        <div className="flex flex-col gap-2">
          <label className="text-[12px] font-medium text-on-surface-variant">Para</label>
          <div className="relative flex items-center">
            <Mail size={14} className="absolute left-3 text-outline-variant" />
            <input
              type="email"
              className="w-full bg-surface border border-outline-variant rounded py-2.5 pl-10 pr-3 text-[14px] text-on-surface focus:border-on-surface focus:outline-none transition-colors"
              value={recipientEmail}
              onChange={(e) => setRecipientEmail(e.target.value)}
              placeholder="destinatario@email.com"
              autoComplete="off"
            />
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <label className="text-[12px] font-medium text-on-surface-variant">Assunto</label>
          <input
            type="text"
            className="w-full bg-surface border border-outline-variant rounded py-2.5 px-3 text-[14px] text-on-surface focus:border-on-surface focus:outline-none transition-colors"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            placeholder="Assunto da mensagem"
          />
        </div>

        <div className="flex flex-col gap-2">
          <label className="text-[12px] font-medium text-on-surface-variant">Mensagem</label>
          <textarea
            className="w-full bg-surface border border-outline-variant rounded py-2.5 px-3 text-[14px] text-on-surface focus:border-on-surface focus:outline-none transition-colors resize-none"
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="Escreve a tua mensagem..."
            rows={5}
          />
        </div>

        <button
          type="button"
          className="w-full bg-on-surface text-surface text-[12px] font-semibold uppercase tracking-wider rounded py-3.5 mt-2 flex items-center justify-center gap-2 hover:bg-surface-bright hover:text-on-surface transition-colors active:scale-[0.99] disabled:opacity-60"
          onClick={handleSend}
          disabled={isLoading}
        >
          <Lock size={14} fill="currentColor" />
          {isLoading ? 'A cifrar e enviar...' : 'Cifrar e Enviar'}
        </button>
      </div>
    </Layout>
  );
}
