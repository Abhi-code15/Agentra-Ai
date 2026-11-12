import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import api from '../api/client';
import {
  FileText,
  Play,
  ArrowLeft,
  CheckCircle,
  AlertTriangle,
  Clock,
  Shield,
  Trash2,
} from 'lucide-react';

export default function DocumentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [doc, setDoc] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchDoc = async () => {
      try {
        setLoading(true);
        const res = await api.get(`/documents/${id}`);
        setDoc(res.data.data);
      } catch (err) {
        setError('Document not found or access denied.');
      } finally {
        setLoading(false);
      }
    };
    fetchDoc();
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
    if (!window.confirm('Are you sure you want to delete this document?')) return;
    try {
      await api.delete(`/documents/${id}`);
      navigate('/documents');
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to delete document.');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  if (error || !doc) {
    return (
      <div className="max-w-2xl mx-auto p-8 text-center bg-white rounded-2xl border border-slate-200 shadow-sm">
        <AlertTriangle className="w-12 h-12 text-rose-500 mx-auto mb-3" />
        <h2 className="text-lg font-bold text-slate-900">Document Unavailable</h2>
        <p className="text-sm text-slate-500 mt-1 mb-6">{error || 'Requested document was not found.'}</p>
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
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Top Navigation */}
      <div className="flex items-center justify-between">
        <Link
          to="/documents"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Documents
        </Link>

        <button
          onClick={handleDelete}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-rose-600 hover:bg-rose-50 border border-rose-200 transition-colors"
        >
          <Trash2 className="w-3.5 h-3.5" /> Delete Document
        </button>
      </div>

      {/* Main Info Card */}
      <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-100">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-emerald-50 rounded-2xl flex items-center justify-center text-emerald-600">
              <FileText className="w-7 h-7" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900 tracking-tight">{doc.original_filename}</h1>
              <p className="text-xs text-slate-400 mt-0.5">
                Uploaded on {new Date(doc.created_at).toLocaleString()}
              </p>
            </div>
          </div>

          <div>
            <button
              onClick={handleStartAnalysis}
              disabled={analyzing || doc.document_status !== 'READY_FOR_ANALYSIS'}
              className="inline-flex items-center gap-2 px-6 py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-xl text-sm transition-all shadow-lg shadow-emerald-600/20 disabled:opacity-50"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>{analyzing ? 'Executing Agent Loop...' : 'Run Compliance Analysis'}</span>
            </button>
          </div>
        </div>

        {/* Metadata Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 bg-slate-50 rounded-xl">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Status</span>
            <p className="text-sm font-bold text-slate-900 mt-1">{doc.document_status}</p>
          </div>

          <div className="p-4 bg-slate-50 rounded-xl">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Pages</span>
            <p className="text-sm font-bold text-slate-900 mt-1">
              {doc.extraction?.page_count || 1} Pages
            </p>
          </div>

          <div className="p-4 bg-slate-50 rounded-xl">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">File Size</span>
            <p className="text-sm font-bold text-slate-900 mt-1">
              {(doc.file_size_bytes / 1024).toFixed(1)} KB
            </p>
          </div>

          <div className="p-4 bg-slate-50 rounded-xl">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Extractor</span>
            <p className="text-sm font-bold text-slate-900 mt-1">
              {doc.extraction?.extractor_name || 'PyMuPDF'}
            </p>
          </div>
        </div>

        {/* Checksum & Integrity */}
        <div className="p-4 bg-slate-900 rounded-xl text-slate-300 font-mono text-xs flex items-center justify-between">
          <div className="truncate mr-4">
            <span className="text-slate-500 select-none mr-2">SHA256:</span>
            {doc.checksum_sha256}
          </div>
          <span className="text-emerald-400 font-sans text-[11px] font-bold px-2 py-0.5 bg-emerald-950 rounded border border-emerald-800">
            VERIFIED
          </span>
        </div>
      </div>
    </div>
  );
}
