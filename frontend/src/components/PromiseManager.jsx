import React, { useEffect, useState } from 'react';
import { fetchPromises, createPromise, markPromisePaid, markPromiseBroken, runDeadlineWatcher } from '../api/client';
import { CalendarCheck, Clock, Plus, CheckCircle2, XCircle, RefreshCw, Calendar, Sparkles, Filter } from 'lucide-react';

export default function PromiseManager({ onUpdate }) {
  const [promises, setPromises] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);

  // New Promise Form State
  const [newCaseId, setNewCaseId] = useState('CASE_LIVE_03');
  const [newAmount, setNewAmount] = useState(85000);
  const [newDaysDue, setNewDaysDue] = useState(3);
  const [creating, setCreating] = useState(false);
  const [formMsg, setFormMsg] = useState(null);

  useEffect(() => {
    loadPromises();
  }, [filter]);

  const loadPromises = async () => {
    setLoading(true);
    try {
      const data = await fetchPromises(filter);
      setPromises(data.promises || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleRunDeadlineWatcher = async () => {
    setLoading(true);
    try {
      await runDeadlineWatcher();
      await loadPromises();
      if (onUpdate) onUpdate();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePromise = async (e) => {
    e.preventDefault();
    if (!newCaseId || !newAmount) return;
    setCreating(true);
    setFormMsg(null);
    try {
      await createPromise(newCaseId, newAmount, newDaysDue);
      setFormMsg({ type: 'success', text: `Promise registered for ${newCaseId}!` });
      setTimeout(() => {
        setShowAddForm(false);
        setFormMsg(null);
      }, 1500);
      await loadPromises();
      if (onUpdate) onUpdate();
    } catch (err) {
      console.error(err);
      setFormMsg({ type: 'error', text: 'Error registering promise. Backend auto-resolving case ID...' });
    } finally {
      setCreating(false);
    }
  };

  const handleMarkPaid = async (promiseId) => {
    try {
      await markPromisePaid(promiseId);
      await loadPromises();
      if (onUpdate) onUpdate();
    } catch (err) {
      console.error(err);
    }
  };

  const handleMarkBroken = async (promiseId) => {
    try {
      await markPromiseBroken(promiseId);
      await loadPromises();
      if (onUpdate) onUpdate();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="rz-card" style={{ padding: '28px', marginTop: '24px', background: '#ffffff' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h3 className="font-heading" style={{ fontSize: '1.25rem', fontWeight: '800', color: '#6366f1', letterSpacing: '-0.01em', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <CalendarCheck size={22} />
              <span>Promise-to-Pay Tracker</span>
            </h3>
            <span style={{ background: '#e0e7ff', border: '1px solid #c7d2fe', color: '#4338ca', padding: '3px 10px', borderRadius: '12px', fontSize: '0.75rem', fontWeight: '700' }}>
              Module 4.8 Commitment Engine
            </span>
          </div>
          <p style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '4px' }}>
            Tracks customer B2B payment commitments and triggers automated re-queueing into Detector on broken deadlines.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button className="btn-rz-secondary" onClick={() => setShowAddForm(!showAddForm)}>
            {showAddForm ? '✕ Close Form' : <><Plus size={16} /> Log New Commitment</>}
          </button>
          <button className="btn-rz-primary" onClick={handleRunDeadlineWatcher} disabled={loading}>
            <RefreshCw size={15} className={loading ? 'spin' : ''} />
            {loading ? 'Scanning...' : 'Run Deadline Watcher Scan'}
          </button>
        </div>
      </div>

      {/* New Commitment Registration Form */}
      {showAddForm && (
        <form onSubmit={handleCreatePromise} style={{ padding: '20px 24px', background: '#f8fafc', borderRadius: '14px', border: '1px solid #cbd5e1', marginBottom: '24px', animation: 'fadeIn 0.2s ease' }}>
          <div style={{ fontSize: '0.875rem', fontWeight: '800', color: '#0284c7', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Sparkles size={16} /> Register Customer Payment Commitment:
          </div>
          {formMsg && (
            <div style={{ padding: '8px 12px', borderRadius: '8px', marginBottom: '12px', fontSize: '0.85rem', fontWeight: '700', background: formMsg.type === 'success' ? '#dcfce7' : '#fee2e2', color: formMsg.type === 'success' ? '#15803d' : '#b91c1c' }}>
              {formMsg.text}
            </div>
          )}
          <div style={{ display: 'flex', gap: '14px', flexWrap: 'wrap', alignItems: 'flex-end' }}>
            <div style={{ flex: '1', minWidth: '160px' }}>
              <label style={{ fontSize: '0.75rem', fontWeight: '700', color: '#475569', display: 'block', marginBottom: '4px' }}>Case ID</label>
              <input
                type="text"
                value={newCaseId}
                onChange={(e) => setNewCaseId(e.target.value)}
                placeholder="e.g. CASE_1002"
                style={{ width: '100%', padding: '9px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '0.85rem', background: '#ffffff' }}
                required
              />
            </div>
            <div style={{ flex: '1', minWidth: '160px' }}>
              <label style={{ fontSize: '0.75rem', fontWeight: '700', color: '#475569', display: 'block', marginBottom: '4px' }}>Promised Amount (INR)</label>
              <input
                type="number"
                value={newAmount}
                onChange={(e) => setNewAmount(parseFloat(e.target.value))}
                placeholder="14999"
                style={{ width: '100%', padding: '9px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '0.85rem', background: '#ffffff' }}
                required
              />
            </div>
            <div style={{ flex: '1', minWidth: '160px' }}>
              <label style={{ fontSize: '0.75rem', fontWeight: '700', color: '#475569', display: 'block', marginBottom: '4px' }}>Days Until Due</label>
              <input
                type="number"
                value={newDaysDue}
                onChange={(e) => setNewDaysDue(parseInt(e.target.value))}
                placeholder="3"
                style={{ width: '100%', padding: '9px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '0.85rem', background: '#ffffff' }}
                required
              />
            </div>
            <button className="btn-rz-primary" type="submit" disabled={creating} style={{ padding: '10px 20px', fontSize: '0.85rem' }}>
              {creating ? 'Registering...' : 'Save Commitment'}
            </button>
          </div>
        </form>
      )}

      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>
        {['all', 'promised', 'paid', 'broken'].map((f) => (
          <button
            key={f}
            className={filter === f ? 'btn-rz-primary' : 'btn-rz-secondary'}
            style={{ padding: '6px 16px', fontSize: '0.8rem', textTransform: 'uppercase', borderRadius: '20px' }}
            onClick={() => setFilter(f)}
          >
            {f}
          </button>
        ))}
      </div>

      <div className="table-container" style={{ border: '1px solid #e2e8f0', borderRadius: '14px', overflow: 'hidden' }}>
        <table>
          <thead>
            <tr>
              <th>Promise ID</th>
              <th>Case ID</th>
              <th>Promised Amount</th>
              <th>Due Date</th>
              <th>Status</th>
              <th>Automated Action</th>
              <th>State Transition Actions</th>
            </tr>
          </thead>
          <tbody>
            {promises.length === 0 ? (
              <tr>
                <td colSpan="7" style={{ textAlign: 'center', padding: '48px', color: '#64748b' }}>
                  <Clock size={28} style={{ margin: '0 auto 8px auto', display: 'block', color: '#94a3b8' }} />
                  No payment commitments found for selected filter.
                </td>
              </tr>
            ) : (
              promises.map((p, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: '700', color: '#00d2ff', fontFamily: 'Monaco, Consolas, monospace' }}>{p.promise_id}</td>
                  <td style={{ fontWeight: '700', color: '#0284c7', fontFamily: 'Monaco, Consolas, monospace' }}>{p.case_id}</td>
                  <td style={{ fontFamily: 'Plus Jakarta Sans, sans-serif', fontWeight: '800', color: '#0f172a', fontSize: '0.95rem' }}>
                    ₹{(p.promised_amount || 0).toLocaleString('en-IN')}
                  </td>
                  <td style={{ fontSize: '0.85rem', color: '#475569' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Calendar size={14} color="#64748b" />
                      {new Date(p.due_date).toLocaleDateString()}
                    </div>
                  </td>
                  <td>
                    <span className={`rz-badge ${
                      p.status === 'paid' ? 'badge-recovered' : (p.status === 'broken' ? 'badge-blocked' : 'badge-escalated')
                    }`}>
                      {p.status}
                    </span>
                  </td>
                  <td>
                    <span style={{ fontSize: '0.8rem', color: p.status === 'broken' ? '#b91c1c' : (p.status === 'paid' ? '#047857' : '#64748b'), fontWeight: '600', display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                      {p.status === 'broken' ? '⚠️ Re-queued to Detector' : (p.status === 'paid' ? '🎉 Case Recovered' : '⏳ Monitoring Deadline')}
                    </span>
                  </td>
                  <td>
                    {p.status === 'promised' ? (
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button
                          className="btn-rz-secondary"
                          style={{ padding: '4px 12px', fontSize: '0.75rem', background: '#ecfdf5', color: '#047857', border: '1px solid #a7f3d0', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                          onClick={() => handleMarkPaid(p.promise_id)}
                        >
                          <CheckCircle2 size={13} /> Mark Paid
                        </button>
                        <button
                          className="btn-rz-secondary"
                          style={{ padding: '4px 12px', fontSize: '0.75rem', background: '#fff1f2', color: '#be123c', border: '1px solid #fecdd3', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                          onClick={() => handleMarkBroken(p.promise_id)}
                        >
                          <XCircle size={13} /> Mark Broken
                        </button>
                      </div>
                    ) : (
                      <span style={{ fontSize: '0.775rem', color: '#94a3b8', fontWeight: '600' }}>Resolved</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
