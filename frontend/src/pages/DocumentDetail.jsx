import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import api from '../api/client';
import AIChatDrawer from '../components/AIChatDrawer';
import {
  FileText,
  Play,
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Shield,
  Trash2,
  Sparkles,
  Copy,
  Check,
  Search,
  Bot,
  Send,
  ExternalLink,
  ChevronRight,
  ShieldAlert,
} from 'lucide-react';

export default function DocumentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [doc, setDoc] = useState(null);
  const [extractions, setExtractions] = useState([]);
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'text' | 'chat' | 'analyses'
  const [copiedSha, setCopiedSha] = useState(false);
  const [searchFilter, setSearchFilter] = useState('');
  const [isSideChatOpen, setIsSideChatOpen] = useState(false);

  // Embedded chat state
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  useEffect(() => {
    const fetchDocDetails = async () => {
      try {
        setLoading(true);
        const [docRes, extRes] = await Promise.all([
          api.get(`/documents/${id}`),
          api.get(`/documents/${id}/extractions`).catch(() => ({ data: { data: [] } })),
        ]);
        setDoc(docRes.data.data);
        const rawExt = extRes.data.data || [];
        setExtractions(rawExt);

        // Prepopulate welcome message for embedded chat
        setChatMessages([
          {
            role: 'assistant',
            content: `Hello! I have indexed **${docRes.data.data.original_filename}**. Ask me any question about approval limits, documentation mandates, or compliance conditions in this policy.`,
          },
        ]);
      } catch (err) {
        setError('Document not found or access denied.');
      } finally {
        setLoading(false);
      }
    };
    fetchDocDetails();
  }, [id]);

  const handleStartAnalysis = async () => {
    setAnalyzing(true);
    setError('');
    try {
      const res = await api.post(`/documents/${id}/analyze`);
      const runId = res.data.data.analysis_run_id;
      navigate(`/analyses/${runId}`);
    } catch (err) {
      setError(
        err.response?.data?.error?.message || 'Failed to initiate document compliance analysis.'
      );
      setAnalyzing(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to permanently delete this document?')) return;
    try {
      await api.delete(`/documents/${id}`);
      navigate('/documents');
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to delete document.');
    }
  };

  const copySha = () => {
    if (!doc?.checksum_sha256) return;
    navigator.clipboard.writeText(doc.checksum_sha256);
    setCopiedSha(true);
    setTimeout(() => setCopiedSha(false), 2000);
  };

  const handleSendEmbeddedChat = async (promptToSend = null) => {
    const text = promptToSend || chatInput.trim();
    if (!text || chatLoading) return;

    const userMsg = { role: 'user', content: text };
    const updated = [...chatMessages, userMsg];
    setChatMessages(updated);
    setChatInput('');
    setChatLoading(true);

    try {
      const historyToSend = updated
        .filter((_, idx) => idx > 0)
        .map((m) => ({ role: m.role, content: m.content }));

      const res = await api.post('/chat', {
        message: text,
        document_id: id,
        history: historyToSend,
      });

      setChatMessages([...updated, { role: 'assistant', content: res.data.data.reply }]);
    } catch (err) {
      setChatMessages([
        ...updated,
        {
          role: 'assistant',
          content: '⚠️ Failed to get answer from AI. Please check server connection.',
        },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-80 space-y-3">
        <div className="w-8 h-8 rounded-full border-2 border-indigo-600 border-t-transparent animate-spin"></div>
        <p className="text-xs font-medium text-slate-500">Loading document workspace...</p>
      </div>
    );
  }

  if (error || !doc) {
    return (
      <div className="max-w-xl mx-auto p-8 text-center bg-white rounded-xl border border-slate-200 shadow-sm mt-12">
        <div className="w-12 h-12 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center mx-auto mb-3">
          <AlertTriangle className="w-6 h-6" />
        </div>
        <h2 className="text-base font-semibold text-slate-900">Document Unavailable</h2>
        <p className="text-xs text-slate-500 mt-1 mb-6">{error || 'Requested document was not found.'}</p>
        <Link
          to="/documents"
          className="inline-flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded-lg text-xs font-medium hover:bg-slate-800 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Documents
        </Link>
      </div>
    );
  }

  const primaryExtraction = extractions.length > 0 ? extractions[0] : (doc?.extraction || null);
  const rawText = primaryExtraction?.extracted_text || doc?.extraction?.extracted_text || '';
  const filteredText = searchFilter
    ? rawText
        .split('\n')
        .filter((line) => line.toLowerCase().includes(searchFilter.toLowerCase()))
        .join('\n')
    : rawText;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Top Breadcrumb & Actions Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <Link to="/documents" className="hover:text-slate-900 transition-colors">
            Documents
          </Link>
          <ChevronRight className="w-3.5 h-3.5 text-slate-300" />
          <span className="font-medium text-slate-800 truncate max-w-xs">
            {doc.original_filename}
          </span>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => setIsSideChatOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 hover:text-indigo-600 transition-colors shadow-sm"
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
            <span>Ask AI Assistant</span>
          </button>

          <button
            onClick={handleStartAnalysis}
            disabled={analyzing}
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white transition-all shadow-xs disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {analyzing ? (
              <>
                <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Extracting Policy Rules...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Extract Policy Rules</span>
              </>
            )}
          </button>

          <button
            onClick={handleDelete}
            title="Delete Document"
            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 border border-slate-200 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Header Document Summary Card */}
      <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-start gap-4">
            <div className="w-11 h-11 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 flex-shrink-0">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2.5 flex-wrap">
                <h1 className="text-base font-semibold text-slate-900 leading-tight">
                  {doc.original_filename}
                </h1>
                <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200">
                  {doc.mime_type}
                </span>
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                  Ready to Verify Claims
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Uploaded on {new Date(doc.created_at).toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        {/* Metadata Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6 pt-6 border-t border-slate-100">
          <div className="bg-slate-50/70 p-3 rounded-lg border border-slate-100">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
              Pages
            </span>
            <span className="text-sm font-semibold text-slate-800 mt-0.5 block">
              {primaryExtraction?.page_count || 1} Pages
            </span>
          </div>

          <div className="bg-slate-50/70 p-3 rounded-lg border border-slate-100">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
              File Size
            </span>
            <span className="text-sm font-semibold text-slate-800 mt-0.5 block">
              {(doc.file_size_bytes / 1024).toFixed(1)} KB
            </span>
          </div>

          <div className="bg-slate-50/70 p-3 rounded-lg border border-slate-100">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
              Standard Format
            </span>
            <span className="text-sm font-semibold text-slate-800 mt-0.5 block">
              Company PDF Policy
            </span>
          </div>

          <div className="bg-slate-50/70 p-3 rounded-lg border border-slate-100">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
              Verification State
            </span>
            <div className="flex items-center gap-1.5 mt-0.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
              <span className="text-xs font-semibold text-emerald-700">Verified & Ingested</span>
            </div>
          </div>
        </div>

        {/* Checksum Snippet */}
        <div className="mt-3 flex items-center justify-between px-3 py-2 bg-slate-50 rounded-lg border border-slate-200/80 text-[11px] font-mono text-slate-600">
          <span className="truncate pr-2">SHA256: {doc.checksum_sha256}</span>
          <button
            onClick={copySha}
            className="flex items-center gap-1 text-[11px] font-sans text-indigo-600 hover:text-indigo-800 font-medium flex-shrink-0"
          >
            {copiedSha ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
            <span>{copiedSha ? 'Copied' : 'Copy'}</span>
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-slate-200">
        <nav className="flex space-x-6">
          <button
            onClick={() => setActiveTab('overview')}
            className={`pb-3 text-xs font-semibold border-b-2 transition-colors ${
              activeTab === 'overview'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            Document Overview
          </button>
          <button
            onClick={() => setActiveTab('text')}
            className={`pb-3 text-xs font-semibold border-b-2 transition-colors ${
              activeTab === 'text'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            Extracted Text Content ({rawText.length > 0 ? `${rawText.length} chars` : 'Empty'})
          </button>
          <button
            onClick={() => setActiveTab('chat')}
            className={`pb-3 text-xs font-semibold border-b-2 transition-colors flex items-center gap-1.5 ${
              activeTab === 'chat'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
            AI Document Q&A
          </button>
        </nav>
      </div>

      {/* Tab 1: Overview */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 space-y-6">
            <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-sm space-y-4">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Company Reimbursement Policy Standard
              </h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                This document serves as your company&apos;s reimbursement policy standard. Click <strong>Extract Policy Rules</strong> above to identify spending allowances, receipt requirements, and approval limits that will automatically evaluate employee claims.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                <div className="p-3.5 rounded-lg border border-slate-100 bg-slate-50/50">
                  <span className="text-[11px] font-semibold text-slate-700 block">1. Allowance & Rule Extraction</span>
                  <p className="text-[11px] text-slate-500 mt-1">
                    Detects daily meal limits, lodging caps, receipt mandates, and eligible categories from policy text.
                  </p>
                </div>

                <div className="p-3.5 rounded-lg border border-slate-100 bg-slate-50/50">
                  <span className="text-[11px] font-semibold text-slate-700 block">2. Automatic Claim Verification</span>
                  <p className="text-[11px] text-slate-500 mt-1">
                    Compares employee bills directly against company limits for instant verification and fast payout.
                  </p>
                </div>
              </div>
            </div>

            {/* Quick Preview of First 500 Chars */}
            <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Text Ingestion Preview
                </h3>
                <button
                  onClick={() => setActiveTab('text')}
                  className="text-xs font-medium text-indigo-600 hover:text-indigo-800"
                >
                  View Full Text →
                </button>
              </div>
              <div className="p-4 bg-slate-50 rounded-lg border border-slate-200/80 font-mono text-xs text-slate-700 whitespace-pre-wrap max-h-48 overflow-y-auto leading-relaxed">
                {rawText ? rawText.slice(0, 600) + '...' : 'No extracted text available.'}
              </div>
            </div>
          </div>

          {/* Right Column: Actions & Quick Q&A Trigger */}
          <div className="space-y-6">
            <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-sm space-y-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                AI Q&A Assistant
              </h3>
              <p className="text-xs text-slate-600">
                Have questions about approval limits, documentation mandates, or non-reimbursable clauses in this policy?
              </p>

              <div className="space-y-1.5 pt-1">
                {[
                  'What are the manager approval limits?',
                  'Are receipts required for small expenses?',
                  'What is the submission deadline?',
                ].map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setActiveTab('chat');
                      handleSendEmbeddedChat(q);
                    }}
                    className="w-full text-left px-3 py-2 rounded-lg text-xs bg-slate-50 hover:bg-indigo-50 hover:text-indigo-700 border border-slate-200 text-slate-600 transition-colors"
                  >
                    • {q}
                  </button>
                ))}
              </div>

              <button
                onClick={() => setActiveTab('chat')}
                className="w-full mt-2 py-2 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs font-semibold transition-colors flex items-center justify-center gap-1.5"
              >
                <Sparkles className="w-3.5 h-3.5" />
                Open AI Q&A Workspace
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Extracted Text Content */}
      {activeTab === 'text' && (
        <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-sm font-semibold text-slate-900">Extracted Policy Document Text</h3>
              <p className="text-xs text-slate-400">
                Generated by {primaryExtraction?.extractor_name || 'PyMuPDF'} • {rawText.length} Total Characters
              </p>
            </div>

            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                placeholder="Search extracted clauses..."
                className="pl-8 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-indigo-500 text-slate-800 w-64"
              />
            </div>
          </div>

          <div className="p-4 bg-slate-50 rounded-lg border border-slate-200/80 font-mono text-xs text-slate-800 whitespace-pre-wrap leading-relaxed max-h-[550px] overflow-y-auto">
            {filteredText || 'No text found matching filter.'}
          </div>
        </div>
      )}

      {/* Tab 3: Embedded AI Document Q&A */}
      {activeTab === 'chat' && (
        <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm flex flex-col h-[600px] overflow-hidden">
          {/* Chat Header */}
          <div className="px-5 py-3 border-b border-slate-100 flex items-center justify-between bg-slate-50">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-indigo-600 text-white flex items-center justify-center shadow-sm">
                <Bot className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-xs font-semibold text-slate-900">Document Intelligence Q&A</h4>
                <p className="text-[10px] text-slate-400">Grounded strictly on {doc.original_filename}</p>
              </div>
            </div>

            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
              Gemini 3.5 Active
            </span>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-5 space-y-4 bg-slate-50/40">
            {chatMessages.map((msg, idx) => {
              const isUser = msg.role === 'user';
              return (
                <div key={idx} className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
                  {!isUser && (
                    <div className="w-7 h-7 rounded-lg bg-indigo-600 text-white flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Bot className="w-4 h-4" />
                    </div>
                  )}

                  <div
                    className={`max-w-[80%] rounded-2xl p-4 text-xs leading-relaxed ${
                      isUser
                        ? 'bg-indigo-600 text-white rounded-br-sm shadow-sm'
                        : 'bg-white text-slate-800 border border-slate-200/80 rounded-bl-sm shadow-sm'
                    }`}
                  >
                    <div className="whitespace-pre-wrap">{msg.content}</div>
                  </div>
                </div>
              );
            })}

            {chatLoading && (
              <div className="flex gap-3 justify-start items-center">
                <div className="w-7 h-7 rounded-lg bg-indigo-600 text-white flex items-center justify-center flex-shrink-0">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="bg-white border border-slate-200 rounded-2xl rounded-bl-sm p-3.5 shadow-sm flex items-center gap-2 text-xs text-slate-500">
                  <div className="w-3 h-3 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
                  <span>Analyzing policy text and citing evidence...</span>
                </div>
              </div>
            )}
          </div>

          {/* Quick Prompts */}
          <div className="px-5 py-2 bg-white border-t border-slate-100 flex items-center gap-2 overflow-x-auto">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider flex-shrink-0">
              Quick Ask:
            </span>
            {[
              'What are the manager approval limits?',
              'Are receipts mandatory for all claims?',
              'What is the submission deadline?',
            ].map((q, idx) => (
              <button
                key={idx}
                onClick={() => handleSendEmbeddedChat(q)}
                className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-50 hover:bg-indigo-50 hover:text-indigo-700 border border-slate-200 text-slate-600 whitespace-nowrap transition-colors"
              >
                {q}
              </button>
            ))}
          </div>

          {/* Input Box */}
          <div className="p-4 bg-white border-t border-slate-200">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendEmbeddedChat();
              }}
              className="flex items-center gap-2"
            >
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Ask a question about this policy (e.g. 'Can managers approve travel over 10,000?')"
                disabled={chatLoading}
                className="flex-1 px-4 py-2.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-slate-900"
              />
              <button
                type="submit"
                disabled={!chatInput.trim() || chatLoading}
                className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold disabled:opacity-40 transition-colors shadow-sm flex items-center gap-1.5"
              >
                <Send className="w-3.5 h-3.5" />
                <span>Ask</span>
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Slide-Over Drawer Assistant */}
      <AIChatDrawer
        isOpen={isSideChatOpen}
        onClose={() => setIsSideChatOpen(false)}
        documentId={doc.id}
        documentTitle={doc.original_filename}
      />
    </div>
  );
}
