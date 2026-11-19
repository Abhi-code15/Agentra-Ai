import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import WorkflowLoopBanner from '../components/WorkflowLoopBanner';
import {
  CheckSquare,
  CheckCircle2,
  XCircle,
  Clock,
  AlertCircle,
  ArrowRight,
  UserCheck,
  X,
  Send,
  HelpCircle,
  BookOpen,
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

    if (decision !== 'APPROVED' && !comments.trim()) {
      setError('Please provide comments explaining what needs to be changed.');
      return;
    }

    setSubmitting(true);

    try {
      await api.post(`/reviews/${selectedTask.id}/decision`, {
        decision,
        reviewer_comments: comments,
      });
      setSuccessMsg(`Decision recorded: ${decision === 'APPROVED' ? 'Approved' : decision === 'REJECTED' ? 'Rejected' : 'Changes Requested'}.`);
      setSelectedTask(null);
      setComments('');
      await fetchQueue();
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to submit review decision.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-12">
      {/* Visual Workflow Loop */}
      <WorkflowLoopBanner role="REVIEWER" activeStep={4} />

      {/* Header */}
      <div className="pb-3 border-b border-slate-200">
        <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <CheckSquare className="w-5 h-5 text-indigo-600" />
          Review Queue
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Review employee requests that exceed policy limits or require manager verification.
        </p>
      </div>

      {successMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg flex items-center gap-2 text-emerald-800 text-xs">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {error && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-center gap-2 text-rose-700 text-xs">
          <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Review Tasks List */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        {loading ? (
          <div className="py-16 text-center text-slate-400 text-xs">
            <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            <p>Loading pending reviews...</p>
          </div>
        ) : tasks.length === 0 ? (
          <div className="py-16 text-center text-slate-500 text-xs">
            <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2 opacity-80" />
            <p className="font-semibold text-slate-800 text-sm">Review Queue Clear</p>
            <p className="text-slate-400 mt-0.5">No employee requests currently require your decision.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {tasks.map((task) => {
              const finding = task.finding;
              return (
                <div key={task.id} className="p-5 space-y-3 hover:bg-slate-50/50 transition-colors">
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                    <div className="space-y-1.5 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-amber-50 text-amber-700 border border-amber-200">
                          {finding?.severity || 'HIGH'}
                        </span>
                        <span className="font-mono text-xs font-semibold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">
                          {finding?.rule_code || 'RULE-CHECK'}
                        </span>
                        <span className="text-[11px] text-slate-400">
                          Submitted on {new Date(task.created_at).toLocaleDateString()}
                        </span>
                      </div>

                      <h3 className="text-sm font-bold text-slate-900">{finding?.title || 'Policy Rule Finding'}</h3>
                      <p className="text-xs text-slate-600 leading-relaxed">{finding?.description}</p>

                      {finding?.evidence_quote && (
                        <div className="p-2.5 rounded bg-slate-50 border border-slate-200 text-xs">
                          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block mb-0.5">
                            Policy Excerpt:
                          </span>
                          <p className="italic text-slate-700 font-serif leading-relaxed">
                            &ldquo;{finding.evidence_quote}&rdquo;
                          </p>
                        </div>
                      )}
                    </div>

                    <div className="flex items-center gap-2 flex-shrink-0">
                      {task.claim_id && (
                        <Link
                          to={`/claims/${task.claim_id}`}
                          className="px-3 py-1.5 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 text-xs font-semibold"
                        >
                          View Request
                        </Link>
                      )}

                      <button
                        onClick={() => {
                          setSelectedTask(task);
                          setError('');
                          setComments('');
                        }}
                        className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg text-xs shadow-xs transition-colors"
                      >
                        <UserCheck className="w-3.5 h-3.5" />
                        <span>Decide</span>
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Review Decision Modal */}
      {selectedTask && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="bg-white rounded-xl border border-slate-200 shadow-xl max-w-lg w-full overflow-hidden animate-in fade-in zoom-in-95 duration-100">
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <CheckSquare className="w-4 h-4 text-indigo-600" />
                Review Decision
              </h3>
              <button
                onClick={() => setSelectedTask(null)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-md"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleDecisionSubmit} className="p-6 space-y-4">
              <div>
                <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 block mb-1">
                  Item Under Review
                </span>
                <p className="text-xs font-bold text-slate-900">{selectedTask.finding?.title}</p>
                <p className="text-xs text-slate-600 mt-1">{selectedTask.finding?.description}</p>
              </div>

              {/* Action Buttons */}
              <div className="grid grid-cols-3 gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setDecision('APPROVED')}
                  className={`p-2.5 rounded-lg border text-xs font-bold flex items-center justify-center gap-1.5 transition-all ${
                    decision === 'APPROVED'
                      ? 'bg-emerald-50 border-emerald-500 text-emerald-800 shadow-xs'
                      : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  Approve
                </button>

                <button
                  type="button"
                  onClick={() => setDecision('REJECTED')}
                  className={`p-2.5 rounded-lg border text-xs font-bold flex items-center justify-center gap-1.5 transition-all ${
                    decision === 'REJECTED'
                      ? 'bg-rose-50 border-rose-500 text-rose-800 shadow-xs'
                      : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  <XCircle className="w-3.5 h-3.5 text-rose-600" />
                  Reject
                </button>

                <button
                  type="button"
                  onClick={() => setDecision('NEEDS_REVISION')}
                  className={`p-2.5 rounded-lg border text-xs font-bold flex items-center justify-center gap-1.5 transition-all ${
                    decision === 'NEEDS_REVISION'
                      ? 'bg-amber-50 border-amber-500 text-amber-800 shadow-xs'
                      : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  <HelpCircle className="w-3.5 h-3.5 text-amber-600" />
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
                      ? 'Explain what needs to be changed or why this was rejected...'
                      : 'Optional notes for records...'
                  }
                  value={comments}
                  onChange={(e) => setComments(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-indigo-500 focus:outline-hidden"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setSelectedTask(null)}
                  className="px-4 py-2 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs disabled:opacity-50"
                >
                  {submitting ? 'Recording...' : 'Submit Decision'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
