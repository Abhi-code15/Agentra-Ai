import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import AIChatDrawer from './AIChatDrawer';
import {
  FileText,
  LayoutDashboard,
  CheckSquare,
  ShieldCheck,
  LogOut,
  User as UserIcon,
  Sparkles,
  Search,
  Activity,
  Bot,
  ExternalLink,
} from 'lucide-react';

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isChatOpen, setIsChatOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const isReviewer = user?.role === 'REVIEWER' || user?.role === 'ADMIN';

  const navItems = [
    { name: 'Dashboard', to: '/', icon: LayoutDashboard },
    { name: 'Documents', to: '/documents', icon: FileText },
    ...(isReviewer
      ? [
          { name: 'Review Queue', to: '/reviews', icon: CheckSquare },
          { name: 'Audit Ledger', to: '/audit', icon: ShieldCheck },
        ]
      : []),
  ];

  // Helper for page title
  const getPageTitle = () => {
    const path = location.pathname;
    if (path === '/') return 'Governance Overview';
    if (path.startsWith('/documents')) return 'Document Repository';
    if (path.startsWith('/analyses')) return 'Agent Analysis Telemetry';
    if (path.startsWith('/reviews')) return 'Human-in-the-Loop Review';
    if (path.startsWith('/audit')) return 'Immutable Audit Ledger';
    return 'Enterprise Governance';
  };

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden font-sans">
      {/* Sleek Enterprise Sidebar */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between flex-shrink-0 z-20">
        <div>
          {/* Brand Header */}
          <div className="h-16 flex items-center justify-between px-6 border-b border-slate-800/80">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-sm shadow-sm">
                A
              </div>
              <div>
                <span className="text-base font-bold tracking-tight text-white block leading-tight">
                  Agentra
                </span>
                <span className="text-[10px] font-medium text-slate-400 block tracking-wider uppercase">
                  AI Governance
                </span>
              </div>
            </div>

            <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              v1.0
            </span>
          </div>

          {/* Navigation Links */}
          <div className="px-3 py-4">
            <div className="px-3 mb-2">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                Workspace
              </span>
            </div>
            <nav className="space-y-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.to === '/'}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                        isActive
                          ? 'bg-indigo-600 text-white font-semibold shadow-sm'
                          : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                      }`
                    }
                  >
                    <Icon className="w-4 h-4" />
                    {item.name}
                  </NavLink>
                );
              })}
            </nav>

            {/* Quick AI Trigger */}
            <div className="mt-6 pt-4 border-t border-slate-800/80">
              <div className="px-3 mb-2">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                  AI Copilot
                </span>
              </div>
              <button
                onClick={() => setIsChatOpen(true)}
                className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium text-indigo-300 bg-indigo-950/40 hover:bg-indigo-900/40 border border-indigo-800/40 transition-colors group"
              >
                <span className="flex items-center gap-2.5">
                  <Sparkles className="w-4 h-4 text-indigo-400 group-hover:rotate-12 transition-transform" />
                  Ask Agentra AI
                </span>
                <span className="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-indigo-500/20 text-indigo-300">
                  Chat
                </span>
              </button>
            </div>
          </div>
        </div>

        {/* User Card & Logout */}
        <div className="p-3 border-t border-slate-800/80 bg-slate-900/50">
          <div className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-slate-800/50 mb-2">
            <div className="w-7 h-7 rounded-full bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 font-semibold text-xs">
              {user?.full_name ? user.full_name[0].toUpperCase() : 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-slate-200 truncate">{user?.full_name}</p>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                <span className="text-[10px] font-medium text-slate-400 uppercase tracking-wider">
                  {user?.role}
                </span>
              </div>
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-rose-400 hover:bg-rose-950/20 transition-colors"
          >
            <LogOut className="w-3.5 h-3.5" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header Bar */}
        <header className="h-16 bg-white border-b border-slate-200 px-8 flex items-center justify-between flex-shrink-0 z-10">
          <div className="flex items-center gap-3">
            <h1 className="text-sm font-semibold text-slate-900">{getPageTitle()}</h1>
            <span className="text-slate-300">•</span>
            <div className="flex items-center gap-1.5 text-xs text-slate-500">
              <Activity className="w-3.5 h-3.5 text-emerald-600" />
              <span>Engine Status: <strong className="text-slate-700 font-medium">Ready</strong></span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsChatOpen(true)}
              className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium bg-slate-100 hover:bg-indigo-50 hover:text-indigo-700 border border-slate-200/80 text-slate-700 transition-colors shadow-sm"
            >
              <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
              <span>Ask AI Chatbot</span>
            </button>

            <div className="h-4 w-px bg-slate-200"></div>

            <div className="text-right">
              <span className="text-xs font-medium text-slate-800 block leading-tight">
                {user?.full_name}
              </span>
              <span className="text-[10px] text-slate-400 block">{user?.email}</span>
            </div>
          </div>
        </header>

        {/* Scrollable Main Viewport */}
        <main className="flex-1 overflow-y-auto p-8 bg-slate-50/60">
          <Outlet context={{ openChatWithDoc: (docId, title) => setIsChatOpen(true) }} />
        </main>
      </div>

      {/* Floating Global Chat Pill (Bottom Right) */}
      {!isChatOpen && (
        <button
          onClick={() => setIsChatOpen(true)}
          className="fixed bottom-6 right-6 z-40 flex items-center gap-2.5 px-4 py-2.5 rounded-full bg-slate-900 text-white text-xs font-medium shadow-xl hover:bg-indigo-600 hover:scale-105 active:scale-95 transition-all border border-slate-800 group"
        >
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></div>
          <Sparkles className="w-4 h-4 text-indigo-400 group-hover:text-white transition-colors" />
          <span>Ask Agentra AI</span>
        </button>
      )}

      {/* Global AI Chat Drawer */}
      <AIChatDrawer isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
    </div>
  );
}
