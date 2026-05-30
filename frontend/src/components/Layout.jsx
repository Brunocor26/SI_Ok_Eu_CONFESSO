import { useNavigate, useLocation } from 'react-router-dom';
import { Shield, Send, Unlock, CheckCircle, User } from 'lucide-react';

const navItems = [
  { key: 'send',    label: 'Enviar',      icon: Send,        path: '/send' },
  { key: 'decrypt', label: 'Desencriptar',icon: Unlock,      path: '/decrypt' },
  { key: 'verify',  label: 'Verificar',   icon: CheckCircle, path: '/verify' },
  { key: 'register',label: 'Registo',     icon: User,        path: '/register' },
];

export default function Layout({ children, activeTab }) {
  const navigate = useNavigate();

  return (
    <div className="bg-background text-on-background min-h-screen flex flex-col antialiased selection:bg-primary-container selection:text-on-primary-container">
      {/* TopAppBar */}
      <header className="bg-background border-b border-outline-variant flex items-center justify-between px-6 h-16 w-full sticky top-0 z-40 mx-auto max-w-[640px]">
        <div className="flex items-center gap-3 cursor-pointer active:opacity-80 transition-opacity" onClick={() => navigate('/send')}>
          <Shield size={20} className="text-on-background" fill="currentColor" />
          <span className="text-[18px] font-semibold text-on-background uppercase tracking-wider" style={{ fontFamily: 'Inter, sans-serif' }}>
            OK, Eu Confesso
          </span>
        </div>
        {/* Desktop nav */}
        <nav className="hidden md:flex gap-6">
          {navItems.map(({ key, label, icon: Icon, path }) => (
            <button
              key={key}
              onClick={() => navigate(path)}
              className={`text-[12px] font-medium uppercase tracking-wider flex items-center gap-2 transition-colors ${
                activeTab === key ? 'text-primary font-semibold' : 'text-on-surface-variant hover:text-primary'
              }`}
            >
              <Icon size={16} />
              {label}
            </button>
          ))}
        </nav>
      </header>

      {/* Main */}
      <main className="flex-1 flex flex-col w-full max-w-[640px] mx-auto px-6 pt-12 pb-24 md:pb-12">
        {children}
      </main>

      {/* Footer (desktop) */}
      <footer className="hidden md:flex mt-auto py-8 flex-col items-center gap-4 w-full max-w-[640px] mx-auto text-center border-t border-outline-variant">
        <div className="flex gap-6 text-[13px]">
          <span className="text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer">Privacidade</span>
          <span className="text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer">Termos</span>
          <span className="text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer">Segurança</span>
        </div>
        <div className="text-[12px] text-on-surface-variant opacity-60">© 2026 OK, Eu Confesso — Encriptação Ponta-a-Ponta</div>
      </footer>

      {/* BottomNavBar (mobile) */}
      <nav className="fixed bottom-0 left-0 w-full z-50 flex justify-around items-center h-16 bg-surface-container-low border-t border-outline-variant md:hidden">
        {navItems.map(({ key, label, icon: Icon, path }) => {
          const isActive = activeTab === key;
          return (
            <button
              key={key}
              onClick={() => navigate(path)}
              className={`flex flex-col items-center justify-center flex-1 h-full relative transition-all duration-200 active:scale-95 ${
                isActive ? 'text-on-background font-bold' : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              {isActive && <div className="absolute top-0 w-8 h-0.5 bg-primary rounded-b" />}
              <Icon
                size={16}
                className={isActive ? 'text-primary mb-1' : 'mb-1'}
                {...(isActive ? { fill: 'currentColor' } : {})}
              />
              <span className={`text-[10px] font-medium uppercase tracking-widest ${isActive ? 'text-primary' : ''}`}>
                {label}
              </span>
            </button>
          );
        })}
      </nav>
    </div>
  );
}
