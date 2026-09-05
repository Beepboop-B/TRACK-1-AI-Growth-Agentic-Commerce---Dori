import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getAuthStatus, updateAuthStatus, checkPaymentStatus } from '../api/client';
import { useTheme } from '../context/ThemeContext';
import { fmtInr, fmtPct } from '../utils/format';

export default function PhoneApproval() {
  const { token } = useParams();
  const navigate = useNavigate();
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState('');
  
  const [paymentStatus, setPaymentStatus] = useState(null);
  const [paymentError, setPaymentError] = useState(null);

  useEffect(() => {
    getAuthStatus(token).then(res => {
      setData(res);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setError("Transaction not found or could not be loaded.");
      setLoading(false);
    });
  }, [token]);

  const handleAction = async (action) => {
    setActionLoading(true);
    try {
      await updateAuthStatus(token, action, "Phone");
      const updated = await getAuthStatus(token);
      setData(updated);
    } catch (err) {
      setError("Failed to update status.");
    }
    setActionLoading(false);
  };

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
    const orderId = data?.razorpay_order_id;
    if (!orderId) return;
    
    const amountPaise = Math.round(data.total_negotiated_price_inr * 100);

    const options = {
      key: data.razorpay_key_id,
      amount: amountPaise,
      currency: "INR",
      name: "A.M.E. Merchant",
      description: `Order ${orderId}`,
      order_id: orderId,
      handler: function (resp) {
        setActionLoading(true);
        checkPaymentStatus(orderId).then(payRes => {
          setPaymentStatus(payRes);
          setActionLoading(false);
        }).catch(err => {
          console.error(err);
          setPaymentError("Verification failed.");
          setActionLoading(false);
        });
      },
      prefill: {
        name: "AI Buyer",
        email: "buyer@ame.local",
        contact: "9999999999"
      },
      theme: {
        color: isDark ? "#D99A3D" : "#B47C2A"
      }
    };
    
    setActionLoading(true);
    loadRazorpay(options).then(success => {
      setActionLoading(false);
      if (!success) setPaymentError("Failed to load Razorpay SDK.");
    });
  };

  const bg = isDark ? 'bg-darkBg text-darkText1' : 'bg-lightBg text-lightText1';
  const cardCls = `rounded-2xl border p-5 shadow-sm mb-6 ${isDark ? 'bg-darkSurface border-darkBorder' : 'bg-lightSurface border-lightBorder'}`;
  const hdrCls = `text-[11px] font-bold tracking-wider uppercase mb-3 ${isDark ? 'text-darkText3' : 'text-lightText3'}`;

  const Row = ({ k, v, success, strike }) => (
    <div className={`flex justify-between items-center py-2 border-b last:border-none ${isDark ? 'border-darkBorder' : 'border-lightBorder'}`}>
      <span className={`text-[11px] font-bold tracking-wider uppercase ${success ? (isDark ? 'text-green' : 'text-lightGreen') : (isDark ? 'text-darkText3' : 'text-lightText3')}`}>{k}</span>
      <span className={`text-[15px] font-semibold ${strike ? 'line-through opacity-60' : ''} ${success ? (isDark ? 'text-green' : 'text-lightGreen') : (isDark ? 'text-darkText1' : 'text-lightText1')}`}>{v}</span>
    </div>
  );

  if (loading) {
    return <div className={`min-h-screen p-6 flex items-center justify-center ${bg}`}>Loading...</div>;
  }

  if (error) {
    return (
      <div className={`min-h-screen p-6 flex flex-col items-center justify-center ${bg}`}>
        <div className="text-red font-bold mb-4">{error}</div>
        <button onClick={() => navigate('/')} className={`px-4 py-2 rounded-lg border ${isDark ? 'border-darkBorder hover:bg-darkSurfaceEl' : 'border-lightBorder hover:bg-lightSurfaceEl'}`}>Return Home</button>
      </div>
    );
  }

  const isPaid = paymentStatus?.status === 'paid';

  if (data?.merchant_auth === 'APPROVED') {
    return (
      <div className={`min-h-screen p-6 flex flex-col ${bg}`}>
        <div className="mb-8">
          <h1 className={`text-2xl font-extrabold tracking-tight ${isDark ? 'text-darkText1' : 'text-lightText1'}`}>A.M.E.</h1>
        </div>

        <div className={`${cardCls} border-l-4 ${isDark ? 'border-l-green' : 'border-l-lightGreen'} text-center py-8`}>
          <div className={`text-5xl font-bold mb-4 ${isDark ? 'text-green' : 'text-lightGreen'}`}>✓</div>
          <div className={`text-xl font-extrabold tracking-tight mb-2 ${isDark ? 'text-green' : 'text-lightGreen'}`}>MERCHANT APPROVED</div>
          <div className={`text-sm opacity-70`}>Transaction authorized from phone.</div>
        </div>
        
        {!isPaid ? (
          <div className={`${cardCls}`}>
             <div className="text-center mb-6">
                <div className="text-[11px] uppercase tracking-widest opacity-50 mb-1">PROCEED TO CHECKOUT</div>
                <div className="text-sm">Pay securely from your mobile device.</div>
             </div>
             <button onClick={handlePay} disabled={actionLoading} className={`w-full py-4 rounded-xl font-bold text-lg transition-transform hover:-translate-y-0.5 ${isDark ? 'bg-amber text-[#0D0B08]' : 'bg-lightAmber text-white'} ${actionLoading ? 'opacity-50' : ''}`}>
                {actionLoading ? 'PROCESSING...' : 'CONTINUE TO PAYMENT'}
             </button>
             {paymentError && <div className="text-red text-xs mt-4 text-center font-medium">{paymentError}</div>}
          </div>
        ) : (
          <div className={`${cardCls} border-l-4 ${isDark ? 'border-l-green' : 'border-l-lightGreen'} text-center py-8`}>
             <div className={`text-xl font-extrabold tracking-tight mb-2 ${isDark ? 'text-green' : 'text-lightGreen'}`}>PAYMENT SUCCESSFUL</div>
             <div className="text-2xl font-bold my-2">{fmtInr(data.total_negotiated_price_inr)} PAID</div>
             <div className="text-xs opacity-70">Razorpay Status: {paymentStatus?.status}</div>
          </div>
        )}

      </div>
    );
  }

  if (data?.merchant_auth === 'DECLINED') {
    return (
      <div className={`min-h-screen p-6 flex flex-col items-center justify-center ${bg}`}>
        <div className={`text-4xl font-bold mb-4 text-red`}>✕</div>
        <div className={`text-xl font-extrabold tracking-tight mb-2 text-red`}>MERCHANT DECLINED</div>
        <div className={`text-sm text-center opacity-70`}>Transaction was rejected.</div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen p-6 flex flex-col ${bg}`}>
      <div className="mb-8">
        <h1 className={`text-2xl font-extrabold tracking-tight ${isDark ? 'text-darkText1' : 'text-lightText1'}`}>A.M.E.</h1>
        <h2 className="text-xs uppercase tracking-widest opacity-60 font-bold mt-1">Merchant Authorization</h2>
      </div>

      <div className={`${cardCls} border-l-4 ${isDark ? 'border-l-amber' : 'border-l-lightAmber'}`}>
        <div className={hdrCls}>TRANSACTION READY FOR APPROVAL</div>
        
        <Row k="PRODUCT" v={`${data.requested_quantity} × ${data.sku}`} />
        <Row k="UNIT PRICE" v={fmtInr(data.negotiated_unit_price)} />
        <Row k="DISCOUNT" v={fmtPct(data.requested_discount_pct)} />
        
        <div className="my-3 border-t border-dashed opacity-20"></div>
        <div className="flex justify-between items-end py-2">
          <span className={`text-[11px] font-bold tracking-wider uppercase opacity-70`}>TRANSACTION VALUE</span>
          <span className="text-3xl font-extrabold">{fmtInr(data.total_negotiated_price_inr)}</span>
        </div>
      </div>

      <div className={cardCls}>
        <div className={hdrCls}>POLICY CHECK</div>
        <Row k="MAX DISCOUNT ALLOWED" v="10%" />
        <Row k="STATUS" v="✓ WITHIN POLICY" success />
      </div>

      <div className="mt-auto flex flex-col gap-3">
        <button 
          onClick={() => handleAction('APPROVE')}
          disabled={actionLoading}
          className={`w-full py-4 rounded-xl font-bold text-lg transition-transform hover:-translate-y-0.5 ${isDark ? 'bg-amber text-[#0D0B08]' : 'bg-lightAmber text-white'} ${actionLoading ? 'opacity-50' : ''}`}
        >
          {actionLoading ? 'PROCESSING...' : 'APPROVE TRANSACTION'}
        </button>
        
        <button 
          onClick={() => handleAction('REJECT')}
          disabled={actionLoading}
          className={`w-full py-3 text-sm rounded-xl font-bold border transition-transform hover:-translate-y-0.5 ${isDark ? 'border-darkBorder hover:bg-darkSurfaceEl text-darkText1' : 'border-lightBorder hover:bg-lightSurfaceEl text-lightText1'} ${actionLoading ? 'opacity-50' : ''}`}
        >
          REJECT
        </button>
      </div>
    </div>
  );
}
