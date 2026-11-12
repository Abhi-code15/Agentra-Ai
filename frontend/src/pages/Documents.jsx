import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import {
  FileText,
  UploadCloud,
  Search,
  ArrowRight,
  AlertCircle,
  CheckCircle,
} from 'lucide-react';

export default function Documents() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const fetchDocs = async () => {
    try {
      setLoading(true);
      const res = await api.get('/documents?page=1&page_size=50');
      setDocuments(res.data.data || []);
    } catch (err) {
      console.error('Failed to load documents', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    setUploadError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      await api.post('/documents', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      await fetchDocs();
    } catch (err) {
      setUploadError(
        err.response?.data?.error?.message || 'File upload failed. Ensure it is a valid PDF or DOCX file under 25MB.'
      );
    } finally {
      setUploading(false);
      e.target.value = ''; // Reset input
    }
  };

  const filteredDocs = documents.filter((doc) =>
    doc.original_filename.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Policy Documents</h1>
          <p className="text-sm text-slate-500 mt-1">
            Ingest and manage enterprise policies for compliance extraction
          </p>
        </div>

        {/* Upload Button */}
        <div>
          <label className="cursor-pointer inline-flex items-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-xl text-sm transition-all shadow-md shadow-emerald-600/20">
            <UploadCloud className="w-4 h-4" />
            <span>{uploading ? 'Parsing File...' : 'Upload PDF / DOCX'}</span>
            <input
              type="file"
              accept=".pdf,.docx"
              disabled={uploading}
              onChange={handleFileUpload}
              className="hidden"
            />
          </label>
        </div>
      </div>

      {uploadError && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-center gap-3 text-rose-700 text-xs">
          <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-600" />
          <span>{uploadError}</span>
        </div>
      )}

      {/* Search Bar */}
      <div className="relative">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
        <input
          type="text"
          placeholder="Search documents by filename..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 shadow-sm"
        />
      </div>

      {/* Documents Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600 mx-auto"></div>
          </div>
        ) : filteredDocs.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <FileText className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <p className="font-semibold text-sm">No documents found</p>
            <p className="text-xs text-slate-400 mt-1">Upload an expense reimbursement policy to begin analysis.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {filteredDocs.map((doc) => (
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
                      {(doc.file_size_bytes / 1024).toFixed(1)} KB • Ingested on{' '}
                      {new Date(doc.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-semibold ${
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
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
                  >
                    Inspect <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
