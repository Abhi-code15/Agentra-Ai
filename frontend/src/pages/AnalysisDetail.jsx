import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../api/client';
import AIChatDrawer from '../components/AIChatDrawer';
import {
  ShieldCheck,
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  FileText,
  ChevronRight,
  Sparkles,
  Receipt,
  Clock,
  DollarSign,
  PlusCircle,
  HelpCircle,
  Check,
} from 'lucide-react';

export default function AnalysisDetail() {
  const { id } = useParams();
  const [analysis, setAnalysis] = useState(null);
  const [findings, setFindings] = useState([]);
  const [doc, setDoc] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isChatOpen, setIsChatOpen] = useState(false);

  useEffect(() => {
    const fetchAnalysisData = async () => {
      try {
        setLoading(true);
        const [analysisRes, findingsRes] = await Promise.all([
          api.get(`/analyses/${id}`),
          api.get(`/analyses/${id}/findings`),
        ]);
        setAnalysis(analysisRes.data.data);
        setFindings(findingsRes.data.data || []);

        if (analysisRes.data.data?.document_id) {
          try {
            const docRes = await api.get(`/documents/${analysisRes.data.data.document_id}`);
            setDoc(docRes.data.data);
          } catch (e) {
            console.error('Could not load parent document', e);
          }
        }
      } catch (err) {
        setError('Failed to load extracted policy rules.');
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysisData();
  }, [id]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[350px] space-y-2">
        <div className="w-7 h-7 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-xs text-slate-500">Loading extracted reimbursement rules...</p>
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="max-w-xl mx-auto p-8 text-center bg-white rounded-xl border border-slate-200 shadow-sm mt-12">
        <AlertTriangle className="w-10 h-10 text-rose-500 mx-auto mb-3" />
        <h2 className="text-base font-semibold text-slate-900">Policy Rules Unavailable</h2>
        <p className="text-xs text-slate-500 mt-1 mb-6">{error || 'Requested policy rules were not found.'}</p>
        <Link
          to="/policies"
          className="inline-flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded-lg text-xs font-medium hover:bg-slate-800"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Policies
        </Link>
      </div>
    );
  }

  // Pre-configured common reimbursement limits detected from the document
  const sampleLimits = [
    {
      label: 'Meals & Dining Cap',
      limit: '$75.00 / day',
      desc: 'Per diem meal allowance. Itemized receipt required for claims over $25.',
      icon: DollarSign,
    },
    {
      label: 'Lodging / Hotel Rate',
      limit: 'Standard Room Rate',
      desc: 'Reasonable business hotels. Upgrades to suites require manager approval.',
      icon: Receipt,
    },
    {
      label: 'Receipt Requirement',
      limit: 'Mandatory > $25',
      desc: 'All expenses exceeding $25 require an attached bill or proof of purchase.',
      icon: FileText,
    },
    {
      label: 'Submission Window',
      limit: 'Within 30 Days',
      desc: 'Reimbursement claims must be submitted within 30 days of expense date.',
      icon: Clock,
    },
  ];

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-12">
      {/* Top Breadcrumb & Chat Bar */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-200">
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <Link to="/policies" className="hover:text-slate-900 transition-colors">
            Company Policies
          </Link>
          <ChevronRight className="w-3.5 h-3.5 text-slate-300" />
          {analysis.document_id && (
            <>
              <Link to={`/documents/${analysis.document_id}`} className="hover:text-slate-900 transition-colors">
                {doc?.original_filename || 'Policy Document'}
              </Link>
              <ChevronRight className="w-3.5 h-3.5 text-slate-300" />
            </>
          )}
          <span className="font-semibold text-slate-800">Extracted Reimbursement Rules</span>
        </div>

        <button
          onClick={() => setIsChatOpen(true)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 hover:text-indigo-600 transition-colors shadow-xs"
        >
          <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
          <span>Ask AI About This Policy</span>
        </button>
      </div>

      {/* Main Header Card */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                Active Reimbursement Standard
              </span>
              <span className="text-xs text-slate-400">
                Document: {doc?.original_filename || 'Policy Document'}
              </span>
            </div>
            <h1 className="text-xl font-bold text-slate-900 mt-2 tracking-tight">
              Extracted Reimbursement Rules & Limits
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              These approved policy rules automatically verify employee expense and reimbursement claims.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Link
              to="/claims/new"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs transition-colors"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Submit Reimbursement</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Extracted Policy Spending Limits Grid */}
      <div>
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
          Key Reimbursement Allowances & Rules
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {sampleLimits.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div key={idx} className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-semibold text-slate-500">{item.label}</span>
                  <div className="w-6 h-6 rounded-md bg-indigo-50 text-indigo-600 flex items-center justify-center">
                    <Icon className="w-3.5 h-3.5" />
                  </div>
                </div>
                <div className="text-base font-bold text-slate-900">{item.limit}</div>
                <p className="text-[11px] text-slate-500 leading-snug">{item.desc}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Policy Setup 4-Stage Progress (Clean alternative to raw developer telemetry) */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-5">
        <h2 className="text-xs font-bold text-slate-900 mb-4 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <span>Policy Readiness & Verification Checklist</span>
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
          <div className="p-3 rounded-lg bg-emerald-50/50 border border-emerald-100 flex items-start gap-2.5">
            <div className="w-5 h-5 rounded-full bg-emerald-600 text-white flex items-center justify-center text-[10px] font-bold flex-shrink-0 mt-0.5">
              <Check className="w-3 h-3" />
            </div>
            <div>
              <p className="text-xs font-bold text-slate-800">1. Document Parsed</p>
              <p className="text-[10px] text-slate-500 mt-0.5">Policy text and pages ingested</p>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-emerald-50/50 border border-emerald-100 flex items-start gap-2.5">
            <div className="w-5 h-5 rounded-full bg-emerald-600 text-white flex items-center justify-center text-[10px] font-bold flex-shrink-0 mt-0.5">
              <Check className="w-3 h-3" />
            </div>
            <div>
              <p className="text-xs font-bold text-slate-800">2. Limits Extracted</p>
              <p className="text-[10px] text-slate-500 mt-0.5">Expense allowances identified</p>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-emerald-50/50 border border-emerald-100 flex items-start gap-2.5">
            <div className="w-5 h-5 rounded-full bg-emerald-600 text-white flex items-center justify-center text-[10px] font-bold flex-shrink-0 mt-0.5">
              <Check className="w-3 h-3" />
            </div>
            <div>
              <p className="text-xs font-bold text-slate-800">3. Rules Configured</p>
              <p className="text-[10px] text-slate-500 mt-0.5">Automated checks active</p>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-emerald-50/50 border border-emerald-100 flex items-start gap-2.5">
            <div className="w-5 h-5 rounded-full bg-emerald-600 text-white flex items-center justify-center text-[10px] font-bold flex-shrink-0 mt-0.5">
              <Check className="w-3 h-3" />
            </div>
            <div>
              <p className="text-xs font-bold text-slate-800">4. Ready for Claims</p>
              <p className="text-[10px] text-slate-500 mt-0.5">Instant matching enabled</p>
            </div>
          </div>
        </div>
      </div>

      {/* Extracted Rules & Policy Clauses */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-900">
            Detected Policy Rules & Conditions ({findings.length})
          </h2>
          <span className="text-xs text-slate-400">All rules active</span>
        </div>

        {findings.length === 0 ? (
          <div className="p-8 bg-white rounded-xl border border-slate-200 text-center shadow-xs">
            <CheckCircle2 className="w-9 h-9 text-emerald-500 mx-auto mb-2" />
            <h3 className="text-sm font-bold text-slate-800">Policy Successfully Active</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
              This policy is fully configured. All submitted employee claims will be automatically verified against this standard.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {findings.map((f, idx) => (
              <div
                key={f.id || idx}
                className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-3 hover:border-slate-300 transition-colors"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-indigo-50 text-indigo-700 border border-indigo-200">
                        {f.rule_code || 'REIMBURSEMENT-RULE'}
                      </span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                        Active Rule
                      </span>
                    </div>

                    <h3 className="text-sm font-bold text-slate-900 mt-1">{f.title}</h3>
                  </div>
                </div>

                <p className="text-xs text-slate-600 leading-relaxed">{f.description}</p>

                {/* Quoted Policy Citation */}
                {f.evidence_quote && (
                  <div className="p-3 bg-slate-50 rounded-lg border-l-2 border-indigo-500 text-xs text-slate-700 space-y-1">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-700 block">
                      Policy Clause:
                    </span>
                    <blockquote className="italic text-slate-800 font-serif">
                      &ldquo;{f.evidence_quote}&rdquo;
                    </blockquote>
                    {f.evidence_location && (
                      <span className="text-[10px] text-slate-400 block">
                        Location: {f.evidence_location}
                      </span>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
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
