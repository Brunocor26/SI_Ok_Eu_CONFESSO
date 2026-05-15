import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import Login from './pages/Login';
import Register from './pages/Register';
import SendMessage from './pages/SendMessage';
import DecryptMessage from './pages/DecryptMessage';
import VerifyReceipt from './pages/VerifyReceipt';
import { api } from './services/api';
import './index.css';

function AuthGuard({ children }) {
  const [checking, setChecking] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    api.auth.me()
      .then(() => setChecking(false))
      .catch(() => navigate('/login', { replace: true }));
  }, [navigate]);

  if (checking) return null;
  return children;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/send" element={<AuthGuard><SendMessage /></AuthGuard>} />
        <Route path="/decrypt" element={<DecryptMessage />} />
        <Route path="/verify" element={<VerifyReceipt />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
