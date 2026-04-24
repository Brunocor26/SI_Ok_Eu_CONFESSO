import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, User, Eye, EyeOff, LogIn, AlertCircle } from 'lucide-react';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleLogin = (e) => {
    e.preventDefault();
    if (!username.trim()) {
      setError('Introduza o nome de utilizador.');
      return;
    }
    if (password.length !== 16) {
      setError('A password deve ter exatamente 16 caracteres.');
      return;
    }
    setError('');
    alert('Autenticado com sucesso (Mock)!');
  };

  return (
    <div className="card">
      <div className="card-header">
        <span className="badge">
          <Lock size={10} />
          Autenticação Segura
        </span>
        <h1 className="title">Bem-vindo de volta</h1>
        <p className="subtitle">Introduza as suas credenciais para aceder ao sistema.</p>
      </div>

      <div className="divider" />

      <form onSubmit={handleLogin}>
        <div className="form-group">
          <label className="label">Utilizador</label>
          <div className="input-wrapper">
            <span className="input-icon"><User size={15} /></span>
            <input
              type="text"
              className="input"
              value={username}
              onChange={(e) => { setUsername(e.target.value); setError(''); }}
              placeholder="nome.apelido"
              autoComplete="username"
            />
          </div>
        </div>

        <div className="form-group">
          <label className="label">Password (16 caracteres)</label>
          <div className="input-wrapper">
            <span className="input-icon"><Lock size={15} /></span>
            <input
              type={showPassword ? 'text' : 'password'}
              className={`input input-with-action ${error && username.trim() ? 'error' : ''}`}
              value={password}
              onChange={(e) => { setPassword(e.target.value); setError(''); }}
              placeholder="••••••••••••••••"
              maxLength={16}
              autoComplete="current-password"
            />
            <button
              type="button"
              className="input-action-btn"
              onClick={() => setShowPassword(!showPassword)}
              tabIndex={-1}
            >
              {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
            </button>
          </div>
          <div className="input-hint">
            <span className={`char-count ${password.length === 16 ? 'ok' : ''}`}>
              {password.length}/16
            </span>
          </div>
        </div>

        {error && (
          <div className="error-banner">
            <AlertCircle size={14} />
            {error}
          </div>
        )}

        <button type="submit" className="btn btn-primary btn-block">
          <LogIn size={15} />
          Entrar
        </button>
      </form>

      <div className="card-footer">
        <button type="button" className="link-btn" onClick={() => navigate('/register')}>
          Não tem conta?{' '}<span>Criar acesso</span>
        </button>
      </div>
    </div>
  );
}
