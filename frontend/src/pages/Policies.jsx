import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import WorkflowLoopBanner from '../components/WorkflowLoopBanner';
import {
  FileCheck2,
  Plus,
  Search,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  Clock,
  Filter,
  UploadCloud,
  X,
  FileText,
} from 'lucide-react';

export default function Policies() {
  const { user } = useAuth();
  const isReviewer = user?.role === 'REVIEWER' || user?.role === 'ADMIN';

  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('ALL');

  // Form state
  const [policyName, setPolicyName] = useState('');
  const [policyCategory, setPolicyCategory] = useState('EXPENSE');
  const [policyDescription, setPolicyDescription] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);

  const fetchPolicies = async () => {
    try {
      setLoading(true);
      const res = await api.get('/policies?page=1&page_size=50');
      setPolicies(res.data.data || []);
    } catch (err) {
      console.error('Failed to load policies', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPolicies();
  }, []);

  const handleCreatePolicy = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setErrorMessage('');

    try {
      let documentId = null;

      // 1. If standard file attached, upload first
      if (selectedFile) {
        const formData = new FormData();
        formData.append('file', selectedFile);
        const uploadRes = await api.post('/documents', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        documentId = uploadRes.data.data.id;
      }

      // 2. Create Policy with attached document
      const queryParam = documentId ? `?document_id=${documentId}` : '';
      await api.post(`/policies${queryParam}`, {
        name: policyName,
        category: policyCategory,
        description: policyDescription,
      });

      setShowCreateModal(false);
      setPolicyName('');
      setPolicyDescription('');
      setSelectedFile(null);
      await fetchPolicies();
    } catch (err) {
      setErrorMessage(err.response?.data?.error?.message || 'Failed to create policy. Please verify inputs.');
    } finally {
      setSubmitting(false);
    }
  };

  const filteredPolicies = policies.filter((p) => {
    const matchesSearch =
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (p.description && p.description.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesCategory = categoryFilter === 'ALL' || p.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      {/* Visual Workflow Loop */}
      <WorkflowLoopBanner role={user?.role} activeStep={1} />

      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">
            Company Policies & Standards
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            {isReviewer
              ? 'Official company standards uploaded by finance reviewers. Approved rules set the spending allowances for claims.'
              : 'Official company reimbursement guidelines and spending allowances for employees.'}
          </p>
        </div>

        {isReviewer && (
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs transition-colors self-start sm:self-auto"
          >
            <Plus className="w-4 h-4" />
            <span>Upload New Policy</span>
          </button>
        )}
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search policies by name or keywords..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 rounded-lg border border-slate-300 bg-white text-xs text-slate-800 placeholder-slate-400 focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="text-xs border border-slate-300 rounded-lg px-2.5 py-1.5 bg-white text-slate-700 focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
          >
            <option value="ALL">All Categories</option>
            <option value="EXPENSE">Expense Reimbursement</option>
            <option value="TRAVEL">Travel & Lodging</option>
            <option value="LEAVE">Employee Leave</option>
            <option value="PROCUREMENT">Procurement / Purchase</option>
            <option value="HR">HR & Hiring Guidelines</option>
          </select>
        </div>
      </div>

      {/* Policies Grid */}
      {loading ? (
        <div className="py-20 text-center text-slate-400">
          <div className="inline-block w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-xs mt-2">Loading policies...</p>
        </div>
      ) : filteredPolicies.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 p-12 text-center bg-white">
          <FileCheck2 className="w-10 h-10 text-slate-300 mx-auto mb-3" />
          <h3 className="text-sm font-semibold text-slate-800">No Policies Found</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            Upload an official policy or guideline document (PDF/DOCX) to set limits and rules for employee claims.
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="mt-4 inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 text-white hover:bg-indigo-700 shadow-xs"
          >
            <Plus className="w-3.5 h-3.5" />
            Upload First Policy
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredPolicies.map((pol) => {
            const isActive = pol.status === 'ACTIVE';
            return (
              <div
                key={pol.id}
                className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs hover:border-slate-300 transition-colors flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-3 mb-2.5">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700 uppercase tracking-wide">
                      {pol.category}
                    </span>
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold border ${
                        isActive
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          : 'bg-amber-50 text-amber-700 border-amber-200'
                      }`}
                    >
                      {isActive ? (
                        <>
                          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                          <span>Active Standard</span>
                        </>
                      ) : (
                        <>
                          <Clock className="w-3 h-3 text-amber-600" />
                          <span>Draft</span>
                        </>
                      )}
                    </span>
                  </div>

                  <h3 className="text-sm font-bold text-slate-900 leading-snug">{pol.name}</h3>
                  <p className="text-xs text-slate-500 mt-1 line-clamp-2 leading-relaxed">
                    {pol.description || 'Standard policy defining limits and requirements.'}
                  </p>
                </div>

                <div className="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="text-[11px] text-slate-400">
                    {pol.versions_count || 1} Version{(pol.versions_count || 1) > 1 ? 's' : ''}
                  </span>

                  <Link
                    to={`/policies/${pol.id}`}
                    className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800"
                  >
                    <span>View Rules</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Create / Upload Policy Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="bg-white rounded-xl border border-slate-200 shadow-xl max-w-lg w-full overflow-hidden animate-in fade-in zoom-in-95 duration-100">
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <FileCheck2 className="w-4 h-4 text-indigo-600" />
                Upload Company Policy Document
              </h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-md"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreatePolicy} className="p-6 space-y-4">
              {errorMessage && (
                <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium">
                  {errorMessage}
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Policy Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Corporate Travel & Lodging Policy 2026"
                  value={policyName}
                  onChange={(e) => setPolicyName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-800 focus:ring-2 focus:ring-indigo-500 focus:outline-hidden"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Category</label>
                <select
                  value={policyCategory}
                  onChange={(e) => setPolicyCategory(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-800 focus:ring-2 focus:ring-indigo-500 focus:outline-hidden bg-white"
                >
                  <option value="EXPENSE">Expense Reimbursement</option>
                  <option value="TRAVEL">Travel & Lodging</option>
                  <option value="LEAVE">Employee Leave</option>
                  <option value="PROCUREMENT">Procurement & Equipment</option>
                  <option value="HR">HR & Hiring Guidelines / CV</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Description (Optional)</label>
                <textarea
                  rows={2}
                  placeholder="Brief summary of what this standard governs..."
                  value={policyDescription}
                  onChange={(e) => setPolicyDescription(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-800 focus:ring-2 focus:ring-indigo-500 focus:outline-hidden"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Upload Policy Document (PDF or DOCX)
                </label>
                <div className="border border-dashed border-slate-300 rounded-lg p-4 text-center hover:border-indigo-400 transition-colors">
                  <input
                    type="file"
                    id="policy-file"
                    accept=".pdf,.docx,.doc"
                    onChange={(e) => setSelectedFile(e.target.files[0])}
                    className="hidden"
                  />
                  <label htmlFor="policy-file" className="cursor-pointer block">
                    <UploadCloud className="w-6 h-6 text-indigo-600 mx-auto mb-1" />
                    <p className="text-xs font-medium text-slate-800">
                      {selectedFile ? selectedFile.name : 'Click to select official document file'}
                    </p>
                    <p className="text-[10px] text-slate-400 mt-0.5">PDF or Word document</p>
                  </label>
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs transition-colors disabled:opacity-50"
                >
                  {submitting ? 'Creating...' : 'Upload & Create Policy'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
