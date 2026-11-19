import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import WorkflowLoopBanner from '../components/WorkflowLoopBanner';
import {
  FileText,
  CheckCircle2,
  Clock,
  ArrowRight,
  PlusCircle,
  AlertCircle,
  Receipt,
  BookOpen,
  CheckSquare,
  DollarSign,
  User,
} from 'lucide-react';

export default function Dashboard() {
  const { user } = useAuth();
  const isReviewer = user?.role === 'REVIEWER' || user?.role === 'ADMIN';

  const [claims, setClaims] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        setLoading(true);
        const [claimsRes, policiesRes] = await Promise.all([
          api.get('/claims?page=1&page_size=10'),
          api.get('/policies?page=1&page_size=10'),
        ]);

        setClaims(claimsRes.data.data || []);
        setPolicies(policiesRes.data.data || []);

        if (isReviewer) {
          try {
            const revRes = await api.get('/reviews?status=OPEN&page=1&page_size=10');
            setReviews(revRes.data.data || []);
          } catch (e) {
            console.error('Failed to load reviews', e);
          }
        }
      } catch (err) {
        console.error('Failed to load dashboard data', err);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, [user, isReviewer]);

  // Metrics
  const totalClaims = claims.length;
  const approvedClaims = claims.filter((c) => c.status === 'APPROVED').length;
  const inReviewClaims = claims.filter((c) => c.status === 'IN_REVIEW').length;
  const totalAmount = claims.reduce((sum, c) => sum + (c.total_amount || 0), 0);

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
            <AlertCircle className="w-3 h-3 text-rose-600" /> Rejected
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
            <Clock className="w-3 h-3 text-orange-600" /> Needs Changes
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

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[350px] text-slate-400">
        <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mb-2" />
        <p className="text-xs">Loading your workspace...</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Visual Workflow Loop */}
      <WorkflowLoopBanner role={user?.role} activeStep={isReviewer ? (reviews.length > 0 ? 4 : 2) : 2} />

      {/* Welcome Banner */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Welcome back, {user?.full_name || 'User'}
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            {isReviewer
              ? 'Review pending employee reimbursement claims and manage official company policy standards.'
              : 'Submit reimbursement claims and check them automatically against company standards.'}
          </p>
        </div>

        <div className="flex items-center gap-3">
          {isReviewer ? (
            <>
              <Link
                to="/reviews"
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs transition-colors"
              >
                <CheckSquare className="w-4 h-4" />
                Review Pending ({reviews.length})
              </Link>
              <Link
                to="/policies"
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 text-xs font-semibold shadow-xs transition-colors"
              >
                <BookOpen className="w-4 h-4 text-indigo-600" />
                Company Policies
              </Link>
            </>
          ) : (
            <Link
              to="/claims/new"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs transition-colors"
            >
              <PlusCircle className="w-4 h-4" />
              Submit New Reimbursement
            </Link>
          )}
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {isReviewer ? (
          <>
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Pending Your Review
              </span>
              <div className="text-2xl font-bold text-amber-600">{reviews.length}</div>
              <span className="text-[11px] text-slate-500 mt-0.5 block">Waiting for decision</span>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Active Policies
              </span>
              <div className="text-2xl font-bold text-slate-900">{policies.length}</div>
              <span className="text-[11px] text-slate-500 mt-0.5 block">Approved standards</span>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Total Claims Value
              </span>
              <div className="text-2xl font-bold text-slate-900">${totalAmount.toFixed(2)}</div>
              <span className="text-[11px] text-slate-500 mt-0.5 block">Across all employees</span>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Approved Claims
              </span>
              <div className="text-2xl font-bold text-emerald-600">{approvedClaims}</div>
              <span className="text-[11px] text-slate-500 mt-0.5 block">Successfully verified</span>
            </div>
          </>
        ) : (
          <>
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                My Total Reimbursements
              </span>
              <div className="text-2xl font-bold text-slate-900">{totalClaims}</div>
              <span className="text-[11px] text-slate-500 mt-0.5 block">Submitted claims</span>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Approved & Paid
              </span>
              <div className="text-2xl font-bold text-emerald-600">{approvedClaims}</div>
              <span className="text-[11px] text-emerald-600 font-medium mt-0.5 block">Vouchers issued</span>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                In Review
              </span>
              <div className="text-2xl font-bold text-amber-600">{inReviewClaims}</div>
              <span className="text-[11px] text-amber-600 font-medium mt-0.5 block">Being checked</span>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Total Amount Claimed
              </span>
              <div className="text-2xl font-bold text-slate-900">${totalAmount.toFixed(2)}</div>
              <span className="text-[11px] text-slate-500 mt-0.5 block">Total reimbursement value</span>
            </div>
          </>
        )}
      </div>

      {/* Main Content Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-900">
            {isReviewer ? 'Reimbursements Pending Review' : 'My Recent Submissions'}
          </h2>
          <Link
            to={isReviewer ? '/reviews' : '/claims'}
            className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
          >
            View All <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {isReviewer ? (
          reviews.length === 0 ? (
            <div className="py-12 text-center text-slate-400 text-xs">
              <CheckCircle2 className="w-8 h-8 mx-auto mb-2 text-emerald-500 opacity-80" />
              <p className="font-medium text-slate-700">Review Inbox is Clear</p>
              <p className="mt-0.5">No employee requests are currently waiting for your decision.</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {reviews.map((task) => (
                <div
                  key={task.id}
                  className="p-4 hover:bg-slate-50/70 transition-colors flex items-center justify-between gap-4"
                >
                  <div>
                    <h3 className="text-xs font-bold text-slate-900">
                      {task.finding?.title || 'Review Task'}
                    </h3>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      Submitted on {new Date(task.created_at).toLocaleDateString()}
                    </p>
                  </div>

                  <Link
                    to={task.claim_id ? `/claims/${task.claim_id}` : '/reviews'}
                    className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs font-semibold transition-colors"
                  >
                    Inspect & Decide <ArrowRight className="w-3 h-3" />
                  </Link>
                </div>
              ))}
            </div>
          )
        ) : claims.length === 0 ? (
          <div className="py-12 text-center text-slate-400 text-xs">
            <Receipt className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="font-medium text-slate-700">No requests submitted yet</p>
            <p className="mt-0.5 mb-3">Click below to submit your first claim or document check.</p>
            <Link
              to="/claims/new"
              className="inline-flex items-center gap-1 px-3.5 py-1.5 rounded-lg bg-indigo-600 text-white text-xs font-semibold shadow-xs hover:bg-indigo-700"
            >
              <PlusCircle className="w-3.5 h-3.5" /> Submit First Request
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {claims.map((claim) => (
              <div
                key={claim.id}
                className="p-4 hover:bg-slate-50/70 transition-colors flex items-center justify-between gap-4"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-indigo-700">{claim.claim_number}</span>
                    <h3 className="text-xs font-bold text-slate-900">{claim.title}</h3>
                  </div>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    {claim.policy_name || 'Standard Policy'} • ${claim.total_amount?.toFixed(2)} • Submitted{' '}
                    {new Date(claim.created_at).toLocaleDateString()}
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  {getStatusBadge(claim.status)}
                  <Link
                    to={`/claims/${claim.id}`}
                    className="p-1.5 rounded-md text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
                  >
                    <ArrowRight className="w-4 h-4" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
