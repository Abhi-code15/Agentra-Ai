import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../api/client';
import WorkflowLoopBanner from '../components/WorkflowLoopBanner';
import {
  FileText,
  Plus,
  Trash2,
  UploadCloud,
  ArrowLeft,
  DollarSign,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  Building2,
  FileCheck2,
} from 'lucide-react';

export default function NewClaim() {
  const navigate = useNavigate();

  // Organizations & Policies
  const [policies, setPolicies] = useState([]);
  const [loadingPolicies, setLoadingPolicies] = useState(true);

  // Form State
  const [companyName, setCompanyName] = useState('Acme Corporation');
  const [claimType, setClaimType] = useState('EXPENSE');
  const [selectedPolicyId, setSelectedPolicyId] = useState('');
  const [standardDocName, setStandardDocName] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [expenseDate, setExpenseDate] = useState(new Date().toISOString().split('T')[0]);
  const [currency, setCurrency] = useState('USD');

  // Itemized List
  const [lineItems, setLineItems] = useState([
    { category: 'Meals', description: '', amount: '', expense_date: new Date().toISOString().split('T')[0] },
  ]);

  // Uploaded Files
  const [uploadedDocuments, setUploadedDocuments] = useState([]);
  const [uploadingDoc, setUploadingDoc] = useState(false);

  // Submission State
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  // Load Company Policies
  useEffect(() => {
    const fetchPolicies = async () => {
      try {
        setLoadingPolicies(true);
        const res = await api.get('/policies?page=1&page_size=50');
        const list = res.data.data || [];
        setPolicies(list);

        if (list.length > 0) {
          const active = list.find((p) => p.status === 'ACTIVE') || list[0];
          setSelectedPolicyId(active.id);
          setStandardDocName(active.name);
        }
      } catch (err) {
        console.error('Failed to load company policies', err);
      } finally {
        setLoadingPolicies(false);
      }
    };
    fetchPolicies();
  }, []);

  // Sync selected policy name
  const handlePolicyChange = (policyId) => {
    setSelectedPolicyId(policyId);
    const found = policies.find((p) => p.id === policyId);
    if (found) {
      setStandardDocName(found.name);
    }
  };

  // Line item handlers
  const handleAddLineItem = () => {
    setLineItems([
      ...lineItems,
      { category: 'Meals', description: '', amount: '', expense_date: expenseDate },
    ]);
  };

  const handleRemoveLineItem = (index) => {
    if (lineItems.length === 1) return;
    setLineItems(lineItems.filter((_, i) => i !== index));
  };

  const handleLineItemChange = (index, field, value) => {
    const updated = [...lineItems];
    updated[index][field] = value;
    setLineItems(updated);
  };

  const totalAmount = lineItems.reduce((sum, it) => {
    const val = parseFloat(it.amount);
    return sum + (isNaN(val) ? 0 : val);
  }, 0);

  // Document Upload
  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    try {
      setUploadingDoc(true);
      setErrorMessage('');
      const formData = new FormData();
      formData.append('file', file);

      const res = await api.post('/documents', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const doc = res.data.data;
      setUploadedDocuments((prev) => [
        ...prev,
        {
          id: doc.id,
          filename: doc.original_filename,
          size: doc.file_size_bytes,
        },
      ]);
    } catch (err) {
      setErrorMessage(err.response?.data?.error?.message || 'Failed to upload document. Please try again.');
    } finally {
      setUploadingDoc(false);
      e.target.value = '';
    }
  };

  const handleRemoveDoc = (docId) => {
    setUploadedDocuments(uploadedDocuments.filter((d) => d.id !== docId));
  };

  // Submit Handler
  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setErrorMessage('');

    // Ensure valid numbers
    if (lineItems.some((it) => !it.amount || isNaN(parseFloat(it.amount)))) {
      setErrorMessage('Please provide a valid amount for each item.');
      setSubmitting(false);
      return;
    }

    try {
      const payload = {
        title,
        description: `${description ? description + ' | ' : ''}Company: ${companyName} | Standard: ${standardDocName || 'Default'}`,
        claim_type: claimType,
        policy_id: selectedPolicyId || null,
        expense_date: expenseDate,
        currency,
        line_items: lineItems.map((it) => ({
          category: it.category,
          description: it.description || 'Expense item',
          amount: parseFloat(it.amount),
          expense_date: it.expense_date,
        })),
        document_ids: uploadedDocuments.map((d) => d.id),
      };

      const res = await api.post('/claims', payload);
      const createdClaim = res.data.data;

      // Navigate to the check results page
      navigate(`/claims/${createdClaim.id}`);
    } catch (err) {
      setErrorMessage(err.response?.data?.error?.message || 'Failed to submit request. Please verify inputs.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-16">
      {/* Visual Workflow Loop */}
      <WorkflowLoopBanner role="USER" activeStep={2} />

      <div className="flex items-center justify-between">
        <Link to="/claims" className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-indigo-600">
          <ArrowLeft className="w-4 h-4" /> Back to My Reimbursements
        </Link>
      </div>

      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight">Submit New Reimbursement</h1>
        <p className="text-xs text-slate-500 mt-1">
          Submit your reimbursement claim for travel, meals, procurement, or business expenses. It will be automatically checked against company limits.
        </p>
      </div>

      {errorMessage && (
        <div className="p-3.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-500 flex-shrink-0" />
          {errorMessage}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Step 1: Company & Standard Specification */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-6 space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
            <span className="w-6 h-6 rounded-full bg-indigo-50 text-indigo-700 font-bold text-xs flex items-center justify-center">
              1
            </span>
            <h2 className="text-sm font-bold text-slate-900">Company & Policy Standard</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Company Name */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Company / Organization Name
              </label>
              <div className="relative">
                <Building2 className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  required
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  placeholder="e.g. Acme Corporation"
                  className="w-full pl-9 pr-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-800 focus:ring-2 focus:ring-indigo-500 focus:outline-hidden"
                />
              </div>
            </div>

            {/* Request Type */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Request Category
              </label>
              <select
                value={claimType}
                onChange={(e) => setClaimType(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-800 focus:ring-2 focus:ring-indigo-500 focus:outline-hidden bg-white"
              >
                <option value="EXPENSE">Expense Reimbursement</option>
                <option value="TRAVEL">Business Travel</option>
                <option value="PROCUREMENT">Purchase Order / Procurement</option>
                <option value="LEAVE">Leave Request</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
            {/* Standard Policy Document to check against */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Standard Document / Policy to Check Against
              </label>
              {loadingPolicies ? (
                <div className="px-3 py-2 text-xs text-slate-400 border border-slate-200 rounded-lg">
                  Loading standards...
                </div>
              ) : (
                <select
                  value={selectedPolicyId}
                  onChange={(e) => handlePolicyChange(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-800 focus:ring-2 focus:ring-indigo-500 focus:outline-hidden bg-white"
                >
                  {policies.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} {p.status === 'ACTIVE' ? '(Active Standard)' : ''}
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* Custom Standard Document Name Override */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Standard Reference Name
              </label>
              <input
                type="text"
                value={standardDocName}
                onChange={(e) => setStandardDocName(e.target.value)}
                placeholder="e.g. Employee Reimbursement Policy 2026 or CV Criteria"
                className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-800 focus:ring-2 focus:ring-indigo-500 focus:outline-hidden"
              />
            </div>
          </div>
        </div>

        {/* Step 2: Request Information */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-6 space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
            <span className="w-6 h-6 rounded-full bg-indigo-50 text-indigo-700 font-bold text-xs flex items-center justify-center">
              2
            </span>
            <h2 className="text-sm font-bold text-slate-900">Request Information</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <label className="block text-xs font-semibold text-slate-700 mb-1">Title / Purpose</label>
              <input
                type="text"
                required
                placeholder="e.g. Client Dinner - Acme Team"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-800 focus:ring-2 focus:ring-indigo-500 focus:outline-hidden"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Date</label>
              <input
                type="date"
                required
                value={expenseDate}
                onChange={(e) => setExpenseDate(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-800 focus:ring-2 focus:ring-indigo-500 focus:outline-hidden bg-white"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Notes / Description (Optional)</label>
            <textarea
              rows={2}
              placeholder="State the reason or details for this request..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-800 focus:ring-2 focus:ring-indigo-500 focus:outline-hidden"
            />
          </div>
        </div>

        {/* Step 3: Itemized Details & Amounts */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-indigo-50 text-indigo-700 font-bold text-xs flex items-center justify-center">
                3
              </span>
              <h2 className="text-sm font-bold text-slate-900">Items & Amounts ({lineItems.length})</h2>
            </div>

            <button
              type="button"
              onClick={handleAddLineItem}
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs font-semibold transition-colors"
            >
              <Plus className="w-3.5 h-3.5" /> Add Another Item
            </button>
          </div>

          <div className="space-y-3">
            {lineItems.map((item, idx) => (
              <div
                key={idx}
                className="grid grid-cols-12 gap-3 items-center bg-slate-50 p-3 rounded-lg border border-slate-200"
              >
                <div className="col-span-12 sm:col-span-3">
                  <label className="block text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
                    Category
                  </label>
                  <select
                    value={item.category}
                    onChange={(e) => handleLineItemChange(idx, 'category', e.target.value)}
                    className="w-full px-2.5 py-1.5 rounded-md border border-slate-300 text-xs bg-white text-slate-800 focus:ring-2 focus:ring-indigo-500 focus:outline-hidden"
                  >
                    <option value="Meals">Meals</option>
                    <option value="Lodging">Hotel / Lodging</option>
                    <option value="Transport">Transport / Taxi</option>
                    <option value="Flight">Airfare / Flight</option>
                    <option value="Office Supplies">Office Supplies</option>
                    <option value="General">Other / General</option>
                  </select>
                </div>

                <div className="col-span-12 sm:col-span-5">
                  <label className="block text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
                    Description
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Dinner with clients"
                    value={item.description}
                    onChange={(e) => handleLineItemChange(idx, 'description', e.target.value)}
                    className="w-full px-2.5 py-1.5 rounded-md border border-slate-300 text-xs text-slate-800 bg-white focus:ring-2 focus:ring-indigo-500 focus:outline-hidden"
                  />
                </div>

                <div className="col-span-10 sm:col-span-3">
                  <label className="block text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
                    Amount ($)
                  </label>
                  <div className="relative">
                    <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400 text-xs font-semibold">
                      $
                    </span>
                    <input
                      type="number"
                      step="0.01"
                      required
                      placeholder="0.00"
                      value={item.amount}
                      onChange={(e) => handleLineItemChange(idx, 'amount', e.target.value)}
                      className="w-full pl-6 pr-2.5 py-1.5 rounded-md border border-slate-300 text-xs font-semibold text-slate-800 bg-white focus:ring-2 focus:ring-indigo-500 focus:outline-hidden"
                    />
                  </div>
                </div>

                <div className="col-span-2 sm:col-span-1 flex items-end justify-center pt-4 sm:pt-0">
                  <button
                    type="button"
                    disabled={lineItems.length === 1}
                    onClick={() => handleRemoveLineItem(idx)}
                    className="p-1.5 text-slate-400 hover:text-rose-600 disabled:opacity-30 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="flex items-center justify-between p-3.5 bg-slate-100 rounded-lg border border-slate-200 mt-2">
            <span className="text-xs font-semibold text-slate-700">Total Request Amount:</span>
            <span className="text-base font-bold text-slate-900">
              ${totalAmount.toFixed(2)} {currency}
            </span>
          </div>
        </div>

        {/* Step 4: Supporting Bills & Files */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-6 space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
            <span className="w-6 h-6 rounded-full bg-indigo-50 text-indigo-700 font-bold text-xs flex items-center justify-center">
              4
            </span>
            <h2 className="text-sm font-bold text-slate-900">
              Upload Supporting Documents / Bills ({uploadedDocuments.length})
            </h2>
          </div>

          <div className="border-2 border-dashed border-slate-300 hover:border-indigo-400 rounded-xl p-6 text-center transition-colors">
            <input
              type="file"
              id="file-upload"
              accept=".pdf,.png,.jpg,.jpeg,.docx"
              onChange={handleFileUpload}
              className="hidden"
            />
            <label htmlFor="file-upload" className="cursor-pointer block">
              <UploadCloud className="w-8 h-8 text-indigo-600 mx-auto mb-2" />
              <p className="text-xs font-semibold text-slate-800">
                {uploadingDoc ? 'Uploading...' : 'Click to attach receipt, invoice, or CV document'}
              </p>
              <p className="text-[11px] text-slate-500 mt-0.5">Supports PDF, PNG, JPG, DOCX</p>
            </label>
          </div>

          {uploadedDocuments.length > 0 && (
            <div className="space-y-2 pt-1">
              {uploadedDocuments.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs"
                >
                  <div className="flex items-center gap-2 truncate">
                    <FileText className="w-4 h-4 text-indigo-600 flex-shrink-0" />
                    <span className="font-semibold text-slate-800 truncate">{doc.filename}</span>
                    <span className="text-slate-400 text-[11px]">({(doc.size / 1024).toFixed(1)} KB)</span>
                  </div>

                  <button
                    type="button"
                    onClick={() => handleRemoveDoc(doc.id)}
                    className="p-1 text-slate-400 hover:text-rose-600 rounded"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Submit Bar */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <Link
            to="/claims"
            className="px-4 py-2 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50"
          >
            Cancel
          </Link>

          <button
            type="submit"
            disabled={submitting}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs transition-colors disabled:opacity-50"
          >
            {submitting ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <FileCheck2 className="w-4 h-4" />
            )}
            {submitting ? 'Checking Against Rules...' : 'Submit & Check My Request'}
          </button>
        </div>
      </form>
    </div>
  );
}
