import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import WorkflowLoopBanner from '../components/WorkflowLoopBanner';
import {
  FileText,
  ArrowLeft,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Clock,
  ShieldCheck,
  DollarSign,
  Download,
  RefreshCw,
  Send,
  HelpCircle,
  BookOpen,
  Printer,
  Sparkles,
  CreditCard,
  Building,
  UserCheck,
} from 'lucide-react';

export default function ClaimDetail() {
  const { id: claimId } = useParams();
  const { user } = useAuth();
  const isReviewer = user?.role === 'REVIEWER' || user?.role === 'ADMIN';

  const [claim, setClaim] = useState(null);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  // Review Decision State
  const [decision, setDecision] = useState('APPROVED');
  const [reviewerComments, setReviewerComments] = useState('');
  const [submittingReview, setSubmittingReview] = useState(false);

  // Fetch claim
  const fetchClaim = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/claims/${claimId}`);
      setClaim(res.data.data);
    } catch (err) {
      setErrorMessage(err.response?.data?.error?.message || 'Failed to load reimbursement details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClaim();
  }, [claimId]);

  // Re-run Check
  const handleReevaluate = async () => {
    try {
      setEvaluating(true);
      setErrorMessage('');
      setSuccessMessage('');
      await api.post(`/claims/${claimId}/evaluate`);
      setSuccessMessage('Policy check refreshed successfully.');
      await fetchClaim();
    } catch (err) {
      setErrorMessage(err.response?.data?.error?.message || 'Failed to re-check rules.');
    } finally {
      setEvaluating(false);
    }
  };

  // Submit Decision
  const handleReviewDecision = async (e) => {
    e.preventDefault();
    if (!claim?.review_task_id) return;

    if ((decision === 'REJECTED' || decision === 'NEEDS_REVISION') && !reviewerComments.trim()) {
      setErrorMessage('Please provide a reason or comment for the employee.');
      return;
    }

    try {
      setSubmittingReview(true);
      setErrorMessage('');
      setSuccessMessage('');

      await api.post(`/reviews/${claim.review_task_id}/decision`, {
        decision,
        reviewer_comments: reviewerComments,
      });

      setSuccessMessage(
        `Decision recorded: ${
          decision === 'APPROVED' ? 'Approved' : decision === 'REJECTED' ? 'Rejected' : 'Changes Requested'
        }`
      );
      setReviewerComments('');
      await fetchClaim();
    } catch (err) {
      setErrorMessage(err.response?.data?.error?.message || 'Failed to submit decision.');
    } finally {
      setSubmittingReview(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[350px] text-slate-400">
        <RefreshCw className="w-6 h-6 animate-spin text-indigo-600 mb-2" />
        <p className="text-xs">Loading reimbursement details...</p>
      </div>
    );
  }

  if (!claim) {
    return (
      <div className="max-w-4xl mx-auto py-12 text-center">
        <h2 className="text-base font-bold text-slate-900 mb-2">Reimbursement Not Found</h2>
        <p className="text-xs text-slate-500 mb-4">The requested reimbursement claim could not be located.</p>
        <Link
          to="/claims"
          className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-xs font-semibold hover:bg-indigo-700"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Reimbursements
        </Link>
      </div>
    );
  }

  const getStatusBadge = (status) => {
    switch (status) {
      case 'APPROVED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Approved for Payout
          </span>
        );
      case 'REJECTED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            <XCircle className="w-3.5 h-3.5 text-rose-600" /> Rejected
          </span>
        );
      case 'IN_REVIEW':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            <Clock className="w-3.5 h-3.5 text-amber-600" /> Awaiting Manager Review
          </span>
        );
      case 'REVISION_REQUESTED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-orange-50 text-orange-700 border border-orange-200">
            <HelpCircle className="w-3.5 h-3.5 text-orange-600" /> Changes Requested
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
            {status}
          </span>
        );
    }
  };

  const issues = claim.findings?.filter((f) => f.finding_type === 'violation') || [];
  const activeLoopStep = claim.status === 'APPROVED' ? 5 : claim.status === 'IN_REVIEW' ? 4 : 3;

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-16">
      {/* Workflow Loop Stepper */}
      <WorkflowLoopBanner role={user?.role} activeStep={activeLoopStep} />

      <div className="flex items-center justify-between print:hidden">
        <Link
          to="/claims"
          className="inline-flex items-center gap-1 text-xs font-semibold text-slate-500 hover:text-indigo-600 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Reimbursements
        </Link>
      </div>

      {errorMessage && (
        <div className="p-3.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-500 flex-shrink-0" />
          {errorMessage}
        </div>
      )}
      {successMessage && (
        <div className="p-3.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-medium flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
          {successMessage}
        </div>
      )}

      {/* ========================================================================= */}
      {/* 1. DEDICATED APPROVED REIMBURSEMENT VOUCHER UI (When status is APPROVED) */}
      {/* ========================================================================= */}
      {claim.status === 'APPROVED' && (
        <div className="bg-gradient-to-br from-emerald-50/50 via-white to-emerald-50/20 rounded-2xl border-2 border-emerald-400/90 shadow-md p-6 sm:p-8 space-y-6 relative overflow-hidden print:border-black print:shadow-none">
          {/* Watermark Seal */}
          <div className="absolute -right-8 -bottom-8 w-56 h-56 border-8 border-emerald-200/30 rounded-full flex items-center justify-center pointer-events-none select-none">
            <div className="border-2 border-dashed border-emerald-300/40 w-44 h-44 rounded-full flex flex-col items-center justify-center text-emerald-400/40 font-black uppercase tracking-widest text-[10px] transform -rotate-12">
              <span>Official Voucher</span>
              <span>Authorized</span>
              <span>Paid Out</span>
            </div>
          </div>

          {/* Voucher Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-emerald-200">
            <div className="flex items-center gap-3.5">
              <div className="w-12 h-12 rounded-xl bg-emerald-600 text-white flex items-center justify-center shadow-xs flex-shrink-0">
                <CheckCircle2 className="w-7 h-7" />
              </div>
              <div>
                <span className="text-[10px] font-bold uppercase tracking-widest text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full inline-block">
                  Authorized Payment Voucher
                </span>
                <h2 className="text-xl font-black text-slate-900 tracking-tight mt-1">
                  Reimbursement Approval Voucher
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Voucher #{claim.claim_number} • Ready for direct deposit disbursement
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 print:hidden">
              <button
                onClick={() => window.print()}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold shadow-xs transition-colors"
              >
                <Printer className="w-3.5 h-3.5" />
                <span>Print / Save Voucher</span>
              </button>
            </div>
          </div>

          {/* Three Key Info Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white p-5 rounded-xl border border-emerald-200 shadow-xs">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Authorized Payout Amount
              </span>
              <div className="text-3xl font-black text-emerald-700 tracking-tight">
                ${claim.total_amount?.toFixed(2)}{' '}
                <span className="text-sm font-semibold text-slate-500">{claim.currency}</span>
              </div>
              <span className="text-[11px] text-emerald-600 font-semibold mt-1 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> 100% Approved for Payment
              </span>
            </div>

            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Disbursement Routing
              </span>
              <div className="text-sm font-bold text-slate-800 mt-1 flex items-center gap-1.5">
                <CreditCard className="w-4 h-4 text-indigo-600 flex-shrink-0" />
                <span>Direct Deposit / Payroll</span>
              </div>
              <span className="text-[11px] text-slate-500 mt-1 block">
                Queued for the next scheduled corporate payment cycle
              </span>
            </div>

            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Authorized Sign-Off
              </span>
              <div className="text-sm font-bold text-slate-800 mt-1 flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                <span>{claim.reviewed_by_name || 'Finance Approver'}</span>
              </div>
              <span className="text-[11px] text-slate-500 mt-1 block">
                Approved on{' '}
                {claim.decided_at
                  ? new Date(claim.decided_at).toLocaleDateString()
                  : new Date(claim.updated_at).toLocaleDateString()}
              </span>
            </div>
          </div>

          {/* Voucher Line Items Breakdown */}
          <div className="bg-white rounded-xl border border-emerald-200/90 overflow-hidden shadow-xs">
            <div className="px-5 py-3 bg-emerald-50/70 border-b border-emerald-100 flex items-center justify-between">
              <h3 className="text-xs font-bold text-emerald-950 uppercase tracking-wider">
                Approved Line Items ({claim.line_items?.length || 0})
              </h3>
              <span className="text-[11px] text-emerald-700 font-semibold">
                Verified against {claim.policy_name || 'Company Policy Standard'}
              </span>
            </div>
            <div className="divide-y divide-slate-100 text-xs">
              {claim.line_items?.map((item) => (
                <div key={item.id} className="p-3.5 flex items-center justify-between hover:bg-slate-50/50">
                  <div>
                    <span className="font-bold text-slate-900 block">{item.description}</span>
                    <span className="text-[11px] text-slate-400">
                      Category: {item.category} • Policy Compliant
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="font-bold text-slate-900 block">${item.amount?.toFixed(2)}</span>
                    <span className="text-[10px] font-semibold text-emerald-600 flex items-center gap-0.5 justify-end">
                      <CheckCircle2 className="w-3 h-3" /> Approved
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Reviewer Note if available */}
          {claim.reviewer_comments && (
            <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-900 space-y-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-700 block">
                Manager Review Notes:
              </span>
              <p className="text-emerald-800 italic">&ldquo;{claim.reviewer_comments}&rdquo;</p>
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* 2. REVISION REQUESTED / REJECTED FEEDBACK BOXES */}
      {/* ========================================================================= */}
      {claim.status === 'REVISION_REQUESTED' && (
        <div className="bg-orange-50 border-2 border-orange-300 rounded-xl p-5 shadow-xs space-y-2">
          <div className="flex items-center gap-2">
            <HelpCircle className="w-5 h-5 text-orange-600 flex-shrink-0" />
            <h3 className="text-sm font-bold text-orange-950">
              Manager Requested Changes Before Approval
            </h3>
          </div>
          <p className="text-xs text-orange-800 leading-relaxed">
            Your reviewer has requested additional information or bill updates. Please see their notes below:
          </p>
          {claim.reviewer_comments && (
            <div className="p-3 rounded-lg bg-white border border-orange-200 text-xs text-slate-800 font-medium italic">
              &ldquo;{claim.reviewer_comments}&rdquo;
            </div>
          )}
        </div>
      )}

      {claim.status === 'REJECTED' && (
        <div className="bg-rose-50 border-2 border-rose-300 rounded-xl p-5 shadow-xs space-y-2">
          <div className="flex items-center gap-2">
            <XCircle className="w-5 h-5 text-rose-600 flex-shrink-0" />
            <h3 className="text-sm font-bold text-rose-950">Reimbursement Request Rejected</h3>
          </div>
          <p className="text-xs text-rose-800 leading-relaxed">
            This request was reviewed and cannot be reimbursed under the company policy.
          </p>
          {claim.reviewer_comments && (
            <div className="p-3 rounded-lg bg-white border border-rose-200 text-xs text-slate-800 font-medium italic">
              Reason: &ldquo;{claim.reviewer_comments}&rdquo;
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* 3. MAIN REIMBURSEMENT SUMMARY CARD */}
      {/* ========================================================================= */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-6">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 pb-5 border-b border-slate-100">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2.5 flex-wrap">
              <span className="font-mono text-xs font-bold text-indigo-700 bg-indigo-50 px-2.5 py-0.5 rounded border border-indigo-200">
                {claim.claim_number}
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-100 text-slate-700">
                {claim.claim_type}
              </span>
              {getStatusBadge(claim.status)}
            </div>

            <h1 className="text-lg font-bold text-slate-900 tracking-tight">{claim.title}</h1>
            {claim.description && (
              <p className="text-xs text-slate-600 max-w-2xl">{claim.description}</p>
            )}
          </div>

          <button
            onClick={handleReevaluate}
            disabled={evaluating}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-medium transition-colors disabled:opacity-50 flex-shrink-0 print:hidden"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${evaluating ? 'animate-spin' : ''}`} />
            {evaluating ? 'Checking...' : 'Re-check Rules'}
          </button>
        </div>

        {/* Clean Info Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 text-xs">
          <div>
            <span className="text-slate-400 block text-[10px] font-semibold uppercase tracking-wider">
              Total Amount
            </span>
            <span className="text-base font-bold text-slate-900 mt-0.5 block">
              ${claim.total_amount?.toFixed(2)} {claim.currency}
            </span>
          </div>

          <div>
            <span className="text-slate-400 block text-[10px] font-semibold uppercase tracking-wider">
              Submitted By
            </span>
            <span className="font-semibold text-slate-800 mt-0.5 block truncate">
              {claim.employee_name || 'Employee'}
            </span>
            <span className="text-[11px] text-slate-400">{claim.employee_email}</span>
          </div>

          <div>
            <span className="text-slate-400 block text-[10px] font-semibold uppercase tracking-wider">
              Policy Standard Checked
            </span>
            <span className="font-semibold text-indigo-700 mt-0.5 block truncate">
              {claim.policy_name || 'Company Standard'}
            </span>
          </div>

          <div>
            <span className="text-slate-400 block text-[10px] font-semibold uppercase tracking-wider">
              Date Submitted
            </span>
            <span className="font-semibold text-slate-800 mt-0.5 block">
              {new Date(claim.submission_date || claim.created_at).toLocaleDateString()}
            </span>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 4. POLICY CHECK RESULTS (Simple & Clear) */}
      {/* ========================================================================= */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div>
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-indigo-600" />
              Policy Check Results
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Checked against your company&apos;s approved policy rules and limits.
            </p>
          </div>

          <div>
            {issues.length > 0 ? (
              <span className="text-xs font-bold text-rose-700 bg-rose-50 px-2.5 py-1 rounded-md border border-rose-200">
                {issues.length} Rule Warning{issues.length > 1 ? 's' : ''}
              </span>
            ) : (
              <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-200">
                All Policy Rules Satisfied
              </span>
            )}
          </div>
        </div>

        {(!claim.findings || claim.findings.length === 0) ? (
          <div className="p-8 text-center bg-emerald-50/20">
            <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto mb-2" />
            <h3 className="text-sm font-bold text-emerald-900">Follows All Company Rules</h3>
            <p className="text-xs text-emerald-700 mt-1 max-w-md mx-auto">
              Your request matches the company limits and documentation requirements.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {claim.findings.map((f) => {
              const isViolation = f.finding_type === 'violation';
              return (
                <div key={f.id} className="p-5 hover:bg-slate-50/50 transition-colors">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span
                        className={`text-xs font-bold px-2 py-0.5 rounded border ${
                          isViolation
                            ? 'bg-rose-50 text-rose-700 border-rose-200'
                            : 'bg-amber-50 text-amber-700 border-amber-200'
                        }`}
                      >
                        {isViolation ? 'Exceeds Limit' : 'Note'}
                      </span>
                      <h4 className="text-sm font-bold text-slate-900">{f.title}</h4>
                    </div>

                    <p className="text-xs text-slate-700 leading-relaxed">{f.description}</p>

                    {/* Matched Policy Rule */}
                    {f.evidence && f.evidence.source_quote && (
                      <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs">
                        <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                          Matched Policy Rule:
                        </span>
                        <p className="italic text-slate-700 font-serif leading-relaxed">
                          &ldquo;{f.evidence.source_quote}&rdquo;
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* ========================================================================= */}
      {/* 5. ITEMIZED EXPENSES & ATTACHED RECEIPTS */}
      {/* ========================================================================= */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Line Items Table */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-100 bg-slate-50">
            <h3 className="text-xs font-bold text-slate-900">
              Itemized Bills ({claim.line_items?.length || 0})
            </h3>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50/50 border-b border-slate-200 text-slate-400 font-semibold text-[10px] uppercase tracking-wider">
                  <th className="py-2.5 px-4">Category</th>
                  <th className="py-2.5 px-4">Description</th>
                  <th className="py-2.5 px-4 text-right">Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {claim.line_items?.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50/50">
                    <td className="py-3 px-4 font-semibold text-slate-800">{item.category}</td>
                    <td className="py-3 px-4 text-slate-600">{item.description}</td>
                    <td className="py-3 px-4 text-right font-bold text-slate-900">
                      ${item.amount?.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Attached Files & Proofs */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-5 space-y-3">
          <h3 className="text-xs font-bold text-slate-900 border-b border-slate-100 pb-2">
            Attached Receipts & Proofs ({claim.documents?.length || 0})
          </h3>

          {(!claim.documents || claim.documents.length === 0) ? (
            <div className="py-6 text-center text-slate-400 text-xs">
              <FileText className="w-6 h-6 mx-auto mb-1 opacity-40" />
              <p>No receipts attached</p>
            </div>
          ) : (
            <div className="space-y-2">
              {claim.documents.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs"
                >
                  <div className="truncate mr-2">
                    <span className="font-semibold text-slate-800 block truncate">
                      {doc.original_filename || 'Receipt Bill'}
                    </span>
                    <span className="text-[10px] text-slate-400">
                      {doc.file_size_bytes ? `${(doc.file_size_bytes / 1024).toFixed(1)} KB` : 'Attached'}
                    </span>
                  </div>

                  <a
                    href={`/api/v1/documents/${doc.document_id}/download`}
                    target="_blank"
                    rel="noreferrer"
                    className="p-1.5 text-indigo-600 hover:text-indigo-800 rounded hover:bg-indigo-50 print:hidden"
                    title="Download Receipt"
                  >
                    <Download className="w-4 h-4" />
                  </a>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 6. REVIEWER DECISION SECTION (Only for Reviewer/Admin when review is open) */}
      {/* ========================================================================= */}
      {isReviewer && claim.status === 'IN_REVIEW' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden print:hidden">
          <div className="px-6 py-3 border-b border-slate-100 bg-slate-900 text-white flex items-center justify-between">
            <h3 className="text-xs font-bold">Reviewer Decision Portal</h3>
            <span className="text-[11px] text-slate-300">Authorized Manager Review</span>
          </div>

          <form onSubmit={handleReviewDecision} className="p-6 space-y-4">
            <p className="text-xs text-slate-600">
              Review this employee reimbursement against the policy limits. Choose your decision below.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <button
                type="button"
                onClick={() => setDecision('APPROVED')}
                className={`p-3 rounded-lg border text-xs font-bold flex items-center justify-center gap-2 transition-all ${
                  decision === 'APPROVED'
                    ? 'bg-emerald-50 border-emerald-500 text-emerald-800 shadow-xs'
                    : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                }`}
              >
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                Approve & Issue Voucher
              </button>

              <button
                type="button"
                onClick={() => setDecision('REJECTED')}
                className={`p-3 rounded-lg border text-xs font-bold flex items-center justify-center gap-2 transition-all ${
                  decision === 'REJECTED'
                    ? 'bg-rose-50 border-rose-500 text-rose-800 shadow-xs'
                    : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                }`}
              >
                <XCircle className="w-4 h-4 text-rose-600" />
                Reject Claim
              </button>

              <button
                type="button"
                onClick={() => setDecision('NEEDS_REVISION')}
                className={`p-3 rounded-lg border text-xs font-bold flex items-center justify-center gap-2 transition-all ${
                  decision === 'NEEDS_REVISION'
                    ? 'bg-amber-50 border-amber-500 text-amber-800 shadow-xs'
                    : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                }`}
              >
                <HelpCircle className="w-4 h-4 text-amber-600" />
                Request Changes
              </button>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Reviewer Notes {decision !== 'APPROVED' ? '(Required)' : '(Optional)'}
              </label>
              <textarea
                rows={3}
                required={decision !== 'APPROVED'}
                placeholder={
                  decision !== 'APPROVED'
                    ? 'Explain to the employee what needs to be changed or why this was rejected...'
                    : 'Add optional notes for the employee or records...'
                }
                value={reviewerComments}
                onChange={(e) => setReviewerComments(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-indigo-500 focus:outline-hidden"
              />
            </div>

            <div className="flex items-center justify-end pt-1">
              <button
                type="submit"
                disabled={submittingReview || !claim.review_task_id}
                className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-xs transition-colors disabled:opacity-50"
              >
                <Send className="w-3.5 h-3.5" />
                {submittingReview ? 'Recording...' : 'Submit Decision'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
