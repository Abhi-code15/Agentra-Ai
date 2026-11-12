import React, { useEffect, useState } from 'react';
import api from '../api/client';
import {
  CheckSquare,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  Shield,
  MessageSquare,
  AlertCircle,
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
      setSuccessMsg(`Review successfully adjudicated as ${decision}.`);
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
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Human-in-the-Loop Review Queue</h1>
        <p className="text-sm text-slate-500 mt-1">
          Authorized compliance officers inspect citations and render authoritative governance decisions
        </p>
      </div>

      {successMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center gap-3 text-emerald-800 text-xs">
          <CheckCircle className="w-4 h-4 flex-shrink-0 text-emerald-600" />
          <span>{successMsg}</span>
        </div>
      )}

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-center gap-3 text-rose-700 text-xs">
          <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-600" />
          <span>{error}</span>
        </div>
      )}

      {/* Review Tasks List */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600 mx-auto"></div>
          </div>
        ) : tasks.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <CheckCircle className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
            <p className="font-semibold text-sm">Review Queue Clear!</p>
            <p className="text-xs text-slate-400 mt-1">There are no pending review tasks requiring human adjudication.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {tasks.map((task) => {
              const finding = task.finding;
              return (
                <div key={task.id} className="p-6 space-y-4 hover:bg-slate-50/50 transition-colors">
                  <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2 mb-1.5">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                            finding?.severity === 'CRITICAL' || finding?.severity === 'HIGH'
                              ? 'bg-rose-100 text-rose-700 border border-rose-200'
                              : 'bg-amber-100 text-amber-700 border border-amber-200'
                          }`}
                        >
                          {finding?.severity || 'HIGH'}
                        </span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-600">
                          {finding?.finding_type || 'violation'}
                        </span>
                        <span className="text-xs text-slate-400 font-mono">
                          Task ID: {task.id.slice(0, 8)}
                        </span>
                      </div>
                      <h3 className="text-base font-bold text-slate-900">{finding?.title}</h3>
                      <p className="text-xs text-slate-600 mt-1">{finding?.description}</p>
                    </div>

                    <button
                      onClick={() => {
                        setSelectedTask(task);
                        setError('');
                        setComments('');
                      }}
                      className="inline-flex items-center gap-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white font-semibold rounded-xl text-xs transition-colors shadow-sm"
                    >
                      <CheckSquare className="w-3.5 h-3.5" />
                      Adjudicate Task
                    </button>
                  </div>

                  {/* Evidence Citation */}
                  {finding?.evidence?.quote && (
                    <div className="p-3 bg-slate-900 rounded-xl text-slate-300 text-xs">
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                        Source Policy Citation (Page {finding.evidence?.page || 1})
                      </span>
                      <blockquote className="italic border-l-2 border-emerald-500 pl-3 text-slate-200">
                        "{finding.evidence.quote}"
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
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white max-w-lg w-full rounded-2xl p-6 border border-slate-200 shadow-2xl space-y-4">
            <h2 className="text-lg font-bold text-slate-900">Render Review Decision</h2>
            <p className="text-xs text-slate-500">
              Task ID: <span className="font-mono">{selectedTask.id}</span>
            </p>

            <form onSubmit={handleDecisionSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                  Governance Verdict
                </label>
                <div className="grid grid-cols-3 gap-2">
                  <button
                    type="button"
                    onClick={() => setDecision('APPROVED')}
                    className={`py-2 px-3 rounded-xl text-xs font-bold border transition-colors flex items-center justify-center gap-1.5 ${
                      decision === 'APPROVED'
                        ? 'bg-emerald-50 border-emerald-500 text-emerald-800 shadow-sm'
                        : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    <CheckCircle className="w-3.5 h-3.5" />
                    Approve
                  </button>

                  <button
                    type="button"
                    onClick={() => setDecision('REJECTED')}
                    className={`py-2 px-3 rounded-xl text-xs font-bold border transition-colors flex items-center justify-center gap-1.5 ${
                      decision === 'REJECTED'
                        ? 'bg-rose-50 border-rose-500 text-rose-800 shadow-sm'
                        : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    <XCircle className="w-3.5 h-3.5" />
                    Reject
                  </button>

                  <button
                    type="button"
                    onClick={() => setDecision('NEEDS_REVISION')}
                    className={`py-2 px-3 rounded-xl text-xs font-bold border transition-colors flex items-center justify-center gap-1.5 ${
                      decision === 'NEEDS_REVISION'
                        ? 'bg-amber-50 border-amber-500 text-amber-800 shadow-sm'
                        : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    <Clock className="w-3.5 h-3.5" />
                    Revision
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
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
                      : 'Optional commentary recorded in the audit trail...'
                  }
                  className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-emerald-500 focus:bg-white"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedTask(null)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-5 py-2 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-600/20 disabled:opacity-50"
                >
                  {submitting ? 'Submitting...' : 'Sign & Submit Decision'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
