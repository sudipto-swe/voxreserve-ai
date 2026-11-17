import React, { useEffect, useState } from 'react';
import { Calendar, Wrench, XCircle, Table as TableIcon, RefreshCw, CheckCircle2, Clock } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { API_BASE_URL } from '../config/api';

export const AdminDashboard: React.FC = () => {
  const [analytics, setAnalytics] = useState<any>(null);
  const [conversations, setConversations] = useState<any[]>([]);
  const [tables, setTables] = useState<any[]>([]);
  const [selectedConv, setSelectedConv] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeAdminTab, setActiveAdminTab] = useState<'overview' | 'tables' | 'conversations'>('overview');
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadData = () => {
    setLoading(true);
    Promise.all([
      fetch(`${API_BASE_URL}/api/admin/analytics`).then(r => r.json()),
      fetch(`${API_BASE_URL}/api/admin/conversations`).then(r => r.json()),
      fetch(`${API_BASE_URL}/api/admin/tables`).then(r => r.json())
    ]).then(([ana, convs, tbls]) => {
      setAnalytics(ana);
      setConversations(convs);
      setTables(tbls);
      setLoading(false);
    }).catch(err => {
      console.error("Failed to load admin stats", err);
      setLoading(false);
    });
  };

  useEffect(() => {
    loadData();
  }, []);

  const loadConversationDetails = async (id: string) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/admin/conversations/${id}`);
      const data = await res.json();
      setSelectedConv(data);
    } catch (e) {
      console.error("Error inspecting conversation", e);
    }
  };

  const handleCancelReservation = async (code: string, phone: string) => {
    if (!window.confirm(`Are you sure you want to cancel booking ${code}?`)) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/reservations/cancel`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ booking_code: code, customer_phone: phone, reason: "Cancelled by Admin Host" })
      });
      const data = await res.json();
      if (res.ok) {
        setActionMessage(`Reservation ${code} successfully cancelled.`);
        loadData();
      } else {
        alert(data.detail || "Cancellation failed");
      }
    } catch (e: any) {
      alert("Error: " + e.message);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-xs text-stone-500">Loading operational telemetry...</div>;
  }

  const chartData = [
    { time: '5 PM', count: 2 },
    { time: '6 PM', count: 4 },
    { time: '7 PM', count: 8 },
    { time: '8 PM', count: 6 },
    { time: '9 PM', count: 3 },
    { time: '10 PM', count: 1 }
  ];

  return (
    <div className="space-y-6">
      {/* Admin Action Notification */}
      {actionMessage && (
        <div className="p-3 bg-emerald-950/60 border border-emerald-800 rounded-xl text-xs text-emerald-300 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>{actionMessage}</span>
          </div>
          <button onClick={() => setActionMessage(null)} className="underline text-emerald-200">Dismiss</button>
        </div>
      )}

      {/* Header with Sub-tabs and Refresh */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-stone-800">
        <div>
          <h3 className="text-xl font-bold text-white tracking-wide">Restaurant Host & Operations Center</h3>
          <p className="text-xs text-stone-400">Live PostgreSQL bookings, table statuses, and AI telemetry</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex bg-stone-900 border border-stone-800 rounded-lg p-1 text-xs">
            <button
              onClick={() => setActiveAdminTab('overview')}
              className={`px-3 py-1 rounded-md transition ${activeAdminTab === 'overview' ? 'bg-rose-600 text-white font-medium' : 'text-stone-400 hover:text-white'}`}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveAdminTab('tables')}
              className={`px-3 py-1 rounded-md transition ${activeAdminTab === 'tables' ? 'bg-rose-600 text-white font-medium' : 'text-stone-400 hover:text-white'}`}
            >
              Tables ({tables.length})
            </button>
            <button
              onClick={() => setActiveAdminTab('conversations')}
              className={`px-3 py-1 rounded-md transition ${activeAdminTab === 'conversations' ? 'bg-rose-600 text-white font-medium' : 'text-stone-400 hover:text-white'}`}
            >
              AI Logs ({conversations.length})
            </button>
          </div>
          <button
            onClick={loadData}
            className="p-2 bg-stone-800 hover:bg-stone-700 text-stone-300 rounded-lg border border-stone-700 transition"
            title="Refresh Ledger"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-stone-900 border border-stone-800 p-5 rounded-xl shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-stone-400">Total Reservations</span>
            <Calendar className="w-4 h-4 text-rose-500" />
          </div>
          <p className="text-2xl font-bold text-white mt-2">{analytics?.total_reservations || 0}</p>
          <span className="text-[11px] text-emerald-400">{analytics?.confirmed_reservations || 0} Confirmed</span>
        </div>

        <div className="bg-stone-900 border border-stone-800 p-5 rounded-xl shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-stone-400">Dining Tables</span>
            <TableIcon className="w-4 h-4 text-amber-500" />
          </div>
          <p className="text-2xl font-bold text-white mt-2">{analytics?.total_tables || tables.length || 0}</p>
          <span className="text-[11px] text-stone-400">Main, Patio, Booths, Bar</span>
        </div>

        <div className="bg-stone-900 border border-stone-800 p-5 rounded-xl shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-stone-400">AI Tool Invocations</span>
            <Wrench className="w-4 h-4 text-indigo-500" />
          </div>
          <p className="text-2xl font-bold text-white mt-2">{analytics?.total_tool_calls || 0}</p>
          <span className="text-[11px] text-indigo-400">Success Rate: {analytics?.tool_success_rate}</span>
        </div>

        <div className="bg-stone-900 border border-stone-800 p-5 rounded-xl shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-stone-400">Cancellation Rate</span>
            <XCircle className="w-4 h-4 text-stone-400" />
          </div>
          <p className="text-2xl font-bold text-white mt-2">{analytics?.cancellation_rate || '0%'}</p>
          <span className="text-[11px] text-stone-400">Within optimal 5% threshold</span>
        </div>
      </div>

      {/* SUB-TAB 1: OVERVIEW */}
      {activeAdminTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-stone-900 border border-stone-800 rounded-2xl p-6 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-sm font-semibold text-white">Live Bookings & Guest Ledger</h4>
              <span className="text-xs text-stone-400">Latest 10 Transactions</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="text-stone-400 border-b border-stone-800">
                  <tr>
                    <th className="pb-3 font-medium">Code</th>
                    <th className="pb-3 font-medium">Guest Name</th>
                    <th className="pb-3 font-medium">Contact Phone</th>
                    <th className="pb-3 font-medium">Date & Time</th>
                    <th className="pb-3 font-medium">Party</th>
                    <th className="pb-3 font-medium">Table</th>
                    <th className="pb-3 font-medium">Status</th>
                    <th className="pb-3 font-medium">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-stone-800/60 text-stone-300">
                  {analytics?.recent_reservations?.map((r: any) => (
                    <tr key={r.id} className="hover:bg-stone-800/40">
                      <td className="py-3 font-mono font-bold text-amber-400">{r.booking_code}</td>
                      <td className="py-3 font-medium text-white">{r.customer_name}</td>
                      <td className="py-3 text-stone-400">{r.customer_phone}</td>
                      <td className="py-3 text-stone-300">{r.time}</td>
                      <td className="py-3">{r.party_size} guests</td>
                      <td className="py-3 font-medium text-amber-300">{r.table}</td>
                      <td className="py-3">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] ${
                          r.status === 'confirmed'
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                            : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                        }`}>
                          {r.status}
                        </span>
                      </td>
                      <td className="py-3">
                        {r.status === 'confirmed' && (
                          <button
                            onClick={() => handleCancelReservation(r.booking_code, r.customer_phone)}
                            className="px-2 py-1 bg-stone-800 hover:bg-rose-950 text-stone-300 hover:text-rose-300 border border-stone-700 hover:border-rose-800 rounded text-[11px] transition"
                          >
                            Cancel
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-stone-900 border border-stone-800 rounded-2xl p-6 shadow-xl flex flex-col">
            <h4 className="text-sm font-semibold text-white mb-2">Peak Dining Demand Distribution</h4>
            <p className="text-xs text-stone-400 mb-4">Guest distribution by hourly seatings</p>
            <div className="h-56 w-full mt-auto">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <XAxis dataKey="time" stroke="#78716c" fontSize={11} />
                  <YAxis stroke="#78716c" fontSize={11} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1c1917', borderColor: '#44403c', fontSize: '12px' }}
                  />
                  <Bar dataKey="count" fill="#e11d48" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* SUB-TAB 2: TABLES MANAGEMENT */}
      {activeAdminTab === 'tables' && (
        <div className="bg-stone-900 border border-stone-800 rounded-2xl p-6 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-sm font-semibold text-white">Table Inventory & Capacity Mapping</h4>
            <span className="text-xs text-stone-400">All Dining Zones</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {tables.map((tbl) => (
              <div key={tbl.id} className="p-4 bg-stone-950 border border-stone-800 rounded-xl space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-base text-amber-400">{tbl.table_number}</span>
                  <span className="px-2 py-0.5 rounded-full text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    {tbl.is_active ? 'Active' : 'Maintenance'}
                  </span>
                </div>
                <div className="text-xs text-stone-400 space-y-1">
                  <p>Zone: <strong className="text-stone-200 capitalize">{tbl.seating_area.replace('_', ' ')}</strong></p>
                  <p>Capacity: <strong className="text-stone-200">{tbl.min_capacity} - {tbl.max_capacity} guests</strong></p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* SUB-TAB 3: CONVERSATIONS & TOOL EXECUTION AUDIT */}
      {activeAdminTab === 'conversations' && (
        <div className="bg-stone-900 border border-stone-800 rounded-2xl p-6 shadow-xl">
          <h4 className="text-sm font-semibold text-white mb-4">AI Agent Conversation & Tool Execution Inspector</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="md:col-span-1 border-r border-stone-800 pr-4 space-y-2">
              <p className="text-xs text-stone-400 mb-2 font-medium">Recent Sessions</p>
              {conversations.map((c: any) => (
                <div
                  key={c.id}
                  onClick={() => loadConversationDetails(c.id)}
                  className={`p-3 rounded-lg border cursor-pointer transition text-xs ${
                    selectedConv?.id === c.id
                      ? 'bg-rose-950/30 border-rose-800 text-white'
                      : 'bg-stone-950 border-stone-800 text-stone-300 hover:border-stone-700'
                  }`}
                >
                  <div className="flex justify-between items-center">
                    <span className="font-mono text-[11px] text-amber-400">{c.id.substring(0, 14)}...</span>
                    <span className="text-[10px] text-stone-500 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(c.started_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <div className="flex gap-3 text-[11px] text-stone-400 mt-1">
                    <span>{c.message_count} messages</span>
                    <span className="text-indigo-400 font-medium">{c.tool_call_count} tool calls</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="md:col-span-2">
              {selectedConv ? (
                <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2">
                  <div className="border-b border-stone-800 pb-2">
                    <span className="text-xs text-stone-400">Session ID: </span>
                    <code className="text-xs text-amber-300 font-mono">{selectedConv.id}</code>
                  </div>

                  {selectedConv.tools?.length > 0 && (
                    <div>
                      <h5 className="text-xs font-semibold text-indigo-400 mb-2">Executed Tools Audit:</h5>
                      <div className="space-y-2">
                        {selectedConv.tools.map((t: any, idx: number) => (
                          <div key={idx} className="p-3 bg-stone-950 rounded-lg border border-stone-800 text-xs">
                            <div className="flex items-center justify-between text-indigo-300 font-medium">
                              <span>🛠️ {t.tool_name}</span>
                              <span className="text-emerald-400 text-[10px]">{t.success ? 'Success' : 'Failed'}</span>
                            </div>
                            <pre className="mt-1 text-[10px] text-stone-400 overflow-x-auto bg-stone-900 p-2 rounded border border-stone-800">
                              Args: {t.arguments}
                            </pre>
                            <pre className="mt-1 text-[10px] text-amber-300/80 overflow-x-auto bg-stone-900 p-2 rounded border border-stone-800">
                              Result: {t.result}
                            </pre>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div>
                    <h5 className="text-xs font-semibold text-stone-300 mb-2">Transcript Dialog:</h5>
                    <div className="space-y-2">
                      {selectedConv.messages?.map((m: any, idx: number) => (
                        <div key={idx} className="text-xs p-3 bg-stone-950 rounded-lg border border-stone-800">
                          <span className={`font-semibold ${m.role === 'user' ? 'text-rose-400' : 'text-amber-400'}`}>
                            {m.role.toUpperCase()}:
                          </span>
                          <p className="text-stone-300 mt-1 leading-relaxed">{m.content}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="h-64 flex items-center justify-center text-xs text-stone-500">
                  Select a session from the left to inspect natural language transcripts and database tool telemetry.
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
