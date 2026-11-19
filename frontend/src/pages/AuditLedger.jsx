import React, { useEffect, useState } from 'react';
import api from '../api/client';
import { ShieldCheck, Clock, User, Filter, ChevronDown, ChevronUp } from 'lucide-react';

export default function AuditLedger() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState('');
  const [expandedRow, setExpandedRow] = useState(null);

  useEffect(() => {
    const fetchAuditEvents = async () => {
      try {
        setLoading(true);
        const url = filterType
          ? `/audit-events?event_type=${filterType}&page=1&page_size=50`
          : `/audit-events?page=1&page_size=50`;
        const res = await api.get(url);
        setEvents(res.data.data || []);
      } catch (err) {
        console.error('Failed to load activity records', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAuditEvents();
  }, [filterType]);

  const formatEventName = (type) => {
    switch (type) {
      case 'REVIEW_DECISION_SUBMITTED':
        return 'Review Decision';
      case 'CLAIM_SUBMITTED':
        return 'New Request Submitted';
      case 'CLAIM_EVALUATED':
        return 'Rules Checked';
      case 'POLICY_CREATED':
        return 'Policy Created';
      case 'POLICY_VERSION_ACTIVATED':
        return 'Policy Activated';
      case 'DOCUMENT_UPLOADED':
        return 'File Uploaded';
      default:
        return type.replace(/_/g, ' ');
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-12">
      {/* Header */}
      <div className="pb-3 border-b border-slate-200">
        <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-indigo-600" />
          Activity History
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          History of all policy updates, employee submissions, and reviewer decisions.
        </p>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => setFilterType('')}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors ${
            filterType === ''
              ? 'bg-slate-900 text-white border-slate-900'
              : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
          }`}
        >
          All Activity
        </button>
        <button
          onClick={() => setFilterType('REVIEW_DECISION_SUBMITTED')}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors ${
            filterType === 'REVIEW_DECISION_SUBMITTED'
              ? 'bg-indigo-600 text-white border-indigo-600'
              : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
          }`}
        >
          Review Decisions
        </button>
      </div>

      {/* Audit Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        {loading ? (
          <div className="py-16 text-center text-slate-400 text-xs">
            <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            <p>Loading activity history...</p>
          </div>
        ) : events.length === 0 ? (
          <div className="py-16 text-center text-slate-400 text-xs">
            <ShieldCheck className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="font-semibold text-slate-700">No Activity Recorded Yet</p>
            <p className="mt-0.5">Actions will be logged here as users and reviewers interact with the platform.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="py-3 px-4">Action</th>
                  <th className="py-3 px-4">Item Type</th>
                  <th className="py-3 px-4">Performed By</th>
                  <th className="py-3 px-4">Summary</th>
                  <th className="py-3 px-4 text-right">Date & Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {events.map((ev) => (
                  <React.Fragment key={ev.id}>
                    <tr
                      onClick={() => setExpandedRow(expandedRow === ev.id ? null : ev.id)}
                      className="hover:bg-slate-50/70 transition-colors cursor-pointer"
                    >
                      <td className="py-3.5 px-4 font-bold text-slate-900">
                        <span className="px-2 py-0.5 rounded bg-slate-100 text-[11px] text-slate-800">
                          {formatEventName(ev.event_type)}
                        </span>
                      </td>

                      <td className="py-3.5 px-4 font-medium text-slate-700 capitalize">
                        {ev.entity_type}
                      </td>

                      <td className="py-3.5 px-4 text-slate-600">
                        {ev.actor?.full_name || 'System / User'}
                      </td>

                      <td className="py-3.5 px-4 text-slate-500 max-w-xs truncate">
                        {ev.event_metadata ? (
                          ev.event_metadata.decision ? (
                            <span className="font-semibold text-slate-800">
                              Decision: {ev.event_metadata.decision}
                            </span>
                          ) : (
                            JSON.stringify(ev.event_metadata).slice(0, 50) + '...'
                          )
                        ) : (
                          'Recorded action'
                        )}
                      </td>

                      <td className="py-3.5 px-4 text-right text-slate-400">
                        {new Date(ev.timestamp).toLocaleString()}
                      </td>
                    </tr>

                    {expandedRow === ev.id && (
                      <tr className="bg-slate-50">
                        <td colSpan={5} className="p-4 border-t border-slate-100">
                          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                            Action Details
                          </span>
                          <pre className="text-[11px] font-mono bg-white p-3 rounded-lg border border-slate-200 text-slate-700 overflow-x-auto">
                            {JSON.stringify(ev.event_metadata, null, 2)}
                          </pre>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
