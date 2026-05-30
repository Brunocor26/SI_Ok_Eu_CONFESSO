import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Unlock, Key, CheckCircle, Eye, AlertCircle, ShieldCheck, XCircle, Receipt, FileKey } from 'lucide-react';
import Layout from '../components/Layout';
import { api } from '../services/api';

const STEP_CODE = 1;
const STEP_CONFIRM_RECEIVED = 2;
const STEP_CONFIRM_READ = 3;
const STEP_RESULT = 4;
const STEP_DENIED = 5;

export default function DecryptMessage() {
  const [step, setStep] = useState(STEP_CODE);
  const [code, setCode] = useState('');
  const [password, setPassword] = useState('');
  const [encryptedBody, setEncryptedBody] = useState('');
  const [privateKey, setPrivateKey] = useState('');
  const [privateKeyFilename, setPrivateKeyFilename] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [decryptedData, setDecryptedData] = useState(null);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  const handlePrivateKeyFile = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (evt) => {
      setPrivateKey(evt.target.result);
      setPrivateKeyFilename(file.name);
    };
    reader.readAsText(file);
  };

  const handleCodeSubmit = (e) => {
    e.preventDefault();
    if (!code.trim() || !password.trim() || !encryptedBody.trim() || !privateKey.trim()) {
      setError('Preenche todos os campos (código, password, chave privada e corpo cifrado).');
      return;
    }
    setError('');
    setStep(STEP_CONFIRM_RECEIVED);
  };

  const handleConfirmReceived = async () => {
    setIsLoading(true);
    try {
      await api.receipts.verify(code);
      setStep(STEP_CONFIRM_READ);
    } catch (err) {
      setError(err.message || 'Erro ao confirmar receção.');
      setStep(STEP_CODE);
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirmRead = async () => {
    setIsLoading(true);
    try {
      const data = await api.messages.decrypt(code, password, encryptedBody, privateKey);
      setDecryptedData(data);
      setStep(STEP_RESULT);
    } catch (err) {
      setError(err.message || 'Código inválido ou mensagem não encontrada.');
      setStep(STEP_CODE);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeny = () => setStep(STEP_DENIED);

  const handleRetry = () => {
    setStep(STEP_CODE);
    setCode('');
    setPassword('');
    setEncryptedBody('');
    setPrivateKey('');
    setPrivateKeyFilename('');
    setError('');
    setDecryptedData(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <Layout activeTab="decrypt">
      {/* Header */}
      <div className="mb-8">
        <span className="text-[12px] font-medium text-primary uppercase tracking-widest mb-2 block">
          {step === STEP_CODE && 'Passo 1'}
          {step === STEP_CONFIRM_RECEIVED && 'Passo 2'}
          {step === STEP_CONFIRM_READ && 'Passo 3'}
          {step === STEP_RESULT && 'Passo 4'}
          {step === STEP_DENIED && 'Cancelado'}
        </span>
        <h1 className="text-[24px] font-semibold text-on-surface tracking-tight">Decifrar Mensagem</h1>
        {step === STEP_CODE && <p className="text-[14px] text-outline mt-2">Introduz o código recebido por email.</p>}
        {step === STEP_CONFIRM_RECEIVED && <p className="text-[14px] text-outline mt-2">Confirma a receção antes de decifrar.</p>}
        {step === STEP_CONFIRM_READ && <p className="text-[14px] text-outline mt-2">Confirma que vais ler a mensagem.</p>}
        {step === STEP_RESULT && <p className="text-[14px] text-outline mt-2">A mensagem foi desencriptada com sucesso e a chave foi destruída.</p>}
      </div>

      {error && (
        <div className="flex items-center gap-2 text-error text-[13px] bg-error-container/20 border border-error/30 rounded px-3 py-2 mb-6">
          <AlertCircle size={14} />
          {error}
        </div>
      )}

      {/* Step 1 — Code input */}
      {step === STEP_CODE && (
        <div className="bg-surface-container border border-outline-variant p-[28px] rounded flex flex-col gap-[18px]">
          <div className="flex flex-col gap-2">
            <label className="text-[12px] font-medium text-outline uppercase tracking-wider">Código de acesso</label>
            <div className="relative flex items-center">
              <Key size={14} className="absolute left-3 text-outline-variant" />
              <input
                type="text"
                className="w-full bg-surface-container-highest border border-outline-variant rounded p-4 pl-10 font-[JetBrains_Mono,monospace] text-[14px] tracking-[0.05em] text-on-surface focus:border-on-surface focus:ring-0 outline-none transition-colors"
                value={code}
                onChange={(e) => { setCode(e.target.value); setError(''); }}
                placeholder="Código recebido por email"
                autoComplete="off"
                spellCheck={false}
              />
            </div>
          </div>
          <div className="flex flex-col gap-2 mt-2">
            <label className="text-[12px] font-medium text-outline uppercase tracking-wider">A tua Password de Acesso</label>
            <div className="relative flex items-center">
              <Key size={14} className="absolute left-3 text-outline-variant" />
              <input
                type="password"
                className="w-full bg-surface-container-highest border border-outline-variant rounded p-4 pl-10 font-[JetBrains_Mono,monospace] text-[14px] tracking-[0.05em] text-on-surface focus:border-on-surface focus:ring-0 outline-none transition-colors"
                value={password}
                onChange={(e) => { setPassword(e.target.value); setError(''); }}
                placeholder="Necessária para aceder à tua chave privada"
                autoComplete="off"
              />
            </div>
          </div>
          <div className="flex flex-col gap-2 mt-2">
            <label className="text-[12px] font-medium text-outline uppercase tracking-wider">Corpo Cifrado</label>
            <textarea
              className="w-full bg-surface-container-highest border border-outline-variant rounded p-4 font-[JetBrains_Mono,monospace] text-[13px] tracking-[0.02em] text-on-surface focus:border-on-surface focus:ring-0 outline-none transition-colors h-32 resize-none"
              value={encryptedBody}
              onChange={(e) => { setEncryptedBody(e.target.value); setError(''); }}
              placeholder="Cola aqui a mensagem cifrada..."
              spellCheck={false}
            />
          </div>
          <div className="flex flex-col gap-2 mt-2">
            <label className="text-[12px] font-medium text-outline uppercase tracking-wider">Chave Privada</label>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pem"
              className="hidden"
              onChange={handlePrivateKeyFile}
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className={`w-full flex items-center gap-3 p-4 rounded border transition-colors text-left ${
                privateKeyFilename
                  ? 'border-on-surface bg-surface-container text-on-surface'
                  : 'border-outline-variant bg-surface-container-highest text-outline hover:border-outline'
              }`}
            >
              <FileKey size={16} className={privateKeyFilename ? 'text-primary' : 'text-outline-variant'} />
              <span className="font-[JetBrains_Mono,monospace] text-[13px] truncate">
                {privateKeyFilename || 'Selecionar ficheiro chave_privada.pem…'}
              </span>
            </button>
          </div>
          <button
            type="button"
            className="bg-on-surface text-surface w-full py-4 rounded text-[12px] font-medium uppercase tracking-widest flex items-center justify-center gap-2 hover:bg-surface-bright hover:text-on-surface transition-colors active:scale-[0.99]"
            onClick={handleCodeSubmit}
          >
            <Unlock size={14} />
            Verificar Código
          </button>
        </div>
      )}

      {/* Step 2 — Confirm received */}
      {step === STEP_CONFIRM_RECEIVED && (
        <div className="bg-surface-container border border-outline-variant p-[28px] rounded flex flex-col items-center gap-6 text-center">
          <div className="w-14 h-14 rounded-full bg-surface-container-high border border-outline-variant flex items-center justify-center">
            <CheckCircle size={28} className="text-primary" />
          </div>
          <div>
            <div className="text-[18px] font-semibold text-on-surface mb-2">Confirmação de Receção</div>
            <div className="text-[14px] text-on-surface-variant">Confirmas que recebeste esta mensagem?</div>
          </div>
          <div className="flex gap-4 w-full">
            <button
              className="flex-1 bg-on-surface text-surface py-3 rounded text-[12px] font-medium uppercase tracking-widest hover:bg-surface-bright hover:text-on-surface transition-colors active:scale-[0.99] disabled:opacity-60"
              onClick={handleConfirmReceived}
              disabled={isLoading}
            >
              {isLoading ? 'A confirmar...' : 'Sim, confirmo'}
            </button>
            <button
              className="px-6 py-3 rounded border border-outline-variant text-[12px] font-medium text-on-surface hover:bg-surface-container-high transition-colors"
              onClick={handleDeny}
              disabled={isLoading}
            >
              Não
            </button>
          </div>
        </div>
      )}

      {/* Step 3 — Confirm read */}
      {step === STEP_CONFIRM_READ && (
        <div className="bg-surface-container border border-outline-variant p-[28px] rounded flex flex-col items-center gap-6 text-center">
          <div className="w-14 h-14 rounded-full bg-surface-container-high border border-outline-variant flex items-center justify-center">
            <Eye size={28} className="text-primary" />
          </div>
          <div>
            <div className="text-[18px] font-semibold text-on-surface mb-2">Confirmação de Leitura</div>
            <div className="text-[14px] text-on-surface-variant">Confirmas que vais ler esta mensagem?</div>
          </div>
          <div className="flex gap-4 w-full">
            <button
              className="flex-1 bg-on-surface text-surface py-3 rounded text-[12px] font-medium uppercase tracking-widest hover:bg-surface-bright hover:text-on-surface transition-colors active:scale-[0.99] disabled:opacity-60"
              onClick={handleConfirmRead}
              disabled={isLoading}
            >
              {isLoading ? 'A decifrar...' : 'Sim, vou ler'}
            </button>
            <button
              className="px-6 py-3 rounded border border-outline-variant text-[12px] font-medium text-on-surface hover:bg-surface-container-high transition-colors"
              onClick={handleDeny}
              disabled={isLoading}
            >
              Não
            </button>
          </div>
        </div>
      )}

      {/* Step 4 — Decrypted message */}
      {step === STEP_RESULT && decryptedData && (
        <div className="bg-surface-container border border-outline-variant p-[28px] rounded flex flex-col gap-[18px]">
          {/* Success badge */}
          <div className="flex items-center gap-2 bg-[#0d1f0d] border border-[#1a3a1a] text-[#4ade80] px-3 py-2 rounded">
            <ShieldCheck size={14} />
            <span className="text-[12px] font-medium">Mensagem decifrada e autodestruída do servidor.</span>
          </div>

          {/* Message box */}
          <div className="bg-[#0f0f0f] border border-[#2a2a2a] rounded-lg p-6 flex flex-col">
            <h3 className="text-[18px] font-semibold text-on-surface mb-4">{decryptedData.subject}</h3>
            <hr className="border-[#2a2a2a] mb-4" />
            <p className="text-[14px] text-[#737373] whitespace-pre-line leading-relaxed">{decryptedData.body}</p>
          </div>

          {/* Receipt */}
          <div className="flex items-center gap-2 text-[#404040] border-t border-[#1f1f1f] pt-4">
            <Receipt size={12} />
            <span className="text-[12px] font-medium">O emissor foi notificado de que leste esta mensagem.</span>
          </div>

          {/* Actions */}
          <div className="flex flex-col sm:flex-row gap-4 mt-2">
            <button
              className="bg-[#fafafa] text-[#0a0a0a] text-[12px] font-medium px-6 py-3 rounded hover:bg-gray-200 transition-colors flex items-center justify-center gap-2"
              onClick={handleRetry}
            >
              Decifrar outra mensagem
            </button>
          </div>
        </div>
      )}

      {/* Step 5 — Denied */}
      {step === STEP_DENIED && (
        <div className="bg-surface-container border border-outline-variant p-[28px] rounded flex flex-col items-center gap-6 text-center">
          <div className="w-14 h-14 rounded-full bg-error-container/20 border border-error/30 flex items-center justify-center">
            <XCircle size={28} className="text-error" />
          </div>
          <div>
            <div className="text-[18px] font-semibold text-on-surface mb-2">Confirmação Recusada</div>
            <div className="text-[14px] text-on-surface-variant">A mensagem não foi decifrada.</div>
          </div>
          <button
            className="bg-on-surface text-surface w-full py-4 rounded text-[12px] font-medium uppercase tracking-widest flex items-center justify-center gap-2 hover:bg-surface-bright hover:text-on-surface transition-colors active:scale-[0.99]"
            onClick={handleRetry}
          >
            <Unlock size={14} />
            Tentar novamente
          </button>
        </div>
      )}

      <div className="mt-8 text-center">
        <button className="text-[13px] text-on-surface-variant hover:text-on-surface transition-colors" onClick={() => navigate('/login')}>
          Tens conta? <span className="underline">Entrar para enviar mensagens</span>
        </button>
      </div>
    </Layout>
  );
}
