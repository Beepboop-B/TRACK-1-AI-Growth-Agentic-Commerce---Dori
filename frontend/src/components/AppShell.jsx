import React, { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';
import { Moon, Sun, LayoutDashboard, ShoppingCart, List, Play, Menu, X } from 'lucide-react';

const NavItem = ({ to, icon: Icon, label, collapsed, onClick }) => {
  const { theme } = useTheme();
  return (
    <NavLink
      to={to}
      onClick={onClick}
      className={({ isActive }) => `flex items-center gap-3 px-3 py-2.5 mb-1 rounded-lg transition-colors ${
        isActive 
          ? (theme === 'dark' ? 'bg-amberSoft text-amber font-bold' : 'bg-lightAmberSoft text-lightAmber font-bold') 
          : (theme === 'dark' ? 'text-darkText2 hover:bg-darkSurfaceEl' : 'text-lightText2 hover:bg-lightSurfaceEl')
      }`}
    >
      <Icon size={18} />
      {!collapsed && <span>{label}</span>}
    </NavLink>
  );
};

export default function AppShell() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { theme, toggleTheme } = useTheme();

  const isDark = theme === 'dark';
  const surfaceClass = isDark ? 'bg-darkSurface border-darkBorder' : 'bg-lightSurface border-lightBorder';
  const t2Class = isDark ? 'text-darkText2' : 'text-lightText2';
  const t1Class = isDark ? 'text-darkText1' : 'text-lightText1';

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Desktop Sidebar */}
      <aside className={`hidden md:flex border-r transition-all duration-300 flex-col z-20 relative ${surfaceClass} ${collapsed ? 'w-16' : 'w-64'}`}>
        <div className="p-4 flex items-center justify-between">
          {!collapsed && (
            <div>
              <h2 className={`font-extrabold text-xl tracking-tight ${t1Class}`}>A.M.E.</h2>
              <p className={`text-[10px] uppercase tracking-wider ${t2Class}`}>Agentic Merchant Engine</p>
            </div>
          )}
          <button onClick={() => setCollapsed(!collapsed)} className={`p-1 rounded hover:bg-black/10 dark:hover:bg-white/10 ${t2Class}`}>
            <Menu size={20} />
          </button>
        </div>
        <hr className={`border-t ${isDark ? 'border-darkBorder' : 'border-lightBorder'} mb-4`} />
        <nav className="flex-1 px-3">
          <NavItem to="/" icon={LayoutDashboard} label="Command Center" collapsed={collapsed} />
          <NavItem to="/buyer" icon={ShoppingCart} label="Buyer Agent" collapsed={collapsed} />
          <NavItem to="/transactions" icon={List} label="Transactions" collapsed={collapsed} />
          <NavItem to="/demo" icon={Play} label="Demo" collapsed={collapsed} />
        </nav>
        <div className={`p-4 text-xs font-semibold ${t2Class} text-center`}>
          {!collapsed && 'Powered by Razorpay'}
        </div>
      </aside>

      {/* Mobile Drawer Overlay */}
      {mobileMenuOpen && (
        <div className="md:hidden fixed inset-0 z-40 bg-black/50 backdrop-blur-sm" onClick={() => setMobileMenuOpen(false)} />
      )}

      {/* Mobile Drawer */}
      <aside className={`md:hidden fixed inset-y-0 left-0 z-50 w-64 transform transition-transform duration-300 flex flex-col ${surfaceClass} ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="p-4 flex items-center justify-between">
          <div>
            <h2 className={`font-extrabold text-xl tracking-tight ${t1Class}`}>A.M.E.</h2>
            <p className={`text-[10px] uppercase tracking-wider ${t2Class}`}>Agentic Merchant Engine</p>
          </div>
          <button onClick={() => setMobileMenuOpen(false)} className={`p-1 rounded hover:bg-black/10 dark:hover:bg-white/10 ${t2Class}`}>
            <X size={20} />
          </button>
        </div>
        <hr className={`border-t ${isDark ? 'border-darkBorder' : 'border-lightBorder'} mb-4`} />
        <nav className="flex-1 px-3">
          <NavItem to="/" icon={LayoutDashboard} label="Command Center" onClick={() => setMobileMenuOpen(false)} />
          <NavItem to="/buyer" icon={ShoppingCart} label="Buyer Agent" onClick={() => setMobileMenuOpen(false)} />
          <NavItem to="/transactions" icon={List} label="Transactions" onClick={() => setMobileMenuOpen(false)} />
          <NavItem to="/demo" icon={Play} label="Demo" onClick={() => setMobileMenuOpen(false)} />
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col h-full overflow-hidden relative z-0">
        {/* TopBar */}
        <header className="px-4 md:px-8 py-4 md:py-6 flex justify-between items-center shrink-0">
          <div className="flex items-center gap-3">
            <button onClick={() => setMobileMenuOpen(true)} className={`md:hidden p-2 -ml-2 rounded hover:bg-black/10 dark:hover:bg-white/10 ${t1Class}`}>
              <Menu size={24} />
            </button>
            <div>
              <h1 className={`text-lg md:text-[1.7rem] font-extrabold tracking-tight ${t1Class}`}>A.M.E.</h1>
              <p className={`text-[10px] md:text-sm hidden sm:block ${t2Class}`}>Autonomous commerce infrastructure for AI buyers and merchants.</p>
            </div>
          </div>
          <button 
            onClick={toggleTheme}
            className={`flex items-center gap-2 px-3 py-1.5 md:px-4 md:py-2 rounded-lg font-bold border transition-colors text-xs md:text-sm ${
              isDark ? 'border-darkBorder bg-darkSurfaceEl hover:bg-darkSurface text-darkText1' : 'border-lightBorder bg-lightSurfaceEl hover:bg-lightSurface text-lightText1'
            }`}
          >
            {isDark ? <Sun size={16}/> : <Moon size={16}/>}
            <span className="hidden sm:inline">{isDark ? 'Light' : 'Dark'}</span>
          </button>
        </header>

        {/* Page Content */}
        <div className="flex-1 overflow-y-auto px-4 md:px-8 pb-12">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
