import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';
import { Play, ShieldAlert, TrendingUp } from 'lucide-react';

export default function Demo() {
  const { theme } = useTheme();
  const navigate = useNavigate();
  const isDark = theme === 'dark';
  
  const scenarios = [
    {
      title: "SCENARIO 1: BUY",
      description: "Demonstrates a successful autonomous transaction that passes policy constraints, gets merchant authorization, and results in realized revenue.",
      query: "Find me 5 Pro Licenses under 9500 and buy them.",
      icon: Play,
      color: isDark ? "text-green" : "text-lightGreen",
      bg: isDark ? "bg-greenSoft" : "bg-lightGreenSoft"
    },
    {
      title: "SCENARIO 2: GOVERN",
      description: "Demonstrates strict agentic governance. The buyer demands a discount that exceeds the merchant's 10% maximum limit, resulting in an automatic policy rejection.",
      query: "I need 10 Pro Licenses with a 25% discount.",
      icon: ShieldAlert,
      color: "text-red",
      bg: isDark ? "bg-redSoft" : "bg-lightRedSoft"
    },
    {
      title: "SCENARIO 3: GROW",
      description: "Demonstrates agentic cross-selling. After a successful transaction, the merchant agent automatically identifies and proposes a complementary product as a 'Next Revenue Opportunity'.",
      query: "I want 2 API Credentials at a 5% discount.",
      icon: TrendingUp,
      color: isDark ? "text-amber" : "text-lightAmber",
      bg: isDark ? "bg-amberSoft" : "bg-lightAmberSoft"
    }
  ];

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-8">
        <h2 className="text-[1.7rem] font-extrabold mb-1 tracking-tight">A.M.E. // DEMO SCENARIOS</h2>
        <p className={`text-sm ${isDark ? 'text-darkText2' : 'text-lightText2'}`}>
          Select a scenario below to launch the Buyer Agent with a pre-configured prompt. These scenarios run against the real backend and demonstrate live agentic commerce behavior.
        </p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {scenarios.map((s, i) => {
          const Icon = s.icon;
          return (
            <div 
              key={i} 
              onClick={() => navigate(`/buyer?q=${encodeURIComponent(s.query)}`)}
              className={`rounded-2xl border p-6 flex flex-col cursor-pointer transition-transform hover:-translate-y-1 hover:shadow-lg ${isDark ? 'bg-darkSurface border-darkBorder' : 'bg-lightSurface border-lightBorder'}`}
            >
              <div className={`w-12 h-12 rounded-full flex items-center justify-center mb-6 ${s.bg} ${s.color}`}>
                <Icon size={24} />
              </div>
              <h3 className="font-extrabold text-lg mb-2">{s.title}</h3>
              <p className={`text-sm mb-6 flex-grow ${isDark ? 'text-darkText2' : 'text-lightText2'}`}>
                {s.description}
              </p>
              
              <div className={`p-4 rounded-xl font-mono text-[11px] mb-4 border ${isDark ? 'bg-darkBg border-darkBorder' : 'bg-lightBg border-lightBorder'}`}>
                "{s.query}"
              </div>
              
              <div className="mt-auto pt-4 border-t border-dashed opacity-50 text-[10px] uppercase font-bold tracking-widest text-center">
                Launch Scenario &rarr;
              </div>
            </div>
          )
        })}
      </div>
      
      <div className={`mt-10 p-6 rounded-2xl border text-sm text-center ${isDark ? 'bg-darkSurfaceEl border-darkBorder text-darkText2' : 'bg-lightSurfaceEl border-lightBorder text-lightText2'}`}>
        <p className="font-medium mb-1">Testing with Real Payment Gateway</p>
        <p className="opacity-70 text-xs">
          For scenarios resulting in a successful deal, you will be able to complete the transaction using the actual Razorpay Test Mode checkout. No real cards will be charged.
        </p>
      </div>
    </div>
  );
}
