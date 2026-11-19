import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import WorkflowLoopBanner from '../components/WorkflowLoopBanner';
import {
  FileText,
  Plus,
  Search,
  ArrowRight,
  ShieldCheck,
  Clock,
  DollarSign,
  AlertCircle,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Receipt,
} from 'lucide-react';

export default function Claims() {
  const { user } = useAuth();
  const isReviewer = user?.role === 'REVIEWER' || user?.role === 'ADMIN';

  const [claims, setClaims] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [typeFilter, setTypeFilter] = useState('ALL');

  const fetchClaims = async () => {
    try {
      setLoading(true);
      const res = await api.get('/claims?page=1&page_size=50');
      setClaims(res.data.data || []);
    } catch (err) {
      console.error('Failed to load requests', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClaims();
  }, []);

  const filteredClaims = claims.filter((c) => {
    const matchesSearch =
      c.claim_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (c.employee_name && c.employee_name.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesStatus = statusFilter === 'ALL' || c.status === statusFilter;
    const matchesType = typeFilter === 'ALL' || c.claim_type === typeFilter;
    return matchesSearch && matchesStatus && matchesType;
  });

  const totalAmount = claims.reduce((sum, c) => sum + (c.total_amount || 0), 0);
  const inReviewCount = claims.filter((c) => c.status === 'IN_REVIEW').length;
  const approvedCount = claims.filter((c) => c.status === 'APPROVED').length;
  const issuesCount = claims.filter((c) => c.findings_count > 0).length;

  const getStatusBadge = (status) => {
    switch (status) {
      case 'APPROVED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Approved
          </span>
        );
      case 'REJECTED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            <XCircle className="w-3 h-3 text-rose-600" /> Rejected
          </span>
        );
      case 'IN_REVIEW':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            <Clock className="w-3 h-3 text-amber-600" /> In Review
          </span>
        );
      case 'REVISION_REQUESTED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-orange-50 text-orange-700 border border-orange-200">
            <HelpCircle className="w-3 h-3 text-orange-600" /> Changes Needed
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      {/* Visual Workflow Loop */}
      <WorkflowLoopBanner role={user?.role} activeStep={3} />

      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Receipt className="w-5 h-5 text-indigo-600" />
            {isReviewer ? 'All Employee Reimbursements' : 'My Reimbursements'}
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            {isReviewer
              ? 'Track, verify, and approve employee reimbursement claims across the organization.'
              : 'Track the status, policy checks, and approval vouchers for your reimbursement claims.'}
          </p>
        </div>

        <Link
          to="/claims/new"
          className="inline-flex items-center justify-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors flex-shrink-0"
        >
          <Plus className="w-4 h-4" />
          Submit New Reimbursement
        </Link>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
            Total Claims Value
          </span>
          <div className="text-xl font-bold text-slate-900">${totalAmount.toFixed(2)}</div>
          <span className="text-[11px] text-slate-400 mt-0.5 block">{claims.length} claims submitted</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
            In Review
          </span>
          <div className="text-xl font-bold text-amber-600">{inReviewCount}</div>
          <span className="text-[11px] text-amber-600 font-medium mt-0.5 block">Waiting for decision</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
            Approved & Paid
          </span>
          <div className="text-xl font-bold text-emerald-600">{approvedCount}</div>
          <span className="text-[11px] text-emerald-600 font-medium mt-0.5 block">Vouchers issued</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
            Rule Warnings
          </span>
          <div className="text-xl font-bold text-rose-600">{issuesCount}</div>
          <span className="text-[11px] text-rose-600 font-medium mt-0.5 block">Claims exceeding limits</span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-3 flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search request #, title, or name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 rounded-lg border border-slate-300 text-xs text-slate-800 placeholder-slate-400 focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto flex-wrap">
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-slate-500 font-medium">Category:</span>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="px-2.5 py-1.5 rounded-lg border border-slate-300 text-xs text-slate-700 bg-white focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
            >
              <option value="ALL">All Categories</option>
              <option value="EXPENSE">Expense</option>
              <option value="TRAVEL">Travel</option>
              <option value="LEAVE">Leave</option>
              <option value="PROCUREMENT">Procurement</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-xs text-slate-500 font-medium">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-2.5 py-1.5 rounded-lg border border-slate-300 text-xs text-slate-700 bg-white focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
            >
              <option value="ALL">All Statuses</option>
              <option value="SUBMITTED">Submitted</option>
              <option value="IN_REVIEW">In Review</option>
              <option value="APPROVED">Approved</option>
              <option value="REJECTED">Rejected</option>
            </select>
          </div>
        </div>
      </div>

      {/* Claims Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        {loading ? (
          <div className="py-16 text-center text-slate-400 text-xs">
            <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            <p>Loading requests...</p>
          </div>
        ) : filteredClaims.length === 0 ? (
          <div className="py-16 text-center max-w-sm mx-auto text-xs text-slate-500">
            <Receipt className="w-8 h-8 text-slate-300 mx-auto mb-2" />
            <h3 className="font-semibold text-slate-800">No Requests Found</h3>
            <p className="mt-1 mb-4">No submissions match your search or filter.</p>
            <Link
              to="/claims/new"
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-indigo-600 text-white font-semibold hover:bg-indigo-700 shadow-xs"
            >
              <Plus className="w-3.5 h-3.5" /> Submit Request
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-400 font-semibold text-[10px] uppercase tracking-wider">
                  <th className="py-3 px-4">Request #</th>
                  <th className="py-3 px-4">Title & Details</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">Standard Checked</th>
                  <th className="py-3 px-4 text-right">Amount</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredClaims.map((claim) => (
                  <tr key={claim.id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-bold text-indigo-700">
                      {claim.claim_number}
                    </td>

                    <td className="py-3.5 px-4">
                      <div className="font-semibold text-slate-900">{claim.title}</div>
                      <div className="text-[11px] text-slate-400">
                        {claim.employee_name || 'Employee'} • {new Date(claim.created_at).toLocaleDateString()}
                      </div>
                    </td>

                    <td className="py-3.5 px-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700 uppercase">
                        {claim.claim_type}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 text-slate-600 max-w-[160px] truncate">
                      {claim.policy_name || 'Standard Policy'}
                    </td>

                    <td className="py-3.5 px-4 text-right font-bold text-slate-900">
                      ${claim.total_amount?.toFixed(2)} {claim.currency}
                    </td>

                    <td className="py-3.5 px-4">{getStatusBadge(claim.status)}</td>

                    <td className="py-3.5 px-4 text-right">
                      <Link
                        to={`/claims/${claim.id}`}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold text-indigo-600 hover:text-indigo-800 bg-indigo-50 hover:bg-indigo-100 transition-colors"
                      >
                        View <ArrowRight className="w-3 h-3" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
