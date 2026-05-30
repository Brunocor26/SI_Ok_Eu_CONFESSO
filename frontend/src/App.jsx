import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Register from './pages/Register';
import SendMessage from './pages/SendMessage';
import DecryptMessage from './pages/DecryptMessage';
import VerifyReceipt from './pages/VerifyReceipt';
import './index.css';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/send" replace />} />
        <Route path="/register" element={<Register />} />
        <Route path="/send" element={<SendMessage />} />
        <Route path="/decrypt" element={<DecryptMessage />} />
        <Route path="/verify" element={<VerifyReceipt />} />
        <Route path="*" element={<Navigate to="/send" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
