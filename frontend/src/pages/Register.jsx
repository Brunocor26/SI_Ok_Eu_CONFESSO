import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Key, Copy, Check, Sparkles, AlertTriangle, User } from 'lucide-react';
import { api } from '../services/api';

export default function Register() {
  const [username, setUsername] = useState('');
  const [generatedPassword, setGeneratedPassword] = useState('');
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    if (!username.trim()) {
      setError('O nome de utilizador é obrigatório.');
      return;
    }

    setIsLoading(true);
    setError('');

    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$';
    let pwd = '';
    for (let i = 0; i < 16; i++) pwd += chars[Math.floor(Math.random() * chars.length)];
    
    try {
      await api.auth.register(username, pwd);
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
          Novo Utilizador
        </span>
        <h1 className="title">Criar Acesso</h1>
        <p className="subtitle">Gera as tuas credenciais e par de chaves criptográficas.</p>
      </div>

      <div className="divider" />

      {!generatedPassword ? (
        <form onSubmit={handleRegister}>
          <div className="form-group">
            <label className="label">Utilizador (Ex: email ou identificador)</label>
            <div className="input-wrapper">
              <span className="input-icon"><User size={15} /></span>
              <input
                type="text"
                className="input"
                value={username}
                onChange={(e) => { setUsername(e.target.value); setError(''); }}
                placeholder="Introduza o seu identificador"
                autoComplete="username"
              />
            </div>
          </div>

          {error && (
            <div className="error-banner" style={{marginBottom: "1rem"}}>
              <AlertTriangle size={14} />
              {error}
            </div>
          )}

          <button className="btn btn-primary btn-block" type="submit" disabled={isLoading} style={{marginBottom: "1rem"}}>
            <Sparkles size={15} />
            <span>{isLoading ? "A gerar..." : "Gerar Acesso e Chaves"}</span>
          </button>
        </form>
      ) : (
        <div className="animate-in" style={{ marginTop: '0.25rem' }}>
          <div className="warning-box">
            <span className="warning-box-icon"><AlertTriangle size={14} /></span>
            <p className="warning-box-text">
              <strong>Registo efetuado! Guarda esta password.</strong><br/>
              A mesma será necessária (em conjunto com o teu utilizador "{username}") para entrar no sistema e não pode ser recuperada.
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
          Já tem conta?{' '}<span>Fazer login</span>
        </button>
      </div>
    </div>
  );
}
