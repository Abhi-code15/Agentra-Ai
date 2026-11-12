import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import AIChatDrawer from '../components/AIChatDrawer';
import {
  FileText,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowRight,
  UploadCloud,
  Sparkles,
  ShieldCheck,
  CheckSquare,
  Activity,
  Layers,
} from 'lucide-react';

export default function Dashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    totalDocs: 0,
    openFindings: 0,
    openReviews: 0,
    criticalFindings: 0,
  });
  const [recentDocs, setRecentDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isChatOpen, setIsChatOpen] = useState(false);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [docsRes, findingsRes] = await Promise.all([
          api.get('/documents?page=1&page_size=5'),
          api.get('/findings?page=1&page_size=50'),
        ]);

        const totalDocs = docsRes.data.pagination?.total_records || 0;
        setRecentDocs(docsRes.data.data || []);

        const findingsList = findingsRes.data.data || [];
        const openFindings = findingsList.filter((f) => f.status === 'PENDING_REVIEW').length;
        const criticalFindings = findingsList.filter(
          (f) => f.severity === 'CRITICAL' || f.severity === 'HIGH'
        ).length;

        let openReviews = 0;
        if (user?.role === 'REVIEWER' || user?.role === 'ADMIN') {
          try {
            const revRes = await api.get('/reviews?status=OPEN');
            openReviews = revRes.data.pagination?.total_records || 0;
          } catch (e) {
            // Non-reviewers
          }
        }

        setStats({
          totalDocs,
          openFindings,
          openReviews,
          criticalFindings,
        });
      } catch (err) {
        console.error('Failed to load dashboard metrics', err);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, [user]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-80 space-y-2">
        <div className="w-7 h-7 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-xs text-slate-400">Loading governance metrics...</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Enterprise Hero Banner */}
      <div className="bg-white rounded-xl border border-slate-200/80 p-8 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-medium bg-indigo-50 text-indigo-700 border border-indigo-100">
              <Activity className="w-3 h-3 text-indigo-600" />
              Engine Online • Gemini 3.5 Flash
            </span>
            <span className="text-xs text-slate-400">• Role: {user?.role}</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Governance Control Center
          </h1>
          <p className="text-xs text-slate-500 mt-1 max-w-xl">
            Analyze corporate documents, extract policy limits, evaluate deterministic compliance rules,
            and resolve human-in-the-loop audit findings.
          </p>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <button
            onClick={() => setIsChatOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 font-medium rounded-lg text-xs transition-colors shadow-sm"
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
            <span>Ask AI Assistant</span>
          </button>

          <Link
            to="/documents"
            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg text-xs transition-colors shadow-sm"
          >
            <UploadCloud className="w-3.5 h-3.5" />
            <span>Upload Document</span>
          </Link>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Total Documents</p>
            <h3 className="text-2xl font-bold text-slate-900 mt-1">{stats.totalDocs}</h3>
            <span className="text-[10px] text-slate-400 mt-0.5 block">Ingested & Indexed</span>
          </div>
          <div className="w-10 h-10 rounded-lg bg-indigo-50 border border-indigo-100/80 flex items-center justify-center text-indigo-600">
            <FileText className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Open Findings</p>
            <h3 className="text-2xl font-bold text-slate-900 mt-1">{stats.openFindings}</h3>
            <span className="text-[10px] text-slate-400 mt-0.5 block">Pending Verification</span>
          </div>
          <div className="w-10 h-10 rounded-lg bg-amber-50 border border-amber-100/80 flex items-center justify-center text-amber-600">
            <Clock className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Critical / High</p>
            <h3 className="text-2xl font-bold text-rose-600 mt-1">{stats.criticalFindings}</h3>
            <span className="text-[10px] text-slate-400 mt-0.5 block">Policy Contradictions</span>
          </div>
          <div className="w-10 h-10 rounded-lg bg-rose-50 border border-rose-100/80 flex items-center justify-center text-rose-600">
            <AlertTriangle className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Review Queue</p>
            <h3 className="text-2xl font-bold text-slate-900 mt-1">{stats.openReviews}</h3>
            <span className="text-[10px] text-slate-400 mt-0.5 block">Tasks Awaiting Reviewer</span>
          </div>
          <div className="w-10 h-10 rounded-lg bg-sky-50 border border-sky-100/80 flex items-center justify-center text-sky-600">
            <CheckSquare className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Recent Documents Table */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Recent Document Ingestions</h3>
            <p className="text-xs text-slate-400 mt-0.5">Most recent operational policies ready for analysis</p>
          </div>
          <Link
            to="/documents"
            className="text-xs font-medium text-indigo-600 hover:text-indigo-800 flex items-center gap-1 transition-colors"
          >
            <span>View All</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {recentDocs.length === 0 ? (
          <div className="p-8 text-center text-slate-400 text-xs">
            No documents uploaded yet. Click "Upload Document" to begin.
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {recentDocs.map((doc) => (
              <div
                key={doc.id}
                className="p-4 hover:bg-slate-50/70 transition-colors flex items-center justify-between gap-4"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-8 h-8 rounded-lg bg-indigo-50 border border-indigo-100 text-indigo-600 flex items-center justify-center flex-shrink-0">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div className="min-w-0">
                    <Link
                      to={`/documents/${doc.id}`}
                      className="text-xs font-semibold text-slate-900 hover:text-indigo-600 truncate block transition-colors"
                    >
                      {doc.original_filename}
                    </Link>
                    <span className="text-[10px] text-slate-400">
                      Uploaded on {new Date(doc.created_at).toLocaleDateString()} • {(doc.file_size_bytes / 1024).toFixed(1)} KB
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-3 flex-shrink-0">
                  <span
                    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium ${
                      doc.document_status === 'READY_FOR_ANALYSIS'
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        : 'bg-amber-50 text-amber-700 border border-amber-200'
                    }`}
                  >
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${
                        doc.document_status === 'READY_FOR_ANALYSIS' ? 'bg-emerald-500' : 'bg-amber-500'
                      }`}
                    ></span>
                    {doc.document_status.replace(/_/g, ' ')}
                  </span>

                  <Link
                    to={`/documents/${doc.id}`}
                    className="p-1.5 rounded-md hover:bg-slate-100 text-slate-400 hover:text-slate-800 transition-colors"
                  >
                    <ArrowRight className="w-4 h-4" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* AI Chatbot Drawer */}
      <AIChatDrawer isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
    </div>
  );
}
