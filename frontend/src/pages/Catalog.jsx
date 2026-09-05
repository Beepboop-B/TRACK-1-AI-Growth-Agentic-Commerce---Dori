import React, { useState, useEffect } from 'react';
import { useTheme } from '../context/ThemeContext';
import { getCatalog } from '../api/client';
import { fmtInr, fmtPct } from '../utils/format';

export default function Catalog() {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const [catalog, setCatalog] = useState([]);

  useEffect(() => {
    getCatalog().then(setCatalog).catch(console.error);
  }, []);

  return (
    <div className="max-w-4xl mx-auto py-8">
      <h1 className={`text-2xl font-extrabold mb-8 ${isDark ? 'text-darkText1' : 'text-lightText1'}`}>
        Merchant Catalog
      </h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {catalog.map(product => (
          <div key={product.sku} className={`p-6 rounded-xl border flex flex-col ${isDark ? 'bg-darkSurface border-darkBorder' : 'bg-lightSurface border-lightBorder'}`}>
            <div className={`text-[10px] font-bold tracking-widest uppercase mb-2 ${isDark ? 'text-amber' : 'text-lightAmber'}`}>
              {product.sku}
            </div>
            <h3 className={`text-lg font-bold mb-4 ${isDark ? 'text-darkText1' : 'text-lightText1'}`}>
              {product.name}
            </h3>
            
            <div className="space-y-3 text-sm flex-1">
              <div className="flex justify-between border-b pb-2 opacity-80 border-dashed">
                <span>Base Price</span>
                <span className="font-bold">{fmtInr(product.base_price_inr)}</span>
              </div>
              <div className="flex justify-between border-b pb-2 opacity-80 border-dashed">
                <span>Available Stock</span>
                <span className="font-bold">{product.stock}</span>
              </div>
              <div className="flex justify-between opacity-80 border-dashed">
                <span>Max Discount</span>
                <span className="font-bold">{fmtPct(product.max_discount_pct)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
