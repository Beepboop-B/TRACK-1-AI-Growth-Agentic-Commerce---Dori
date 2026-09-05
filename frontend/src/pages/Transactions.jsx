import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '../context/ThemeContext';
import { getTransactions } from '../api/client';
import { fmtInr } from '../utils/format';

export default function Transactions() {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const [txs, setTxs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getTransactions().then(data => {
      setTxs(Array.isArray(data) ? data : []);
      setLoading(false);
    }).catch(console.error);
  }, []);

  if (loading) return <div className="text-sm opacity-50">Fetching transactions...</div>;

  const cardCls = `rounded-2xl border p-6 shadow-sm ${
    isDark ? 'bg-darkSurface border-darkBorder' : 'bg-lightSurface border-lightBorder'
  }`;
  
  const thCls = `text-left px-3 py-3 text-[11px] font-bold tracking-wider uppercase border-b-2 ${
    isDark ? 'text-darkText3 border-darkBorder' : 'text-lightText3 border-lightBorder'
  }`;
  const tdCls = `px-3 py-3 border-b text-sm ${
    isDark ? 'border-darkBorder' : 'border-lightBorder'
  }`;

  const Pill = ({ status, merchant_auth, type }) => {
    let s = status;
    if (type === 'auth') {
      if (merchant_auth === 'APPROVED') s = 'APPROVED';
      else if (merchant_auth === 'DECLINED' || status === 'REJECTED') s = 'DECLINED';
      else if (status === 'PAID') s = 'APPROVED';
      else s = 'PENDING';
    } else if (type === 'pay') {
      s = ['PAID', 'FAILED'].includes(status) ? status : 'PENDING';
    }
    
    let colors = isDark ? 'bg-amberSoft text-amber' : 'bg-lightAmberSoft text-lightAmber';
    if (s === 'APPROVED' || s === 'PAID') colors = isDark ? 'bg-greenSoft text-green' : 'bg-lightGreenSoft text-lightGreen';
    if (s === 'DECLINED' || s === 'FAILED') colors = isDark ? 'bg-redSoft text-red' : 'bg-lightRedSoft text-lightRed';
    
    return <span className={`px-3 py-1 rounded-full text-[10px] font-bold tracking-wider ${colors}`}>{s}</span>;
  };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
      <h2 className="text-[1.7rem] font-extrabold mb-1">TRANSACTION HISTORY</h2>
      <p className={`text-sm mb-6 ${isDark ? 'text-darkText2' : 'text-lightText2'}`}>Every autonomous commerce event recorded by A.M.E.</p>

      {txs.length === 0 ? (
        <div className={`p-10 rounded-2xl border text-center ${cardCls}`}>
          <div className="font-medium mb-2">NO COMPLETED TRANSACTIONS YET</div>
          <div className="text-sm opacity-60">Run the Buyer Agent to create your first autonomous commerce transaction.</div>
        </div>
      ) : (
        <div className={cardCls + " !p-0 overflow-x-auto"}>
          <div className="md:hidden">
              {[...txs].reverse().map((t, i) => (
                <div key={i} className={`p-4 border-b last:border-b-0 ${isDark ? 'border-darkBorder' : 'border-lightBorder'}`}>
                  <div className="flex justify-between items-start mb-2">
                    <div className={`font-mono text-xs ${isDark ? 'text-darkText1' : 'text-lightText1'}`}>{t.sku || '--'}</div>
                    <div className="font-bold">{fmtInr(t.total_negotiated_price_inr)}</div>
                  </div>
                  <div className={`text-[10px] mb-3 ${isDark ? 'text-darkText3' : 'text-lightText3'}`}>
                    Qty: {t.requested_quantity || '--'} &middot; {t.timestamp?.substring(0, 19).replace('T', ' ') || '--'}
                  </div>
                  <div className="flex gap-2">
                    <Pill status={t.status} merchant_auth={t.merchant_auth} type="auth"/>
                    <Pill status={t.status} type="pay"/>
                  </div>
                  <div className={`text-[9px] font-mono mt-3 opacity-40 break-all`}>
                    Order: {t.razorpay_order_id || '--'}
                  </div>
                </div>
              ))}
            </div>
            <table className="hidden md:table w-full border-collapse">
            <thead>
              <tr>
                <th className={thCls}>Timestamp</th>
                <th className={thCls}>SKU</th>
                <th className={thCls}>Qty</th>
                <th className={thCls}>Total</th>
                <th className={thCls}>Authorization</th>
                <th className={thCls}>Payment</th>
                <th className={thCls}>Razorpay Order</th>
              </tr>
            </thead>
            <tbody>
              {[...txs].reverse().map((t, i) => (
                <tr key={i} className={`transition-colors ${isDark ? 'hover:bg-darkSurfaceEl' : 'hover:bg-lightSurfaceEl'}`}>
                  <td className={`${tdCls} font-mono text-[11px]`}>{t.timestamp?.substring(0, 19).replace('T', ' ') || '—'}</td>
                  <td className={`${tdCls} font-mono text-[12px]`}>{t.sku || '—'}</td>
                  <td className={tdCls}>{t.requested_quantity || '—'}</td>
                  <td className={`${tdCls} font-bold`}>{fmtInr(t.total_negotiated_price_inr)}</td>
                  <td className={tdCls}><Pill status={t.status} merchant_auth={t.merchant_auth} type="auth"/></td>
                  <td className={tdCls}><Pill status={t.status} type="pay"/></td>
                  <td className={`${tdCls} font-mono text-[11px]`}>{t.razorpay_order_id || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </motion.div>
  );
}
