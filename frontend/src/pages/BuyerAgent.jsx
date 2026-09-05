import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useSearchParams } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';
import { submitIntent, negotiate, checkPaymentStatus, getCatalog, getAuthStatus, updateAuthStatus, sendApprovalEmail } from '../api/client';
import { fmtInr, fmtPct } from '../utils/format';

const PipelineStage = ({ label, active, color }) => {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const [searchParams] = useSearchParams();
  
  let bg = isDark ? 'bg-darkSurfaceEl' : 'bg-lightSurfaceEl';
  let tc = isDark ? 'text-darkText3' : 'text-lightText3';
  let icon = '○';

  if (active) {
    if (color === 'green') {
      bg = isDark ? 'bg-greenSoft' : 'bg-lightGreenSoft';
      tc = isDark ? 'text-green' : 'text-lightGreen';
      icon = '✓';
    } else if (color === 'amber') {
      bg = isDark ? 'bg-amberSoft' : 'bg-lightAmberSoft';
      tc = isDark ? 'text-amber' : 'text-lightAmber';
      icon = '●';
    } else if (color === 'red') {
      bg = isDark ? 'bg-redSoft' : 'bg-lightRedSoft';
      tc = isDark ? 'text-red' : 'text-lightRed';
      icon = '✗';
    }
  }

  return (
    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg ${bg}`}>
      <span className={tc}>{icon}</span>
      <span className={`text-[11px] font-bold tracking-wide ${tc}`}>{label}</span>
    </div>
  );
};

export default function BuyerAgent() {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const [searchParams] = useSearchParams();
  const [catalog, setCatalog] = useState([]);

  // States
  const [query, setQuery] = useState("Find me 5 Pro Licenses under ₹9,500 and buy them.");
  const [loading, setLoading] = useState(false);
  const [loadingText, setLoadingText] = useState("");
  
  const [payload, setPayload] = useState(null);
  const [response, setResponse] = useState(null);
  
  // Auth & Payment
  const [merchantAuth, setMerchantAuth] = useState(null); // 'APPROVED', 'DECLINED', null
  const [paymentStatus, setPaymentStatus] = useState(null); // Razorpay status response
  const [paymentError, setPaymentError] = useState(null);
  const [authDevice, setAuthDevice] = useState(null); // 'Desktop' or 'Phone'
  const [emailStatus, setEmailStatus] = useState(null); // 'SENDING', 'SENT', 'FAILED'

  useEffect(() => {
    getCatalog().then(setCatalog).catch(console.error);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setLoadingText("Analyzing buyer intent...");
    setPayload(null);
    setResponse(null);
    setMerchantAuth(null);
    setPaymentStatus(null);
    setPaymentError(null);

    try {
      const intentData = await submitIntent(query);
      const payl = {
        sku: intentData.sku || 'SaaS-PRO-1M',
        requested_quantity: intentData.requested_quantity || 1,
        requested_discount_pct: intentData.requested_discount_pct || 0.0,
      };
      setPayload(payl);
      
      setLoadingText("Checking merchant policy & negotiating...");
      const negRes = await negotiate(payl);
      setResponse(negRes);
      
    } catch (err) {
      console.error(err);
      alert("Failed to process request. Ensure backend is running.");
    } finally {
      setLoading(false);
    }
  };

  const handleApproveDesktop = async () => {
    setLoading(true);
    await updateAuthStatus(response.transaction_id, 'APPROVE', 'Desktop');
    setMerchantAuth('APPROVED');
    setAuthDevice('Desktop');
    setLoading(false);
  };
  const handleRejectDesktop = async () => {
    setLoading(true);
    await updateAuthStatus(response.transaction_id, 'REJECT', 'Desktop');
    setMerchantAuth('DECLINED');
    setAuthDevice('Desktop');
    setLoading(false);
  };
  
  const handleApprovePhone = async () => {
    setMerchantAuth('PHONE_PENDING');
    setEmailStatus('SENDING');
    const merchantEmail = localStorage.getItem('merchantEmail');
    if (merchantEmail && merchantEmail.includes('@')) {
      try {
        await sendApprovalEmail(response.transaction_id, merchantEmail);
        setEmailStatus('SENT');
      } catch (err) {
        console.error(err);
        setEmailStatus('FAILED');
      }
    } else {
      setEmailStatus('FAILED');
    }
  };

  useEffect(() => {
    let interval;
    if (merchantAuth === 'PHONE_PENDING' && response?.transaction_id) {
      interval = setInterval(async () => {
        try {
          const authData = await getAuthStatus(response.transaction_id);
          if (authData.merchant_auth === 'APPROVED') {
            setMerchantAuth('APPROVED');
            setAuthDevice('Phone');
            clearInterval(interval);
          } else if (authData.merchant_auth === 'DECLINED') {
            setMerchantAuth('DECLINED');
            setAuthDevice('Phone');
            clearInterval(interval);
          }
        } catch (err) {
          console.error("Polling error", err);
        }
      }, 1500);
    }
    return () => clearInterval(interval);
  }, [merchantAuth, response]);


  const loadRazorpay = (options) => {
    return new Promise((resolve) => {
      const script = document.createElement('script');
      script.src = 'https://checkout.razorpay.com/v1/checkout.js';
      script.onload = () => {
        const rzp = new window.Razorpay(options);
        rzp.on('payment.failed', function (resp) {
          setPaymentError(resp.error.description);
        });
        rzp.open();
        resolve(true);
      };
      script.onerror = () => resolve(false);
      document.body.appendChild(script);
    });
  };

  const handlePay = () => {
    const orderId = response?.razorpay_order_id;
    if (!orderId) return;
    
    const options = {
      key: response.razorpay_key_id,
      amount: response.amount_paise,
      currency: "INR",
      name: "A.M.E. Merchant",
      description: `Order ${orderId}`,
      order_id: orderId,
      handler: function (resp) {
        setLoading(true);
        setLoadingText("Verifying payment...");
        checkPaymentStatus(orderId).then(data => {
          setPaymentStatus(data);
          setLoading(false);
        }).catch(err => {
          console.error(err);
          setPaymentError("Verification failed.");
          setLoading(false);
        });
      },
      theme: { color: "#D99A3D" }
    };
    loadRazorpay(options);
  };

  const checkStatus = () => {
    if (!response?.razorpay_order_id) return;
    setLoading(true);
    setLoadingText("Checking status...");
    checkPaymentStatus(response.razorpay_order_id).then(data => {
      setPaymentStatus(data);
      setLoading(false);
    }).catch(err => {
      setPaymentError("Could not fetch status.");
      setLoading(false);
    });
  };

  const isPaid = paymentStatus?.status === 'paid';
  const status = response?.status || "";
  const prod = catalog.find(p => p.sku === payload?.sku);
  const qty = payload?.requested_quantity || 1;
  const baseP = prod?.base_price_inr || 0;
  const baseTotal = baseP * qty;
  const negTotal = response?.total_negotiated_price_inr || 0;
  const dealSavings = baseTotal - negTotal;
  const reqD = payload?.requested_discount_pct || 0;

  const cardCls = `rounded-2xl border p-6 shadow-sm ${
    isDark ? 'bg-darkSurface border-darkBorder' : 'bg-lightSurface border-lightBorder'
  }`;
  const hdrCls = `text-[11px] font-bold tracking-wider uppercase mb-3 ${isDark ? 'text-darkText3' : 'text-lightText3'}`;
  
  const Row = ({ k, v, success, strike }) => (
    <div className={`flex justify-between items-center py-2 border-b last:border-none ${isDark ? 'border-darkBorder' : 'border-lightBorder'}`}>
      <span className={`text-[11px] font-bold tracking-wider uppercase ${success ? (isDark ? 'text-green' : 'text-lightGreen') : (isDark ? 'text-darkText3' : 'text-lightText3')}`}>{k}</span>
      <span className={`text-[15px] font-semibold ${strike ? 'line-through opacity-60' : ''} ${success ? (isDark ? 'text-green' : 'text-lightGreen') : (isDark ? 'text-darkText1' : 'text-lightText1')}`}>{v}</span>
    </div>
  );

  const Msg = ({ who, type, children }) => {
    let cls = isDark ? 'border-darkBorder bg-darkSurfaceEl' : 'border-lightBorder bg-lightSurfaceEl';
    let line = isDark ? 'border-l-darkText2' : 'border-l-lightText2';
    
    if (type === 'merch') line = isDark ? 'border-l-amber' : 'border-l-lightAmber';
    if (type === 'pay') line = isDark ? 'border-l-green' : 'border-l-lightGreen';
    if (type === 'sys-amber') {
      cls = isDark ? 'bg-amberSoft border-amber' : 'bg-lightAmberSoft border-lightAmber';
      line = 'border-l-transparent';
    }
    if (type === 'sys-red') {
      cls = isDark ? 'bg-redSoft border-red' : 'bg-lightRedSoft border-lightRed';
      line = 'border-l-transparent';
    }
    if (type === 'sys-green') {
      cls = isDark ? 'bg-greenSoft border-green' : 'bg-lightGreenSoft border-lightGreen';
      line = 'border-l-transparent';
    }

    return (
      <div className={`px-4 py-3 rounded-xl border border-l-[3px] text-sm mb-3 ${cls} ${line}`}>
        <div className={`text-[10px] font-bold uppercase tracking-wider mb-1 ${isDark ? 'text-darkText3' : 'text-lightText3'}`}>{who}</div>
        <div>{children}</div>
      </div>
    );
  };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
      <h2 className="text-[1.7rem] font-extrabold mb-1">BUYER AGENT</h2>
      <p className={`text-sm mb-6 ${isDark ? 'text-darkText2' : 'text-lightText2'}`}>Tell the agent what you want to buy.</p>

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="flex gap-3 mb-8">
        <input 
          type="text" 
          value={query}
          onChange={e => setQuery(e.target.value)}
          disabled={loading}
          className={`flex-1 rounded-xl border px-5 py-3 text-base focus:outline-none focus:ring-2 ${
            isDark ? 'bg-darkSurfaceEl border-darkBorder text-darkText1 focus:ring-amberSoft focus:border-amber' : 'bg-lightSurfaceEl border-lightBorder text-lightText1 focus:ring-lightAmberSoft focus:border-lightAmber'
          }`}
        />
        <button 
          disabled={loading}
          type="submit" 
          className={`px-8 py-3 rounded-xl font-bold transition-transform hover:-translate-y-0.5 ${
            isDark ? 'bg-amber text-[#0D0B08] hover:bg-[#E8B45B]' : 'bg-lightAmber text-white hover:bg-[#F0A832]'
          }`}
        >
          {loading ? 'PROCESSING...' : 'PROCESS INTENT →'}
        </button>
      </form>

      {loading && !response && (
        <div className={`p-6 text-center text-sm font-medium ${isDark ? 'text-darkText2' : 'text-lightText2'}`}>
          <div className="animate-pulse">{loadingText}</div>
        </div>
      )}

      {response && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          {/* Pipeline */}
          <div className="flex items-center gap-2 flex-wrap mb-8">
            <PipelineStage label="DISCOVER" active={true} color="green" /> <Arrow/>
            <PipelineStage label="SELECT" active={true} color="green" /> <Arrow/>
            <PipelineStage label="VALIDATE" active={status !== 'REJECTED'} color={status !== 'REJECTED' ? 'green' : 'red'} /> <Arrow/>
            <PipelineStage label="NEGOTIATE" active={['ACCEPTED', 'COUNTER_OFFER'].includes(status)} color={['ACCEPTED', 'COUNTER_OFFER'].includes(status) ? 'green' : 'red'} /> <Arrow/>
            <PipelineStage label="AUTHORIZE" active={merchantAuth !== null || ['ACCEPTED', 'COUNTER_OFFER'].includes(status)} color={merchantAuth === 'APPROVED' ? 'green' : (merchantAuth === 'DECLINED' ? 'red' : 'amber')} /> <Arrow/>
            <PipelineStage label="PAY" active={!!response.razorpay_order_id && merchantAuth === 'APPROVED'} color={(merchantAuth === 'APPROVED' && !isPaid) ? 'amber' : (isPaid ? 'green' : '')} /> <Arrow/>
            <PipelineStage label="CONFIRM" active={isPaid} color={isPaid ? 'green' : ''} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Left Col: Chat */}
            <div>
              <div className={hdrCls}>AGENT-TO-AGENT COMMERCE</div>
              
              <Msg who="AI BUYER" type="buyer">I need {qty} units of {payload.sku} with a {reqD}% discount.</Msg>
              
              {prod && (
                <>
                  <Msg who="MERCHANT AGENT" type="merch">Catalog match: <b>{prod.name}</b>. Inventory validated — {prod.stock} units available.</Msg>
                  <Msg who="POLICY ENGINE" type="merch">Requested discount: {fmtPct(reqD)}. Maximum permitted: {fmtPct(prod.max_discount_pct)}. <b>WITHIN POLICY</b>.</Msg>
                </>
              )}
              
              <Msg who="MERCHANT AGENT" type="merch">Offer <b>{status}</b>. Unit price: <b>{fmtInr(response.negotiated_unit_price)}</b>. Total: <b>{fmtInr(negTotal)}</b>.</Msg>
              
              {!merchantAuth && (
                <Msg who="SYSTEM" type="sys-amber">MERCHANT AUTHORIZATION REQUIRED</Msg>
              )}
              {merchantAuth === 'DECLINED' && (
                <Msg who="SYSTEM" type="sys-red">MERCHANT AUTHORIZATION DECLINED</Msg>
              )}
              {merchantAuth === 'APPROVED' && (
                <Msg who="SYSTEM" type="sys-green">MERCHANT AUTHORIZATION GRANTED {authDevice ? `(VIA ${authDevice.toUpperCase()})` : ''}</Msg>
              )}
              
              {merchantAuth === 'APPROVED' && response.razorpay_order_id && (
                <Msg who="RAZORPAY" type="pay">Order created: <span className="font-mono text-[11px]">{response.razorpay_order_id}</span></Msg>
              )}
              
              {isPaid && (
                <Msg who="BUYER" type="pay">✓ Payment completed and verified. <b>{fmtInr(negTotal)} PAID</b></Msg>
              )}
              
              {/* Expander */}
              <details className={`mt-4 rounded-xl border p-4 text-xs font-mono overflow-x-auto ${isDark ? 'border-darkBorder' : 'border-lightBorder'}`}>
                <summary className={`font-sans font-bold cursor-pointer outline-none ${isDark ? 'text-darkText2' : 'text-lightText2'}`}>AUDIT TRAIL — RAW PAYLOAD</summary>
                <div className="mt-4 opacity-80 whitespace-pre-wrap">{JSON.stringify(response, null, 2)}</div>
                {paymentStatus && <div className="mt-4 opacity-80 border-t pt-2">{JSON.stringify(paymentStatus, null, 2)}</div>}
              </details>
            </div>

            {/* Right Col: Deal / Auth / Checkout */}
            <div>
              <div className={hdrCls}>LIVE DEAL</div>
              <div className={`${cardCls} mb-6 border-l-4 ${isDark ? 'border-l-amber' : 'border-l-lightAmber'}`}>
                <Row k="PRODUCT" v={prod?.name || payload?.sku} />
                <Row k="QUANTITY" v={`${qty} units`} />
                <Row k="ORIGINAL TOTAL" v={fmtInr(baseTotal)} strike />
                <div className="flex justify-between items-end py-4">
                  <span className={`text-[11px] font-bold tracking-wider uppercase ${isDark ? 'text-darkText3' : 'text-lightText3'}`}>NEGOTIATED TOTAL</span>
                  <span className={`text-4xl font-extrabold ${isDark ? 'text-darkText1' : 'text-lightText1'}`}>{fmtInr(negTotal)}</span>
                </div>
                <Row k="SAVINGS" v={fmtInr(dealSavings)} success />
              </div>

              {merchantAuth === 'DECLINED' ? (
                <div className={`${cardCls} mb-6 border-l-4 border-l-red`}>
                  <div className={`${hdrCls} !text-red`}>MERCHANT DECLINED</div>
                  <div className="text-sm">A.M.E. prepared the transaction, but merchant authorization was not granted. Transaction not charged.</div>
                </div>
              ) : merchantAuth === 'PHONE_PENDING' ? (
                <div className={`${cardCls} mb-6 border-l-4 ${isDark ? 'border-l-amber' : 'border-l-lightAmber'}`}>
                  <div className={hdrCls}>📱 WAITING FOR MERCHANT</div>
                  <div className={`text-sm mb-4 ${isDark ? 'text-darkText2' : 'text-lightText2'}`}>Approval request sent to phone.</div>
                  <Row k="PRODUCT" v={`${qty} × ${prod?.name || payload?.sku}`} />
                  <Row k="TRANSACTION VALUE" v={fmtInr(negTotal)} />
                  <div className="my-4 border-t border-dashed opacity-20"></div>
                  
                  <div className="text-center mb-4">
                    <div className="inline-block p-4 bg-white rounded-lg mb-2">
                      <div className="w-32 h-32 flex items-center justify-center border-2 border-dashed border-gray-300 text-gray-400 text-xs text-center p-2">
                        PHONE APPROVAL AVAILABLE IN DEPLOYED VERSION
                      </div>
                    </div>
                    <div className={`text-xs ${isDark ? 'text-darkText3' : 'text-lightText3'}`}>
                      <a href={`/approval/${response.transaction_id}`} target="_blank" rel="noreferrer" className="underline hover:text-amber">Open dev approval link</a>
                    </div>
                  </div>
                  
                  <button onClick={() => setMerchantAuth(null)} className={`w-full py-2.5 rounded-xl font-bold border transition-transform hover:-translate-y-0.5 ${isDark ? 'border-darkBorder hover:bg-darkSurfaceEl text-darkText1' : 'border-lightBorder hover:bg-lightSurfaceEl text-lightText1'}`}>CANCEL</button>
                </div>
              ) : !merchantAuth && response?.razorpay_order_id ? (
                <div className={`${cardCls} mb-6 border-l-4 ${isDark ? 'border-l-amber' : 'border-l-lightAmber'}`}>
                  <div className={hdrCls}>MERCHANT AUTHORIZATION REQUIRED</div>
                  <Row k="PRODUCT" v={`${qty} × ${prod?.name || payload?.sku}`} />
                  <Row k="UNIT PRICE" v={fmtInr(response.negotiated_unit_price)} />
                  <Row k="DISCOUNT" v={fmtPct(reqD)} />
                  <Row k="MAX ALLOWED" v={fmtPct(prod?.max_discount_pct)} success />
                  <div className="my-2 border-t border-dashed opacity-20"></div>
                  <Row k="TRANSACTION VALUE" v={fmtInr(negTotal)} />
                  
                  <div className="mt-6 mb-2 text-center text-[10px] font-bold tracking-widest opacity-50">AUTHORIZE FROM</div>
                  <div className="flex flex-col gap-3">
                    <button onClick={handleApproveDesktop} className={`w-full py-3 rounded-xl font-bold border transition-transform hover:-translate-y-0.5 ${isDark ? 'border-darkBorder hover:bg-darkSurfaceEl text-darkText1' : 'border-lightBorder hover:bg-lightSurfaceEl text-lightText1'}`}>💻 APPROVE ON DESKTOP</button>
                    <button onClick={handleApprovePhone} className={`w-full py-3 rounded-xl font-bold border transition-transform hover:-translate-y-0.5 ${isDark ? 'border-darkBorder hover:bg-darkSurfaceEl text-darkText1' : 'border-lightBorder hover:bg-lightSurfaceEl text-lightText1'}`}>📱 APPROVE ON PHONE</button>
                    <button onClick={handleRejectDesktop} className={`w-full py-2 mt-2 text-xs rounded-xl font-bold text-red opacity-70 hover:opacity-100 transition-opacity`}>REJECT</button>
                  </div>
                </div>
              ) : merchantAuth === 'APPROVED' && response?.razorpay_order_id ? (
                <div className={`${cardCls} mb-6 border-l-4 ${isDark ? 'border-l-green' : 'border-l-lightGreen'}`}>
                  <div className={`${hdrCls} ${isDark ? '!text-green' : '!text-lightGreen'}`}>✓ MERCHANT APPROVED</div>
                  {!isPaid ? (
                    <>
                      <button onClick={handlePay} disabled={loading} className={`w-full py-3 mb-3 rounded-xl font-bold transition-transform hover:-translate-y-0.5 ${isDark ? 'bg-amber text-[#0D0B08]' : 'bg-lightAmber text-white'}`}>
                        {loading ? 'PROCESSING...' : 'PAY VIA RAZORPAY →'}
                      </button>
                      <button onClick={checkStatus} disabled={loading} className={`w-full py-2 text-xs font-bold rounded-lg border transition-transform hover:-translate-y-0.5 ${isDark ? 'border-darkBorder text-darkText2 hover:text-darkText1' : 'border-lightBorder text-lightText2 hover:text-lightText1'}`}>
                        CHECK PAYMENT STATUS
                      </button>
                      {paymentError && <div className="text-red text-xs mt-2 text-center">{paymentError}</div>}
                    </>
                  ) : (
                    <div className="text-center py-4">
                      <div className={`text-lg font-bold mb-1 ${isDark ? 'text-green' : 'text-lightGreen'}`}>PAYMENT SUCCESSFUL</div>
                      <div className="text-xs opacity-70">Razorpay Status: {paymentStatus?.status}</div>
                    </div>
                  )}
                </div>
              ) : null}

              {/* Guardrails */}
              {prod && (
                <div className={cardCls}>
                  <div className={hdrCls}>MERCHANT GUARDRAILS</div>
                  <Row k="MAX DISCOUNT" v={fmtPct(prod.max_discount_pct)} />
                  <Row k="STOCK" v={`${prod.stock} units`} />
                  <Row k="POLICY" v="Merchant Catalog" />
                  <div className={`text-[10px] mt-3 leading-relaxed ${isDark ? 'text-darkText3' : 'text-lightText3'}`}>
                    Discount bounds and inventory limits are hard-coded merchant rules, not LLM judgment.
                  </div>
                </div>
              )}
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}

const Arrow = () => {
  const { theme } = useTheme();
  return <div className={theme === 'dark' ? 'text-darkText3' : 'text-lightText3'}>&rarr;</div>;
};
