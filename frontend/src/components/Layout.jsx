import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import AIChatDrawer from './AIChatDrawer';
import {
  LayoutDashboard,
  CheckSquare,
  ShieldCheck,
  LogOut,
  Sparkles,
  BookOpen,
  Receipt,
  PlusCircle,
  HelpCircle,
  FolderOpen,
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

  // Role-specific intuitive navigation
  const navItems = isReviewer
    ? [
        { name: 'Dashboard', to: '/', icon: LayoutDashboard },
        { name: 'Review Queue', to: '/reviews', icon: CheckSquare },
        { name: 'All Reimbursements', to: '/claims', icon: Receipt },
        { name: 'Company Policies', to: '/policies', icon: BookOpen },
        { name: 'Policy Documents', to: '/documents', icon: FolderOpen },
        { name: 'Activity History', to: '/audit', icon: ShieldCheck },
      ]
    : [
        { name: 'Dashboard', to: '/', icon: LayoutDashboard },
        { name: 'New Reimbursement', to: '/claims/new', icon: PlusCircle },
        { name: 'My Reimbursements', to: '/claims', icon: Receipt },
        { name: 'Company Policies', to: '/policies', icon: BookOpen },
      ];

  // Simple, familiar page titles
  const getPageTitle = () => {
    const path = location.pathname;
    if (path === '/') return isReviewer ? 'Reviewer Overview' : 'My Reimbursements';
    if (path === '/claims/new') return 'Submit New Reimbursement';
    if (path.startsWith('/claims/')) return 'Reimbursement Details & Voucher';
    if (path === '/claims') return isReviewer ? 'All Employee Reimbursements' : 'My Reimbursements';
    if (path.startsWith('/policies')) return 'Company Policies & Standards';
    if (path.startsWith('/documents')) return 'Policy Document Repository';
    if (path.startsWith('/reviews')) return 'Review Queue';
    if (path.startsWith('/audit')) return 'Activity History';
    return 'Agentra';
  };

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden font-sans">
      {/* Clean Enterprise Sidebar */}
      <aside className="w-60 bg-slate-900 border-r border-slate-800 flex flex-col justify-between flex-shrink-0 z-20">
        <div>
          {/* Brand Header */}
          <div className="h-14 flex items-center justify-between px-5 border-b border-slate-800">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-xs shadow-xs">
                A
              </div>
              <div>
                <span className="text-sm font-bold tracking-tight text-white block leading-tight">
                  Agentra
                </span>
                <span className="text-[10px] font-medium text-slate-400 block tracking-wider uppercase">
                  {isReviewer ? 'Reviewer Portal' : 'Employee Portal'}
                </span>
              </div>
            </div>
          </div>

          {/* Navigation Links */}
          <div className="px-3 py-4">
            <div className="px-3 mb-2">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                Menu
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
                      `flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                        isActive
                          ? 'bg-indigo-600 text-white font-semibold shadow-xs'
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

            {/* Single Clean AI Assistant Entry */}
            <div className="mt-6 pt-4 border-t border-slate-800">
              <button
                onClick={() => setIsChatOpen(true)}
                className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium text-indigo-300 bg-indigo-950/40 hover:bg-indigo-900/40 border border-indigo-800/40 transition-colors"
              >
                <span className="flex items-center gap-2">
                  <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                  Ask AI Assistant
                </span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-semibold">
                  Help
                </span>
              </button>
            </div>
          </div>
        </div>

        {/* User Profile Card & Sign Out */}
        <div className="p-3 border-t border-slate-800 bg-slate-900/60">
          <div className="flex items-center gap-2.5 px-3 py-2 rounded-lg bg-slate-800/50 mb-2">
            <div className="w-7 h-7 rounded-full bg-indigo-600/30 text-indigo-300 font-bold text-xs flex items-center justify-center">
              {user?.full_name ? user.full_name[0].toUpperCase() : 'U'}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold text-slate-200 truncate">{user?.full_name || 'User'}</p>
              <p className="text-[10px] text-slate-400 truncate capitalize">{user?.role?.toLowerCase() || 'Member'}</p>
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
        {/* Top Header */}
        <header className="h-14 bg-white border-b border-slate-200 px-6 flex items-center justify-between flex-shrink-0 z-10">
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-bold text-slate-900">{getPageTitle()}</h1>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsChatOpen(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors border border-slate-200"
            >
              <HelpCircle className="w-3.5 h-3.5 text-indigo-600" />
              <span>Questions? Ask AI</span>
            </button>

            <div className="h-4 w-px bg-slate-200"></div>

            <span className="text-xs text-slate-500 font-medium">{user?.email}</span>
          </div>
        </header>

        {/* Scrollable Main Content */}
        <main className="flex-1 overflow-y-auto p-6 bg-slate-50/70">
          <Outlet context={{ openChatWithDoc: () => setIsChatOpen(true) }} />
        </main>
      </div>

      {/* Single Dedicated AI Assistant Drawer */}
      <AIChatDrawer isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
    </div>
  );
}
