import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import {
  FileText,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowRight,
  UploadCloud,
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
            // Non-reviewers might fail or be forbidden
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
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 p-8 rounded-2xl text-white shadow-sm border border-slate-700/60 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-emerald-400 bg-emerald-950/60 px-3 py-1 rounded-full border border-emerald-800/40">
            Enterprise Governance Portal
          </span>
          <h1 className="text-2xl font-bold mt-2 tracking-tight">Welcome back, {user?.full_name}</h1>
          <p className="text-slate-400 text-sm mt-1">
            Deterministic compliance engine active. All decisions human-audited.
          </p>
        </div>
        <Link
          to="/documents"
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold rounded-xl text-sm transition-all shadow-md shadow-emerald-500/20"
        >
          <UploadCloud className="w-4 h-4" />
          Upload Document
        </Link>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Documents</p>
            <h3 className="text-3xl font-black text-slate-900 mt-1">{stats.totalDocs}</h3>
          </div>
          <div className="w-12 h-12 bg-slate-100 rounded-xl flex items-center justify-center text-slate-600">
            <FileText className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Pending Findings</p>
            <h3 className="text-3xl font-black text-amber-600 mt-1">{stats.openFindings}</h3>
          </div>
          <div className="w-12 h-12 bg-amber-50 rounded-xl flex items-center justify-center text-amber-600">
            <Clock className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">High / Critical</p>
            <h3 className="text-3xl font-black text-rose-600 mt-1">{stats.criticalFindings}</h3>
          </div>
          <div className="w-12 h-12 bg-rose-50 rounded-xl flex items-center justify-center text-rose-600">
            <AlertTriangle className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Pending Reviews</p>
            <h3 className="text-3xl font-black text-emerald-600 mt-1">{stats.openReviews}</h3>
          </div>
          <div className="w-12 h-12 bg-emerald-50 rounded-xl flex items-center justify-center text-emerald-600">
            <CheckCircle2 className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <h2 className="text-base font-bold text-slate-900">Recent Policy Ingestion</h2>
          <Link
            to="/documents"
            className="text-xs font-semibold text-emerald-600 hover:text-emerald-700 flex items-center gap-1"
          >
            View all <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="divide-y divide-slate-100">
          {recentDocs.length === 0 ? (
            <div className="p-8 text-center text-slate-500 text-sm">
              No documents uploaded yet. Upload your first expense reimbursement policy to begin!
            </div>
          ) : (
            recentDocs.map((doc) => (
              <div
                key={doc.id}
                className="px-6 py-4 flex items-center justify-between hover:bg-slate-50/80 transition-colors"
              >
                <div className="flex items-center gap-3.5">
                  <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center text-slate-600">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div>
                    <Link
                      to={`/documents/${doc.id}`}
                      className="text-sm font-semibold text-slate-900 hover:text-emerald-600 transition-colors"
                    >
                      {doc.original_filename}
                    </Link>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Uploaded on {new Date(doc.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <span
                    className={`px-2.5 py-1 rounded-full text-xs font-semibold ${
                      doc.document_status === 'READY_FOR_ANALYSIS'
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        : doc.document_status === 'OCR_REQUIRED'
                        ? 'bg-amber-50 text-amber-700 border border-amber-200'
                        : 'bg-slate-100 text-slate-700'
                    }`}
                  >
                    {doc.document_status}
                  </span>
                  <Link
                    to={`/documents/${doc.id}`}
                    className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
                  >
                    <ArrowRight className="w-4 h-4" />
                  </Link>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
