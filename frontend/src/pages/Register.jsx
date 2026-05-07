import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Key, Copy, Check, Sparkles, AlertTriangle } from 'lucide-react';
import { api } from '../services/api';

export default function Register() {
  const [generatedPassword, setGeneratedPassword] = useState('');
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  // Gera um identificador único a partir da password
  const deriveIdentifier = async (pwd) => {
    const encoder = new TextEncoder();
    const data = encoder.encode(pwd);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$';
    let pwd = '';
    for (let i = 0; i < 16; i++) pwd += chars[Math.floor(Math.random() * chars.length)];
    
    try {
      const identifier = await deriveIdentifier(pwd);
      await api.auth.register(identifier, pwd);
      setGeneratedPassword(pwd);
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
    <div className="card">
      <div className="card-header">
        <span className="badge">
          <Shield size={10} />
          Novo Acesso
        </span>
        <h1 className="title">Gerar Password</h1>
        <p className="subtitle">Cria o teu acesso seguro ao sistema.</p>
      </div>

      <div className="divider" />

      {!generatedPassword ? (
        <form onSubmit={handleRegister}>
          <div className="warning-box" style={{marginBottom: "1.5rem"}}>
            <Sparkles size={14} style={{color: "var(--primary)"}} />
            <p className="warning-box-text">
              Não precisas de nome de utilizador. O sistema irá gerar uma password única que servirá como a tua única credencial.
            </p>
          </div>

          {error && (
            <div className="error-banner" style={{marginBottom: "1rem"}}>
              <AlertTriangle size={14} />
              {error}
            </div>
          )}

          <button className="btn btn-primary btn-block" type="submit" disabled={isLoading} style={{marginBottom: "1rem"}}>
            <Sparkles size={15} />
            <span>{isLoading ? "A gerar..." : "Gerar Password e Chaves"}</span>
          </button>
        </form>
      ) : (
        <div className="animate-in" style={{ marginTop: '0.25rem' }}>
          <div className="warning-box">
            <span className="warning-box-icon"><AlertTriangle size={14} /></span>
            <p className="warning-box-text">
              <strong>Registo efetuado! Guarda esta password.</strong><br/>
              A mesma será o teu <strong>único</strong> acesso ao sistema e não pode ser recuperada.
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
            <button type="button" className="btn btn-secondary" style={{cursor: "default"}}>
              <Shield size={13} />
              Chave Pública
            </button>
            <button type="button" className="btn btn-secondary" style={{cursor: "default"}}>
              <Key size={13} />
              Chave Privada (Protegida)
            </button>
          </div>
          
          <button type="button" className="btn btn-primary btn-block" style={{marginTop: "1.5rem"}} onClick={() => navigate('/login')}>
            Ir para Login
          </button>
        </div>
      )}

      <div className="card-footer">
        <button type="button" className="link-btn" onClick={() => navigate('/login')}>
          Já tens password? <span>Entrar</span>
        </button>
      </div>
    </div>
  );
}
