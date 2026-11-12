import React, { useEffect, useState } from 'react';
import api from '../api/client';
import { ShieldCheck, Search, Clock, User, Hash } from 'lucide-react';

export default function AuditLedger() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState('');

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
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Immutable Audit Ledger</h1>
        <p className="text-sm text-slate-500 mt-1">
          Cryptographically attributed, tamper-evident audit trail for enterprise governance compliance
        </p>
      </div>

      {/* Filter Chips */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => setFilterType('')}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors ${
            filterType === ''
              ? 'bg-slate-900 text-white border-slate-900'
              : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
          }`}
        >
          All Events
        </button>
        <button
          onClick={() => setFilterType('REVIEW_DECISION_SUBMITTED')}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors ${
            filterType === 'REVIEW_DECISION_SUBMITTED'
              ? 'bg-emerald-600 text-white border-emerald-600'
              : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
          }`}
        >
          Review Decisions
        </button>
      </div>

      {/* Audit Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600 mx-auto"></div>
          </div>
        ) : events.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <ShieldCheck className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <p className="font-semibold text-sm">No Audit Records Found</p>
            <p className="text-xs text-slate-400 mt-1">Audit events will automatically appear as governance actions occur.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Event Type</th>
                  <th className="py-3 px-4">Entity</th>
                  <th className="py-3 px-4">Actor</th>
                  <th className="py-3 px-4">Metadata</th>
                  <th className="py-3 px-4 text-right">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-sans">
                {events.map((ev) => (
                  <tr key={ev.id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="py-3.5 px-4 font-semibold text-slate-900">
                      <span className="px-2 py-0.5 rounded bg-slate-100 font-mono text-[11px] text-slate-700">
                        {ev.event_type}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-600">
                      <span className="font-semibold text-slate-800">{ev.entity_type}</span>
                      <p className="font-mono text-[10px] text-slate-400">{ev.entity_id?.slice(0, 8)}</p>
                    </td>
                    <td className="py-3.5 px-4 text-slate-600">
                      {ev.event_metadata?.reviewer_email ? (
                        <span className="font-medium text-slate-800">
                          {ev.event_metadata.reviewer_email}
                        </span>
                      ) : (
                        <span className="font-mono text-[10px] text-slate-400">
                          {ev.actor_id ? ev.actor_id.slice(0, 8) : 'System'}
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 max-w-xs truncate font-mono text-[10px] text-slate-500">
                      {JSON.stringify(ev.event_metadata)}
                    </td>
                    <td className="py-3.5 px-4 text-right text-slate-500 font-mono text-[11px]">
                      {new Date(ev.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
