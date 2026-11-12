import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../api/client';
import {
  ShieldCheck,
  AlertTriangle,
  Clock,
  ArrowLeft,
  CheckCircle2,
  FileText,
  Search,
  ExternalLink,
} from 'lucide-react';

export default function AnalysisDetail() {
  const { id } = useParams();
  const [analysis, setAnalysis] = useState(null);
  const [steps, setSteps] = useState([]);
  const [findings, setFindings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

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
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="max-w-2xl mx-auto p-8 text-center bg-white rounded-2xl border border-slate-200 shadow-sm">
        <AlertTriangle className="w-12 h-12 text-rose-500 mx-auto mb-3" />
        <h2 className="text-lg font-bold text-slate-900">Analysis Run Unavailable</h2>
        <p className="text-sm text-slate-500 mt-1 mb-6">{error || 'Requested analysis run was not found.'}</p>
        <Link
          to="/documents"
          className="px-4 py-2 bg-slate-900 text-white rounded-xl text-sm font-semibold hover:bg-slate-800"
        >
          Back to Documents
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Top Navigation */}
      <div>
        <Link
          to={`/documents/${analysis.document_id}`}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Document
        </Link>
      </div>

      {/* Overview Banner */}
      <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-3">
            <span
              className={`px-3 py-1 rounded-full text-xs font-bold ${
                analysis.status === 'COMPLETED'
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                  : 'bg-amber-50 text-amber-700 border border-amber-200'
              }`}
            >
              {analysis.status}
            </span>
            <span className="text-xs text-slate-400 font-mono">Run ID: {analysis.id.slice(0, 8)}</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 mt-2 tracking-tight">
            Compliance Analysis Execution
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Engineered with Gemini 2.5 Flash and Deterministic Python Rule Evaluation
          </p>
        </div>

        <div className="flex items-center gap-6 border-t md:border-t-0 md:border-l border-slate-100 pt-4 md:pt-0 md:pl-8">
          <div>
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Findings</span>
            <p className="text-2xl font-black text-rose-600 mt-0.5">{findings.length}</p>
          </div>
          <div>
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Steps</span>
            <p className="text-2xl font-black text-slate-900 mt-0.5">{steps.length}</p>
          </div>
          <div>
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Model</span>
            <p className="text-xs font-bold text-slate-700 mt-2">{analysis.model_name}</p>
          </div>
        </div>
      </div>

      {/* Agent Execution Timeline */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <h2 className="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
          <Clock className="w-4 h-4 text-emerald-600" />
          Controlled Agent Step Timeline
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          {steps.map((s) => (
            <div key={s.id} className="p-4 bg-slate-50 rounded-xl border border-slate-200/60">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-emerald-600">Step {s.step_number}</span>
                <span className="text-[10px] font-semibold text-slate-400">{s.duration_ms} ms</span>
              </div>
              <p className="text-xs font-semibold text-slate-900 truncate">
                {s.tool_name || s.step_type}
              </p>
              <div className="mt-2 flex items-center gap-1.5 text-[11px] text-emerald-700 font-medium">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>{s.status}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Compliance Findings */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            Identified Findings & Policy Citations
          </h2>
          <span className="text-xs text-slate-500 font-medium">{findings.length} Items Flagged</span>
        </div>

        <div className="divide-y divide-slate-100">
          {findings.length === 0 ? (
            <div className="p-8 text-center text-slate-500 text-sm">
              <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
              All predefined compliance rules passed! Zero policy violations detected.
            </div>
          ) : (
            findings.map((f) => (
              <div key={f.id} className="p-6 space-y-3 hover:bg-slate-50/50 transition-colors">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                          f.severity === 'CRITICAL' || f.severity === 'HIGH'
                            ? 'bg-rose-100 text-rose-700 border border-rose-200'
                            : 'bg-amber-100 text-amber-700 border border-amber-200'
                        }`}
                      >
                        {f.severity}
                      </span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-600">
                        {f.finding_type}
                      </span>
                      <span className="text-xs text-slate-400 font-mono">{f.finding_code}</span>
                    </div>
                    <h3 className="text-base font-bold text-slate-900">{f.title}</h3>
                  </div>

                  <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200">
                    {f.status}
                  </span>
                </div>

                <p className="text-xs text-slate-600 leading-relaxed">{f.description}</p>

                {/* Evidence Quote Citation */}
                {f.evidence?.quote && (
                  <div className="p-3.5 bg-slate-900 rounded-xl border border-slate-800 text-slate-300 text-xs font-sans">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                      Source Document Citation (Page {f.evidence?.page || 1})
                    </span>
                    <blockquote className="italic border-l-2 border-emerald-500 pl-3 text-slate-200">
                      "{f.evidence.quote}"
                    </blockquote>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
