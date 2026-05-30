import { useState } from 'react';
import { ClipboardList, ArrowRight, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import Layout from '../components/Layout';
import { api } from '../services/api';

export default function VerifyReceipt() {
  const [trackingCode, setTrackingCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null); // null | 'read' | 'pending' | 'error' | 'unavailable'
  const [receiptData, setReceiptData] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');

  const handleVerify = async (e) => {
    e.preventDefault();
    if (!trackingCode.trim()) return;
    setIsLoading(true);
    setResult(null);
    setReceiptData(null);
    setErrorMsg('');
    try {
      const data = await api.receipts.check(trackingCode.trim());
      setReceiptData(data);
      setResult(data.read ? 'read' : 'pending');
    } catch (err) {
      if (err.message?.includes('404') || err.message?.includes('não encontrado') || err.message?.includes('not found')) {
        setResult('unavailable');
      } else {
        setErrorMsg(err.message || 'Erro ao verificar o código.');
        setResult('error');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Layout activeTab="verify">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-4">
          <ClipboardList size={14} className="text-on-surface-variant" />
          <span className="text-[12px] font-medium text-on-surface-variant uppercase tracking-widest">Estado da Mensagem</span>
        </div>
        <h1 className="text-[24px] font-semibold text-on-surface tracking-tight mb-2">Verificar Recibo</h1>
        <p className="text-[14px] text-on-surface-variant">Introduz o código de rastreio.</p>
      </div>

      {/* Form card */}
      <div className="bg-surface-container border border-outline-variant p-[28px] rounded flex flex-col gap-[18px] mb-8">
        <div className="flex flex-col gap-2">
          <label className="text-[12px] font-medium text-outline uppercase tracking-wider" htmlFor="tracking-code">
            Código de Rastreio
          </label>
          <input
            id="tracking-code"
            type="text"
            className="bg-surface-container-highest border border-outline-variant rounded p-4 font-[JetBrains_Mono,monospace] text-[14px] tracking-[0.05em] text-on-surface focus:border-on-surface focus:ring-0 outline-none transition-colors w-full"
            value={trackingCode}
            onChange={(e) => { setTrackingCode(e.target.value); setResult(null); }}
            placeholder=""
            autoComplete="off"
            spellCheck={false}
          />
        </div>
        <button
          type="button"
          className="bg-on-surface text-surface w-full py-4 rounded text-[12px] font-medium uppercase tracking-widest flex items-center justify-center gap-2 hover:bg-surface-bright hover:text-on-surface transition-colors mt-2 active:scale-[0.99] disabled:opacity-60"
          onClick={handleVerify}
          disabled={isLoading || !trackingCode.trim()}
        >
          {isLoading ? 'A verificar...' : 'Verificar'}
          <ArrowRight size={16} />
        </button>
      </div>

      {/* Result: read */}
      {result === 'read' && (
        <div className="bg-surface border border-outline-variant p-[28px] rounded flex flex-col gap-4 relative overflow-hidden">
          <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary rounded-l" />
          <div className="flex flex-col gap-3">
            {receiptData?.confirmed_received && (
              <div className="flex items-center gap-3">
                <CheckCircle size={20} className="text-primary" fill="currentColor" />
                <span className="text-[14px] text-on-surface">Receção confirmada</span>
              </div>
            )}
            <div className="flex items-center gap-3">
              <CheckCircle size={20} className="text-primary" fill="currentColor" />
              <span className="text-[14px] text-on-surface">Leitura confirmada</span>
            </div>
          </div>
          <div className="mt-2 pt-4 border-t border-surface-variant flex flex-col gap-2">
            {receiptData?.signature_valid ? (
              <p className="font-[JetBrains_Mono,monospace] text-[13px] text-on-surface-variant opacity-70">
                Assinatura SHA256withRSA válida.
              </p>
            ) : (
              <p className="font-[JetBrains_Mono,monospace] text-[13px] text-outline opacity-70">
                Assinatura não verificável (destinatário sem conta registada).
              </p>
            )}
            {receiptData?.receipt_text && (
              <p className="font-[JetBrains_Mono,monospace] text-[11px] text-outline break-all">
                {receiptData.receipt_text}
              </p>
            )}
          </div>
        </div>
      )}

      {/* Result: pending (not yet read) */}
      {result === 'pending' && (
        <div className="bg-surface border border-outline-variant p-[28px] rounded flex flex-col gap-4 relative overflow-hidden">
          <div className="absolute left-0 top-0 bottom-0 w-1 bg-tertiary rounded-l" />
          <div className="flex items-center gap-3">
            <Clock size={20} className="text-tertiary" />
            <span className="text-[14px] text-on-surface">Mensagem ainda não foi lida.</span>
          </div>
          <div className="mt-2 pt-4 border-t border-surface-variant">
            <p className="font-[JetBrains_Mono,monospace] text-[13px] text-on-surface-variant opacity-70">A aguardar leitura pelo destinatário.</p>
          </div>
        </div>
      )}

      {/* Result: feature unavailable */}
      {result === 'unavailable' && (
        <div className="bg-surface border border-outline-variant p-[28px] rounded flex flex-col gap-4">
          <div className="flex items-center gap-3">
            <AlertCircle size={20} className="text-outline" />
            <span className="text-[14px] text-on-surface-variant">Funcionalidade ainda não disponível no servidor.</span>
          </div>
        </div>
      )}

      {/* Result: error */}
      {result === 'error' && (
        <div className="flex items-center gap-2 text-error text-[13px] bg-error-container/20 border border-error/30 rounded px-3 py-2">
          <AlertCircle size={14} />
          {errorMsg}
        </div>
      )}
    </Layout>
  );
}
