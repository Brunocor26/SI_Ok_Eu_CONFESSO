import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Key, Copy, Check, Sparkles, AlertTriangle } from 'lucide-react';

export default function Register() {
  const [generatedPassword, setGeneratedPassword] = useState('');
  const [copied, setCopied] = useState(false);
  const navigate = useNavigate();

  const handleGenerate = () => {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$';
    let pwd = '';
    for (let i = 0; i < 16; i++) pwd += chars[Math.floor(Math.random() * chars.length)];
    setGeneratedPassword(pwd);
    setCopied(false);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(generatedPassword);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="card">
      <div className="card-header">
        <span className="badge">
          <Shield size={10} />
          Novo Utilizador
        </span>
        <h1 className="title">Criar Acesso</h1>
        <p className="subtitle">Gera as tuas credenciais e par de chaves criptográficas.</p>
      </div>

      <div className="divider" />

      <button className="btn-ghost" onClick={handleGenerate} type="button">
        <div className="btn-ghost-inner">
          <Sparkles size={17} />
          <span>Gerar Acesso e Chaves</span>
        </div>
      </button>

      {generatedPassword && (
        <div className="animate-in" style={{ marginTop: '1.25rem' }}>
          <div className="warning-box">
            <span className="warning-box-icon"><AlertTriangle size={14} /></span>
            <p className="warning-box-text">
              <strong>Guarda esta password.</strong> Não pode ser recuperada e é necessária para decifrar as tuas mensagens.
            </p>
          </div>

          <div className="form-group">
            <label className="label">A tua Password</label>
            <div className="password-display">
              <span>{generatedPassword}</span>
              <button type="button" className="copy-btn" onClick={handleCopy} title="Copiar password">
                {copied ? <Check size={15} /> : <Copy size={15} />}
              </button>
            </div>
          </div>

          <label className="label" style={{ marginBottom: '0.6rem', display: 'block' }}>
            Chaves Criptográficas
          </label>
          <div className="keys-container">
            <button type="button" className="btn btn-secondary">
              <Shield size={13} />
              Chave Pública
            </button>
            <button type="button" className="btn btn-secondary">
              <Key size={13} />
              Chave Privada
            </button>
          </div>
        </div>
      )}

      <div className="card-footer">
        <button type="button" className="link-btn" onClick={() => navigate('/login')}>
          Já tem conta?{' '}<span>Fazer login</span>
        </button>
      </div>
    </div>
  );
}
