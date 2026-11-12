import React, { useEffect, useState } from 'react';
import api from '../api/client';
import { ShieldCheck, Search, Clock, User, Hash, Filter, Terminal, Check } from 'lucide-react';

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
        console.error('Failed to load audit events', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAuditEvents();
  }, [filterType]);

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="pb-2 border-b border-slate-200">
        <h1 className="text-xl font-bold text-slate-900 tracking-tight">Immutable Audit Ledger</h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Cryptographically attributed, tamper-evident audit trail for enterprise governance compliance
        </p>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => setFilterType('')}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
            filterType === ''
              ? 'bg-slate-900 text-white border-slate-900'
              : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
          }`}
        >
          All Audit Events
        </button>
        <button
          onClick={() => setFilterType('REVIEW_DECISION_SUBMITTED')}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
            filterType === 'REVIEW_DECISION_SUBMITTED'
              ? 'bg-indigo-600 text-white border-indigo-600'
              : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
          }`}
        >
          Review Decisions
        </button>
      </div>

      {/* Audit Table */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center">
            <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
            <p className="text-xs text-slate-400">Loading audit records...</p>
          </div>
        ) : events.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <ShieldCheck className="w-10 h-10 text-slate-300 mx-auto mb-2" />
            <p className="font-semibold text-xs text-slate-800">No Audit Records Found</p>
            <p className="text-xs text-slate-400 mt-0.5">
              Audit events will automatically appear as governance actions occur.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="py-3 px-4">Event Type</th>
                  <th className="py-3 px-4">Target Entity</th>
                  <th className="py-3 px-4">Actor</th>
                  <th className="py-3 px-4">Metadata Payload</th>
                  <th className="py-3 px-4 text-right">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {events.map((ev) => (
                  <React.Fragment key={ev.id}>
                    <tr
                      onClick={() => setExpandedRow(expandedRow === ev.id ? null : ev.id)}
                      className="hover:bg-slate-50/70 transition-colors cursor-pointer group"
                    >
                      <td className="py-3.5 px-4 font-semibold text-slate-900">
                        <span className="px-2 py-0.5 rounded bg-slate-100 font-mono text-[10px] text-slate-700 border border-slate-200">
                          {ev.event_type}
                        </span>
                      </td>

                      <td className="py-3.5 px-4 text-slate-600">
                        <span className="font-semibold text-slate-800 text-xs">{ev.entity_type}</span>
                        <p className="font-mono text-[10px] text-slate-400">ID: {ev.entity_id?.slice(0, 8)}...</p>
                      </td>

                      <td className="py-3.5 px-4 text-slate-600">
                        {ev.event_metadata?.reviewer_email ? (
                          <span className="font-medium text-slate-800 text-xs">
                            {ev.event_metadata.reviewer_email}
                          </span>
                        ) : (
                          <span className="font-mono text-[10px] text-slate-400">
                            {ev.actor_id ? `User: ${ev.actor_id.slice(0, 8)}` : 'System'}
                          </span>
                        )}
                      </td>

                      <td className="py-3.5 px-4 max-w-xs truncate font-mono text-[10px] text-slate-500">
                        {JSON.stringify(ev.event_metadata)}
                      </td>

                      <td className="py-3.5 px-4 text-right text-slate-500 font-mono text-[10px]">
                        {new Date(ev.created_at).toLocaleString()}
                      </td>
                    </tr>

                    {expandedRow === ev.id && (
                      <tr className="bg-slate-50/90">
                        <td colSpan={5} className="p-4">
                          <div className="p-3 bg-white rounded-lg border border-slate-200 font-mono text-xs text-slate-800 overflow-x-auto">
                            <span className="text-[10px] font-sans font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                              Raw Audit Event Record
                            </span>
                            <pre className="text-[11px] leading-relaxed whitespace-pre-wrap">
                              {JSON.stringify(ev, null, 2)}
                            </pre>
                          </div>
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
