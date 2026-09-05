import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '../context/ThemeContext';
import { getTransactions } from '../api/client';
import { fmtInr, fmtPct } from '../utils/format';

export default function CommandCenter() {
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

  const paidTxs = txs.filter(t => t.status === 'PAID');
  const gmv = paidTxs.reduce((sum, t) => sum + (t.total_negotiated_price_inr || 0), 0);
  const nOrders = paidTxs.length;
  const aov = nOrders > 0 ? gmv / nOrders : 0;
  const units = paidTxs.reduce((sum, t) => sum + (t.requested_quantity || 0), 0);
  const avgDisc = paidTxs.length ? paidTxs.reduce((sum, t) => sum + (t.requested_discount_pct || 0), 0) / paidTxs.length : 0;
  
  const req = txs.length;
  const neg = txs.filter(t => ['ACCEPTED', 'COUNTER_OFFER', 'PAID'].includes(t.status)).length;
  const auth = txs.filter(t => ['APPROVED', 'DECLINED'].includes(t.merchant_auth) || t.status === 'PAID').length;
  const desktopAuth = txs.filter(t => t.auth_device === 'Desktop').length;
  const phoneAuth = txs.filter(t => t.auth_device === 'Phone').length;
 

  const xsVal = paidTxs.reduce((sum, t) => t.sku === 'SaaS-PRO-1M' ? sum + 4750 : sum, 0);

  const cardCls = `rounded-2xl border p-6 shadow-sm transition-transform hover:-translate-y-1 ${
    isDark ? 'bg-darkSurface border-darkBorder hover:shadow-black/40' : 'bg-lightSurface border-lightBorder hover:shadow-black/5'
  }`;
  const hdrCls = `text-[11px] font-bold tracking-wider uppercase mb-3 ${isDark ? 'text-darkText3' : 'text-lightText3'}`;
  const kpiValCls = `text-3xl font-extrabold leading-tight mb-1`;
  const kpiSubCls = `text-xs ${isDark ? 'text-darkText2' : 'text-lightText2'}`;

  const Arrow = () => <div className={isDark ? 'text-darkText3' : 'text-lightText3'}>&rarr;</div>;
  const Chip = ({ children, active, success, amber }) => {
    let bg = isDark ? 'bg-darkSurfaceEl border-darkBorder' : 'bg-lightSurfaceEl border-lightBorder';
    let text = isDark ? 'text-darkText2' : 'text-lightText2';
    if (success) {
      bg = isDark ? 'bg-greenSoft border-green' : 'bg-lightGreenSoft border-lightGreen';
      text = isDark ? 'text-green' : 'text-lightGreen';
    } else if (amber) {
      bg = isDark ? 'bg-amberSoft border-amber' : 'bg-lightAmberSoft border-lightAmber';
      text = isDark ? 'text-amber' : 'text-lightAmber';
    }
    return <div className={`px-4 py-2 rounded-lg border text-sm font-semibold ${bg} ${text}`}>{children}</div>;
  };

  if (loading) return <div className="text-sm opacity-50">Fetching merchant data...</div>;

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
      <h2 className="text-[1.7rem] font-extrabold mb-1">COMMAND CENTER</h2>
      <p className={`text-sm mb-6 ${isDark ? 'text-darkText2' : 'text-lightText2'}`}>Agentic commerce performance at a glance.</p>

      {/* REVENUE HERO */}
      <div className={`rounded-2xl border p-8 mb-6 shadow-md border-l-4 ${isDark ? 'border-l-amber bg-gradient-to-br from-darkSurface to-darkSurfaceEl border-darkBorder' : 'border-l-lightAmber bg-gradient-to-br from-[#FFFCF5] to-[#FFF8EB] border-lightBorder'}`}>
        <div className={hdrCls}>REVENUE GENERATED</div>
        <div className={`text-4xl md:text-6xl font-extrabold mb-2 break-all ${isDark ? 'text-green' : 'text-lightGreen'}`}>{fmtInr(gmv)}</div>
        <div className={`text-base font-medium mb-8 ${isDark ? 'text-darkText2' : 'text-lightText2'}`}>
          {nOrders} paid transaction{nOrders !== 1 ? 's' : ''} &middot; {units} units &middot; {fmtPct(avgDisc)} avg negotiated discount
        </div>

        <div className={hdrCls}>HOW A.M.E. GENERATED THIS REVENUE</div>
        <div className="flex items-center gap-2 flex-wrap mt-2 mb-4">
          <Chip>Buyer intent</Chip><Arrow/><Chip>Product match</Chip><Arrow/><Chip>Policy validation</Chip><Arrow/>
          <Chip>Negotiation</Chip><Arrow/><Chip amber>Merchant approval</Chip><Arrow/><Chip>Razorpay</Chip><Arrow/><Chip success>Paid</Chip>
        </div>
        <div className={`flex gap-4 text-xs font-medium opacity-70`}>
          <div>💻 Desktop authorized: {desktopAuth}</div>
          <div>📱 Phone authorized: {phoneAuth}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className={cardCls}><div className={hdrCls}>COMPLETED ORDERS</div><div className={kpiValCls}>{nOrders}</div><div className={kpiSubCls}>Paid transactions</div></div>
        <div className={cardCls}><div className={hdrCls}>UNITS SOLD</div><div className={kpiValCls}>{units}</div><div className={kpiSubCls}>Total volume</div></div>
        <div className={cardCls}><div className={hdrCls}>AVG ORDER VALUE</div><div className={kpiValCls}>{fmtInr(aov)}</div><div className={kpiSubCls}>Per transaction</div></div>
        <div className={cardCls}><div className={hdrCls}>AVG DISCOUNT</div><div className={kpiValCls}>{fmtPct(avgDisc)}</div><div className={kpiSubCls}>Negotiated savings</div></div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        <div className={`col-span-2 ${cardCls}`}>
          <div className={hdrCls}>AGENT COMMERCE FUNNEL</div>
          <div className="flex flex-wrap md:flex-nowrap gap-2 text-center items-center mt-4">
             {[
               {l: 'REQUESTED', v: req},
               {l: 'VALIDATED', v: req},
               {l: 'NEGOTIATED', v: neg},
               {l: 'AUTHORIZED', v: auth, amber: true},
               {l: 'PAID', v: nOrders, green: true},
             ].map((s, i, arr) => (
               <React.Fragment key={s.l}>
                 <div className={`flex-auto w-full md:w-auto md:flex-1 p-3 rounded-xl border ${isDark ? 'bg-darkSurfaceEl border-darkBorder' : 'bg-lightSurfaceEl border-lightBorder'} ${s.green ? (isDark ? '!border-green' : '!border-lightGreen') : s.amber ? (isDark ? '!border-amber' : '!border-lightAmber') : ''}`}>
                    <div className={`text-2xl font-extrabold ${s.green ? (isDark?'text-green':'text-lightGreen') : s.amber ? (isDark?'text-amber':'text-lightAmber') : ''}`}>{s.v}</div>
                    <div className="text-[10px] font-bold mt-1 text-gray-500 uppercase">{s.l}</div>
                 </div>
                 {i < arr.length - 1 && <Arrow />}
               </React.Fragment>
             ))}
          </div>
        </div>
        
        <div className={cardCls}>
          <div className={hdrCls}>MERCHANT GROWTH</div>
          <div className="mb-4">
            <div className={hdrCls}>REALIZED GMV</div>
            <div className={`text-2xl font-extrabold ${isDark ? 'text-green' : 'text-lightGreen'}`}>{fmtInr(gmv)}</div>
            <div className={kpiSubCls}>Actual revenue generated</div>
          </div>
          <hr className={`my-3 border-t ${isDark ? 'border-darkBorder' : 'border-lightBorder'}`} />
          <div>
            <div className={hdrCls}>NEXT REVENUE OPPORTUNITY</div>
            <div className="text-xl font-bold mb-1">+{fmtInr(xsVal)} potential</div>
            <div className={`text-xs font-semibold px-2 py-1 inline-block rounded-full border ${isDark ? 'bg-amberSoft text-amber border-amber' : 'bg-lightAmberSoft text-lightAmber border-lightAmber'}`}>OFFERED — NOT PURCHASED</div>
          </div>
        </div>
      </div>

    </motion.div>
  );
}
