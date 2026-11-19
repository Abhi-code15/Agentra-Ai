import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import WorkflowLoopBanner from '../components/WorkflowLoopBanner';
import {
  FileText,
  ArrowLeft,
  Sparkles,
  CheckCircle2,
  XCircle,
  Edit3,
  ShieldCheck,
  AlertCircle,
  Clock,
  BookOpen,
  DollarSign,
  Receipt,
  Layers,
  X,
  RefreshCw,
  PlusCircle,
  Check,
} from 'lucide-react';

export default function PolicyDetail() {
  const { id: policyId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const isReviewer = user?.role === 'REVIEWER' || user?.role === 'ADMIN';

  const [policy, setPolicy] = useState(null);
  const [selectedVersionId, setSelectedVersionId] = useState(null);
  const [versionDetail, setVersionDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [extracting, setExtracting] = useState(false);
  const [activating, setActivating] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  // Edit Rule Modal State
  const [editingRule, setEditingRule] = useState(null);
  const [editForm, setEditForm] = useState({
    rule_name: '',
    description: '',
    limit_amount: '',
    currency: 'USD',
    mandatory_receipt: false,
    severity: 'MEDIUM',
  });
  const [savingRule, setSavingRule] = useState(false);

  // Fetch Policy Overview
  const fetchPolicy = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/policies/${policyId}`);
      const data = res.data?.data;
      setPolicy(data);

      if (data && data.versions && data.versions.length > 0) {
        const activeVer = data.versions.find((v) => v.status === 'ACTIVE') || data.versions[0];
        setSelectedVersionId(activeVer.id);
      }
    } catch (err) {
      setErrorMessage(err.response?.data?.error?.message || 'Failed to load policy details.');
    } finally {
      setLoading(false);
    }
  };

  // Fetch Version Details (rules & source)
  const fetchVersionDetail = async (versionId) => {
    if (!versionId) return;
    try {
      const res = await api.get(`/policies/versions/${versionId}`);
      setVersionDetail(res.data?.data || null);
    } catch (err) {
      console.error('Failed to load version rules', err);
    }
  };

  useEffect(() => {
    fetchPolicy();
  }, [policyId]);

  useEffect(() => {
    if (selectedVersionId) {
      fetchVersionDetail(selectedVersionId);
    }
  }, [selectedVersionId]);

  // AI Rule Extraction
  const handleExtractRules = async () => {
    if (!selectedVersionId) return;
    try {
      setExtracting(true);
      setErrorMessage('');
      setSuccessMessage('');
      const res = await api.post(`/policies/versions/${selectedVersionId}/extract`);
      const extractedCount = res.data?.data?.length || 0;
      setSuccessMessage(`Successfully extracted ${extractedCount} policy rules.`);
      await fetchVersionDetail(selectedVersionId);
      await fetchPolicy();
    } catch (err) {
      setErrorMessage(err.response?.data?.error?.message || 'Failed to extract rules from document.');
    } finally {
      setExtracting(false);
    }
  };

  // Rule Approval
  const handleApproveRule = async (ruleId, decision) => {
    try {
      setErrorMessage('');
      await api.post(`/policies/rules/${ruleId}/approve?decision=${decision}`);
      await fetchVersionDetail(selectedVersionId);
    } catch (err) {
      setErrorMessage(err.response?.data?.error?.message || `Failed to ${decision.toLowerCase()} rule.`);
    }
  };

  // Activate Version as Active Standard
  const handleActivateVersion = async () => {
    if (!selectedVersionId) return;
    try {
      setActivating(true);
      setErrorMessage('');
      setSuccessMessage('');
      await api.post(`/policies/versions/${selectedVersionId}/activate`);
      setSuccessMessage('This version is now the active company standard!');
      await fetchPolicy();
      await fetchVersionDetail(selectedVersionId);
    } catch (err) {
      setErrorMessage(err.response?.data?.error?.message || 'Failed to activate policy standard.');
    } finally {
      setActivating(false);
    }
  };

  // Safe accessor helpers
  const getRuleLimit = (rule) => {
    const val = rule.limit_amount ?? rule.rule_definition?.value ?? rule.rule_definition?.limit ?? rule.rule_definition?.max_amount;
    if (val === null || val === undefined || val === '') return null;
    const num = typeof val === 'number' ? val : parseFloat(val);
    return !isNaN(num) ? num : null;
  };

  const getRuleCurrency = (rule) => {
    return rule.currency || rule.rule_definition?.currency || 'USD';
  };

  const isRuleMandatoryReceipt = (rule) => {
    return !!(rule.mandatory_receipt || rule.rule_definition?.mandatory_receipt || rule.rule_type === 'MANDATORY_DOCUMENTATION' || rule.category === 'DOCUMENTATION');
  };

  const getRuleQuote = (rule) => {
    return rule.source_quote || rule.source_reference?.quote || rule.source_reference?.text || null;
  };

  const getRuleDays = (rule) => {
    return rule.timeliness_days ?? rule.rule_definition?.days ?? rule.rule_definition?.deadline_days ?? null;
  };

  const isRuleApproved = (rule) => {
    return rule.approval_status === 'APPROVED' || !!rule.is_approved;
  };

  const handleOpenEdit = (rule) => {
    setEditingRule(rule);
    const limitNum = getRuleLimit(rule);
    setEditForm({
      rule_name: rule.name || rule.rule_name || '',
      description: rule.description || '',
      limit_amount: limitNum !== null ? limitNum : '',
      currency: getRuleCurrency(rule),
      mandatory_receipt: isRuleMandatoryReceipt(rule),
      severity: rule.severity || 'MEDIUM',
    });
  };

  const handleSaveRule = async (e) => {
    e.preventDefault();
    if (!editingRule) return;
    try {
      setSavingRule(true);
      const parsedLimit = editForm.limit_amount === '' ? null : parseFloat(editForm.limit_amount);
      await api.put(`/policies/rules/${editingRule.id}`, {
        name: editForm.rule_name,
        description: editForm.description,
        rule_definition: {
          ...(editingRule.rule_definition || {}),
          value: parsedLimit,
          currency: editForm.currency,
          mandatory_receipt: editForm.mandatory_receipt,
        },
      });
      setEditingRule(null);
      await fetchVersionDetail(selectedVersionId);
    } catch (err) {
      setErrorMessage(err.response?.data?.error?.message || 'Failed to update rule.');
    } finally {
      setSavingRule(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[350px] text-slate-400">
        <RefreshCw className="w-6 h-6 animate-spin text-indigo-600 mb-2" />
        <p className="text-xs">Loading policy rules...</p>
      </div>
    );
  }

  if (!policy) {
    return (
      <div className="max-w-4xl mx-auto py-12 text-center">
        <h2 className="text-base font-bold text-slate-900 mb-2">Policy Not Found</h2>
        <p className="text-xs text-slate-500 mb-4">{errorMessage || 'The requested policy could not be found.'}</p>
        <Link
          to="/policies"
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-600 text-white rounded-lg text-xs font-semibold"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Policies
        </Link>
      </div>
    );
  }

  const selectedVersion =
    policy.versions?.find((v) => v.id === selectedVersionId) ||
    policy.versions?.[0] ||
    null;

  const rulesList = versionDetail?.rules || [];
  const approvedCount = rulesList.filter(isRuleApproved).length;
  const unverifiedCount = rulesList.length - approvedCount;

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-16">
      {/* Workflow Stepper Loop */}
      <WorkflowLoopBanner role={user?.role} activeStep={2} />

      <div className="flex items-center justify-between">
        <Link
          to="/policies"
          className="inline-flex items-center gap-1 text-xs font-semibold text-slate-500 hover:text-indigo-600 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Company Policies
        </Link>
      </div>

      {errorMessage && (
        <div className="p-3.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-500 flex-shrink-0" />
          {errorMessage}
        </div>
      )}
      {successMessage && (
        <div className="p-3.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-medium flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
          {successMessage}
        </div>
      )}

      {/* Main Policy Header Card */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-6">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 pb-5 border-b border-slate-100">
          <div className="space-y-1.5 flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="px-2.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-indigo-50 text-indigo-700 border border-indigo-200">
                {policy.category}
              </span>
              <span
                className={`px-2.5 py-0.5 rounded text-[10px] font-semibold ${
                  policy.status === 'ACTIVE'
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                    : 'bg-slate-100 text-slate-700 border border-slate-200'
                }`}
              >
                {policy.status === 'ACTIVE' ? 'Active Standard' : 'Draft'}
              </span>
            </div>

            <h1 className="text-xl font-bold text-slate-900 tracking-tight">{policy.name}</h1>
            <p className="text-xs text-slate-600 max-w-2xl">
              {policy.description || 'Company standard defining rules and limits for employee claims.'}
            </p>
          </div>

          {/* Action Buttons for Reviewers */}
          {isReviewer && (
            <div className="flex items-center gap-2 flex-shrink-0">
              <button
                onClick={handleExtractRules}
                disabled={extracting || !selectedVersionId}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 text-xs font-semibold transition-colors disabled:opacity-50"
              >
                {extracting ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                )}
                {extracting ? 'Extracting Rules...' : 'Extract Rules with AI'}
              </button>

              {selectedVersion && selectedVersion.status !== 'ACTIVE' && (
                <button
                  onClick={handleActivateVersion}
                  disabled={activating}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-xs transition-colors disabled:opacity-50"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  {activating ? 'Activating...' : 'Set as Active Standard'}
                </button>
              )}
            </div>
          )}
        </div>

        {/* Version Switcher Tabs */}
        {policy.versions && policy.versions.length > 0 && (
          <div className="pt-4 flex items-center justify-between flex-wrap gap-2 text-xs">
            <div className="flex items-center gap-2">
              <Layers className="w-3.5 h-3.5 text-slate-400" />
              <span className="font-semibold text-slate-600">Versions:</span>
              <div className="flex items-center gap-1">
                {policy.versions.map((ver) => (
                  <button
                    key={ver.id}
                    onClick={() => setSelectedVersionId(ver.id)}
                    className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                      selectedVersionId === ver.id
                        ? 'bg-slate-900 text-white'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    v{ver.version_number}.0 {ver.status === 'ACTIVE' && '★ Active'}
                  </button>
                ))}
              </div>
            </div>

            {selectedVersion?.document_filename && (
              <div className="flex items-center gap-1.5 text-slate-500 text-[11px]">
                <FileText className="w-3.5 h-3.5 text-indigo-500" />
                <span>
                  Attached Standard Document:{' '}
                  <strong className="text-slate-700">{selectedVersion.document_filename}</strong>
                </span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Rules Table / Card View */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div>
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-indigo-600" />
              Company Rules & Limits ({rulesList.length})
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              These approved rules are used to check employee requests automatically.
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs">
            <span className="px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-semibold">
              {approvedCount} Approved
            </span>
            <span className="px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200 font-semibold">
              {unverifiedCount} Unverified
            </span>
          </div>
        </div>

        {rulesList.length === 0 ? (
          <div className="py-16 text-center text-slate-500 text-xs px-4">
            <BookOpen className="w-10 h-10 mx-auto mb-3 text-slate-300" />
            <h3 className="font-bold text-slate-800 text-sm">No Rules Extracted Yet</h3>
            <p className="mt-1 mb-4 text-slate-500 max-w-md mx-auto">
              This policy standard is currently in draft. You can click &quot;Extract Rules with AI&quot; to parse clauses and spending limits from the policy document.
            </p>
            {isReviewer && selectedVersionId && (
              <button
                onClick={handleExtractRules}
                disabled={extracting}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs transition-colors"
              >
                <Sparkles className="w-4 h-4" />
                {extracting ? 'Extracting...' : 'Extract Rules with AI'}
              </button>
            )}
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {rulesList.map((rule) => {
              const ruleLimit = getRuleLimit(rule);
              const ruleCurrency = getRuleCurrency(rule);
              const reqReceipt = isRuleMandatoryReceipt(rule);
              const sourceQuote = getRuleQuote(rule);
              const deadlineDays = getRuleDays(rule);
              const approved = isRuleApproved(rule);

              return (
                <div key={rule.id} className="p-5 hover:bg-slate-50/50 transition-colors">
                  <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                    <div className="space-y-1.5 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-mono text-xs font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">
                          {rule.rule_code}
                        </span>
                        <h4 className="text-sm font-bold text-slate-900">{rule.name || rule.rule_name}</h4>
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700 uppercase">
                          {rule.category}
                        </span>
                      </div>

                      <p className="text-xs text-slate-600 leading-relaxed">{rule.description}</p>

                      <div className="flex items-center gap-3 pt-1 text-xs text-slate-700 flex-wrap">
                        {ruleLimit !== null && (
                          <div className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-100 font-medium">
                            <DollarSign className="w-3.5 h-3.5 text-emerald-600" />
                            <span>
                              Max Limit: <strong>${ruleLimit.toFixed(2)} {ruleCurrency}</strong>
                            </span>
                          </div>
                        )}
                        <div className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-100 font-medium">
                          <Receipt className="w-3.5 h-3.5 text-indigo-600" />
                          <span>
                            Receipt Required: <strong>{reqReceipt ? 'Yes' : 'No'}</strong>
                          </span>
                        </div>
                        {deadlineDays && (
                          <div className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-100 font-medium">
                            <Clock className="w-3.5 h-3.5 text-amber-600" />
                            <span>
                              Submit Within: <strong>{deadlineDays} Days</strong>
                            </span>
                          </div>
                        )}
                      </div>

                      {sourceQuote && (
                        <div className="mt-2.5 p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs">
                          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                            Document Citation:
                          </span>
                          <p className="italic text-slate-700 font-serif leading-relaxed">
                            &ldquo;{sourceQuote}&rdquo;
                          </p>
                        </div>
                      )}
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2 flex-shrink-0 pt-1">
                      {approved ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Approved
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                          <Clock className="w-3.5 h-3.5" /> Pending Approval
                        </span>
                      )}

                      {isReviewer && (
                        <div className="flex items-center gap-1.5">
                          <button
                            onClick={() => handleOpenEdit(rule)}
                            className="px-2.5 py-1 rounded-md text-xs font-medium text-slate-700 bg-white hover:bg-slate-100 border border-slate-300 flex items-center gap-1"
                          >
                            <Edit3 className="w-3 h-3" /> Edit
                          </button>

                          {!approved ? (
                            <button
                              onClick={() => handleApproveRule(rule.id, 'APPROVED')}
                              className="px-2.5 py-1 rounded-md text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 flex items-center gap-1 shadow-xs"
                            >
                              <CheckCircle2 className="w-3 h-3" /> Approve
                            </button>
                          ) : (
                            <button
                              onClick={() => handleApproveRule(rule.id, 'REJECTED')}
                              className="px-2.5 py-1 rounded-md text-xs font-medium text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 flex items-center gap-1"
                            >
                              <XCircle className="w-3 h-3" /> Reject
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Edit Rule Modal */}
      {editingRule && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="bg-white rounded-xl border border-slate-200 shadow-xl max-w-lg w-full overflow-hidden animate-in fade-in zoom-in-95 duration-100">
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Edit3 className="w-4 h-4 text-indigo-600" />
                Edit Rule: {editingRule.rule_code}
              </h3>
              <button
                onClick={() => setEditingRule(null)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-md"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSaveRule} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Rule Name</label>
                <input
                  type="text"
                  required
                  value={editForm.rule_name}
                  onChange={(e) => setEditForm({ ...editForm, rule_name: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-indigo-500 focus:outline-hidden"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Description</label>
                <textarea
                  rows={2}
                  value={editForm.description}
                  onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-indigo-500 focus:outline-hidden"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Limit Amount</label>
                  <input
                    type="number"
                    step="0.01"
                    placeholder="No limit"
                    value={editForm.limit_amount}
                    onChange={(e) => setEditForm({ ...editForm, limit_amount: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-indigo-500 focus:outline-hidden"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Currency</label>
                  <input
                    type="text"
                    value={editForm.currency}
                    onChange={(e) => setEditForm({ ...editForm, currency: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-indigo-500 focus:outline-hidden"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="mandatory_receipt"
                  checked={editForm.mandatory_receipt}
                  onChange={(e) => setEditForm({ ...editForm, mandatory_receipt: e.target.checked })}
                  className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 h-4 w-4"
                />
                <label htmlFor="mandatory_receipt" className="text-xs font-medium text-slate-700">
                  Mandatory bill or receipt required for this rule
                </label>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setEditingRule(null)}
                  className="px-4 py-2 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingRule}
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs"
                >
                  {savingRule ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
