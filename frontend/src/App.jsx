import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import AppShell from './components/AppShell';
import CommandCenter from './pages/CommandCenter';
import BuyerAgent from './pages/BuyerAgent';
import Transactions from './pages/Transactions';
import Demo from './pages/Demo';
import PhoneApproval from './pages/PhoneApproval';

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppShell />}>
            <Route index element={<CommandCenter />} />
            <Route path="buyer" element={<BuyerAgent />} />
            <Route path="transactions" element={<Transactions />} />
            <Route path="demo" element={<Demo />} />
          </Route>
          <Route path="/approval/:token" element={<PhoneApproval />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}
