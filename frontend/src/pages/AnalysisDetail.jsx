import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../api/client';
import AIChatDrawer from '../components/AIChatDrawer';
import {
  ShieldCheck,
  AlertTriangle,
  Clock,
  ArrowLeft,
  CheckCircle2,
  FileText,
  Search,
  ExternalLink,
  ChevronRight,
  Sparkles,
  Layers,
  Terminal,
  Activity,
  UserCheck,
} from 'lucide-react';

export default function AnalysisDetail() {
  const { id } = useParams();
  const [analysis, setAnalysis] = useState(null);
  const [steps, setSteps] = useState([]);
  const [findings, setFindings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [expandedStep, setExpandedStep] = useState(null);

  useEffect(() => {
    const fetchAnalysisData = async () => {
      try {
        setLoading(true);
        const [analysisRes, stepsRes, findingsRes] = await Promise.all([
          api.get(`/analyses/${id}`),
          api.get(`/analyses/${id}/steps`),
          api.get(`/analyses/${id}/findings`),
        ]);
        setAnalysis(analysisRes.data.data);
        setSteps(stepsRes.data.data || []);
        setFindings(findingsRes.data.data || []);
      } catch (err) {
        setError('Failed to load analysis run data.');
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysisData();
  }, [id]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-80 space-y-2">
        <div className="w-7 h-7 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-xs text-slate-400">Loading analysis execution telemetry...</p>
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="max-w-xl mx-auto p-8 text-center bg-white rounded-xl border border-slate-200 shadow-sm mt-12">
        <AlertTriangle className="w-10 h-10 text-rose-500 mx-auto mb-3" />
        <h2 className="text-base font-semibold text-slate-900">Analysis Run Unavailable</h2>
        <p className="text-xs text-slate-500 mt-1 mb-6">{error || 'Requested analysis run was not found.'}</p>
        <Link
          to="/documents"
          className="inline-flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded-lg text-xs font-medium hover:bg-slate-800"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Documents
        </Link>
      </div>
    );
  }

  const criticalCount = findings.filter((f) => f.severity === 'CRITICAL' || f.severity === 'HIGH').length;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Breadcrumb Navigation */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-200">
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <Link to="/documents" className="hover:text-slate-900 transition-colors">
            Documents
          </Link>
          <ChevronRight className="w-3.5 h-3.5 text-slate-300" />
          <Link to={`/documents/${analysis.document_id}`} className="hover:text-slate-900 transition-colors">
            Workspace
          </Link>
          <ChevronRight className="w-3.5 h-3.5 text-slate-300" />
          <span className="font-semibold text-slate-800 font-mono">Run {analysis.id.slice(0, 8)}</span>
        </div>

        <button
          onClick={() => setIsChatOpen(true)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 hover:text-indigo-600 transition-colors shadow-sm"
        >
          <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
          <span>Ask AI About Findings</span>
        </button>
      </div>

      {/* Hero Card */}
      <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5">
              <span
                className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-xs font-medium ${
                  analysis.status === 'COMPLETED'
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                    : 'bg-amber-50 text-amber-700 border border-amber-200'
                }`}
              >
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                {analysis.status}
              </span>
              <span className="text-xs text-slate-400 font-mono">Run ID: {analysis.id}</span>
            </div>
            <h1 className="text-xl font-bold text-slate-900 mt-2 tracking-tight">
              Agent Orchestrator Execution
            </h1>
            <p className="text-xs text-slate-500 mt-0.5">
              Grounded on Gemini 3.5 Flash parameter extraction and deterministic Python rule evaluation.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="bg-slate-50 px-4 py-2.5 rounded-lg border border-slate-200/80 text-right">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 block">
                Findings Generated
              </span>
              <span className="text-lg font-bold text-slate-900">{findings.length} Items</span>
            </div>
          </div>
        </div>
      </div>

      {/* Findings Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-semibold text-slate-900">Compliance Findings & Evidence</h2>
            {criticalCount > 0 && (
              <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                {criticalCount} Action Required
              </span>
            )}
          </div>
          <span className="text-xs text-slate-400">Total: {findings.length} findings</span>
        </div>

        {findings.length === 0 ? (
          <div className="p-8 bg-white rounded-xl border border-slate-200 text-center shadow-sm">
            <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto mb-2" />
            <h3 className="text-xs font-semibold text-slate-800">Clean Compliance Scan</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              No rule contradictions or missing mandates were identified in this document.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {findings.map((f) => {
              const isHigh = f.severity === 'CRITICAL' || f.severity === 'HIGH';
              const isMed = f.severity === 'MEDIUM';
              return (
                <div
                  key={f.id}
                  className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-sm space-y-3 hover:border-slate-300 transition-colors"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider ${
                            isHigh
                              ? 'bg-rose-50 text-rose-700 border border-rose-200'
                              : isMed
                              ? 'bg-amber-50 text-amber-700 border border-amber-200'
                              : 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                          }`}
                        >
                          {f.severity}
                        </span>

                        <span className="text-[11px] font-mono font-semibold text-slate-700">
                          {f.rule_code}
                        </span>

                        <span className="text-[10px] text-slate-400 font-medium">
                          Status: <strong className="text-slate-600">{f.status}</strong>
                        </span>
                      </div>

                      <h3 className="text-sm font-semibold text-slate-900">{f.title}</h3>
                    </div>

                    <span className="text-[10px] text-slate-400 font-mono flex-shrink-0">
                      ID: {f.id.slice(0, 8)}
                    </span>
                  </div>

                  <p className="text-xs text-slate-600 leading-relaxed">{f.description}</p>

                  {/* Quoted Evidence Provenance Box */}
                  {f.evidence_quote && (
                    <div className="p-3 bg-slate-50/80 rounded-lg border-l-2 border-indigo-500 text-xs text-slate-700 space-y-1">
                      <span className="text-[10px] font-semibold uppercase tracking-wider text-indigo-700 block">
                        Verified Policy Citation:
                      </span>
                      <blockquote className="italic text-slate-800">
                        "{f.evidence_quote}"
                      </blockquote>
                      {f.evidence_location && (
                        <span className="text-[10px] text-slate-400 block">
                          Location: {f.evidence_location}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Execution Telemetry (4 Agent Steps) */}
      <div className="space-y-4 pt-4">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-slate-600" />
          <h2 className="text-sm font-semibold text-slate-900">Agent Execution Telemetry</h2>
          <span className="text-[11px] text-slate-400">(4 Bounded Orchestrator Steps)</span>
        </div>

        <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm divide-y divide-slate-100 overflow-hidden">
          {steps.map((st) => (
            <div key={st.step_number} className="p-4 hover:bg-slate-50/60 transition-colors">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-6 h-6 rounded-md bg-indigo-50 text-indigo-600 border border-indigo-100 font-bold text-xs flex items-center justify-center">
                    {st.step_number}
                  </div>
                  <div>
                    <h3 className="text-xs font-semibold text-slate-900 font-mono">{st.tool_name}</h3>
                    <span className="text-[10px] text-slate-400">Duration: {st.execution_time_ms}ms</span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                    {st.step_status}
                  </span>
                  <button
                    onClick={() => setExpandedStep(expandedStep === st.step_number ? null : st.step_number)}
                    className="text-xs text-indigo-600 hover:text-indigo-800 font-medium ml-2"
                  >
                    {expandedStep === st.step_number ? 'Hide I/O' : 'View I/O'}
                  </button>
                </div>
              </div>

              {expandedStep === st.step_number && (
                <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-3 pt-3 border-t border-slate-100 font-mono text-[11px]">
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 overflow-x-auto max-h-48">
                    <span className="text-[10px] font-sans font-bold uppercase text-slate-400 block mb-1">
                      Tool Input
                    </span>
                    <pre className="text-slate-700 whitespace-pre-wrap">{JSON.stringify(st.tool_input, null, 2)}</pre>
                  </div>

                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 overflow-x-auto max-h-48">
                    <span className="text-[10px] font-sans font-bold uppercase text-slate-400 block mb-1">
                      Tool Output
                    </span>
                    <pre className="text-slate-700 whitespace-pre-wrap">{JSON.stringify(st.tool_output, null, 2)}</pre>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* AI Assistant Drawer */}
      <AIChatDrawer
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
        documentId={analysis.document_id}
      />
    </div>
  );
}
