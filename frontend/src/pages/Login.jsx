import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, Eye, EyeOff, LogIn, AlertCircle } from 'lucide-react';
import { api } from '../services/api';

export default function Login() {
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  // Função para gerar um "username" determinístico a partir da password
  // Isto permite que o utilizador não tenha de introduzir um username, 
  // mantendo a compatibilidade com o backend.
  const deriveUsername = async (pwd) => {
    const encoder = new TextEncoder();
    const data = encoder.encode(pwd);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  };

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
      navigate('/send'); // Ou para onde quer que a app vá após o login
    } catch (err) {
      setError(err.message || 'Credenciais inválidas ou erro no servidor.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <span className="badge">
          <Lock size={10} />
          Autenticação Segura
        </span>
        <h1 className="title">Aceder ao Sistema</h1>
        <p className="subtitle">Introduza a sua password de 16 caracteres para entrar.</p>
      </div>

      <div className="divider" />

      <form onSubmit={handleLogin}>
        <div className="form-group">
          <label className="label">A tua Password (16 caracteres)</label>
          <div className="input-wrapper">
            <span className="input-icon"><Lock size={15} /></span>
            <input
              type={showPassword ? 'text' : 'password'}
              className={`input input-with-action ${error ? 'error' : ''}`}
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

        <button type="submit" className="btn btn-primary btn-block" disabled={isLoading}>
          <LogIn size={15} />
          {isLoading ? 'A entrar...' : 'Entrar'}
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
