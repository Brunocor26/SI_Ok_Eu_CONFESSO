import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ShieldCheck } from 'lucide-react';
import Login from './pages/Login';
import Register from './pages/Register';
import './index.css';

function App() {
  return (
    <BrowserRouter>
      <div className="app-container">
        <div className="brand">
          <div className="brand-icon">
            <ShieldCheck size={22} color="white" />
          </div>
          <div className="brand-text">
            <div className="brand-name">OK, Eu Confesso</div>
            <div className="brand-tagline">Mensagens Seguras</div>
          </div>
        </div>
        <Routes>
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
