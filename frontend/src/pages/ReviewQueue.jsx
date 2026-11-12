import React, { useEffect, useState } from 'react';
import api from '../api/client';
import {
  CheckSquare,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  Shield,
  MessageSquare,
  AlertCircle,
  ChevronRight,
  UserCheck,
} from 'lucide-react';

export default function ReviewQueue() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTask, setSelectedTask] = useState(null);
  const [decision, setDecision] = useState('APPROVED');
  const [comments, setComments] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const fetchQueue = async () => {
    try {
      setLoading(true);
      const res = await api.get('/reviews?status=OPEN');
      setTasks(res.data.data || []);
    } catch (err) {
      console.error('Failed to load review queue', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, []);

  const handleDecisionSubmit = async (e) => {
    e.preventDefault();
    if (!selectedTask) return;
    setError('');
    setSuccessMsg('');
    setSubmitting(true);

    try {
      await api.post(`/reviews/${selectedTask.id}/decision`, {
        decision,
        reviewer_comments: comments,
      });
      setSuccessMsg(`Review successfully recorded as ${decision}.`);
      setSelectedTask(null);
      setComments('');
      await fetchQueue();
    } catch (err) {
      setError(
        err.response?.data?.error?.message || 'Failed to submit review decision.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="pb-2 border-b border-slate-200">
        <h1 className="text-xl font-bold text-slate-900 tracking-tight">
          Human-in-the-Loop Review Queue
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Compliance officers inspect flagged citations, verify evidence, and record immutable governance decisions
        </p>
      </div>

      {successMsg && (
        <div className="p-3.5 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center gap-3 text-emerald-800 text-xs">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0 text-emerald-600" />
          <span>{successMsg}</span>
        </div>
      )}

      {error && (
        <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl flex items-center gap-3 text-rose-700 text-xs">
          <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-600" />
          <span>{error}</span>
        </div>
      )}

      {/* Review Tasks List */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center">
            <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
            <p className="text-xs text-slate-400">Loading open review tasks...</p>
          </div>
        ) : tasks.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <div className="w-10 h-10 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto mb-2">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <p className="font-semibold text-xs text-slate-800">Review Queue Clear</p>
            <p className="text-xs text-slate-400 mt-0.5">
              All flagged findings have been verified. No pending tasks require adjudication.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {tasks.map((task) => {
              const finding = task.finding;
              const isHigh = finding?.severity === 'CRITICAL' || finding?.severity === 'HIGH';
              return (
                <div key={task.id} className="p-5 space-y-3 hover:bg-slate-50/60 transition-colors">
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider ${
                            isHigh
                              ? 'bg-rose-50 text-rose-700 border border-rose-200'
                              : 'bg-amber-50 text-amber-700 border border-amber-200'
                          }`}
                        >
                          {finding?.severity || 'HIGH'}
                        </span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-slate-100 text-slate-600 border border-slate-200">
                          {finding?.rule_code || 'EXP_RULE'}
                        </span>
                        <span className="text-[10px] text-slate-400 font-mono">
                          Task ID: {task.id.slice(0, 8)}
                        </span>
                      </div>
                      <h3 className="text-sm font-semibold text-slate-900">{finding?.title}</h3>
                      <p className="text-xs text-slate-600">{finding?.description}</p>
                    </div>

                    <button
                      onClick={() => {
                        setSelectedTask(task);
                        setError('');
                        setComments('');
                      }}
                      className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-slate-900 hover:bg-indigo-600 text-white font-medium rounded-lg text-xs transition-colors shadow-sm flex-shrink-0"
                    >
                      <UserCheck className="w-3.5 h-3.5" />
                      <span>Review & Adjudicate</span>
                    </button>
                  </div>

                  {/* Quoted Citation */}
                  {finding?.evidence_quote && (
                    <div className="p-3 bg-slate-50 rounded-lg border-l-2 border-indigo-500 text-xs text-slate-700">
                      <span className="text-[10px] font-semibold uppercase tracking-wider text-indigo-700 block mb-0.5">
                        Document Citation:
                      </span>
                      <blockquote className="italic text-slate-800">
                        "{finding.evidence_quote}"
                      </blockquote>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Adjudication Modal */}
      {selectedTask && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white max-w-lg w-full rounded-xl p-6 border border-slate-200 shadow-xl space-y-4">
            <div>
              <h2 className="text-base font-semibold text-slate-900">Render Compliance Decision</h2>
              <p className="text-xs text-slate-400 mt-0.5 font-mono">
                Adjudicating Finding: {selectedTask.finding?.title}
              </p>
            </div>

            <form onSubmit={handleDecisionSubmit} className="space-y-4">
              <div>
                <label className="block text-[11px] font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Governance Verdict
                </label>
                <div className="grid grid-cols-3 gap-2">
                  <button
                    type="button"
                    onClick={() => setDecision('APPROVED')}
                    className={`py-2 px-3 rounded-lg text-xs font-semibold border transition-colors flex items-center justify-center gap-1.5 ${
                      decision === 'APPROVED'
                        ? 'bg-emerald-50 border-emerald-500 text-emerald-800 shadow-xs'
                        : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Approve
                  </button>

                  <button
                    type="button"
                    onClick={() => setDecision('REJECTED')}
                    className={`py-2 px-3 rounded-lg text-xs font-semibold border transition-colors flex items-center justify-center gap-1.5 ${
                      decision === 'REJECTED'
                        ? 'bg-rose-50 border-rose-500 text-rose-800 shadow-xs'
                        : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    <XCircle className="w-3.5 h-3.5" />
                    Reject
                  </button>

                  <button
                    type="button"
                    onClick={() => setDecision('NEEDS_REVISION')}
                    className={`py-2 px-3 rounded-lg text-xs font-semibold border transition-colors flex items-center justify-center gap-1.5 ${
                      decision === 'NEEDS_REVISION'
                        ? 'bg-amber-50 border-amber-500 text-amber-800 shadow-xs'
                        : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    <Clock className="w-3.5 h-3.5" />
                    Revision
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Reviewer Commentary {decision === 'REJECTED' && <span className="text-rose-500">*</span>}
                </label>
                <textarea
                  rows={3}
                  required={decision === 'REJECTED'}
                  value={comments}
                  onChange={(e) => setComments(e.target.value)}
                  placeholder={
                    decision === 'REJECTED'
                      ? 'Detailed explanation mandatory when rejecting a compliance finding...'
                      : 'Optional commentary recorded in the immutable audit ledger...'
                  }
                  className="w-full p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2.5 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedTask(null)}
                  className="px-3.5 py-2 rounded-lg text-xs font-medium text-slate-600 hover:bg-slate-100 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 rounded-lg text-xs font-medium bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm disabled:opacity-50 transition-colors"
                >
                  {submitting ? 'Recording Decision...' : 'Commit Decision to Audit Trail'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
