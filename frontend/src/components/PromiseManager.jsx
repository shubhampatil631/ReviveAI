import React, { useEffect, useState } from 'react';
import { fetchPromises, createPromise, markPromisePaid, markPromiseBroken, runDeadlineWatcher } from '../api/client';

export default function PromiseManager({ onUpdate }) {
  const [promises, setPromises] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);

  // New Promise Form State
  const [newCaseId, setNewCaseId] = useState('CASE_1002');
  const [newAmount, setNewAmount] = useState(14999);
  const [newDaysDue, setNewDaysDue] = useState(3);
  const [creating, setCreating] = useState(false);

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
    try {
      await createPromise(newCaseId, newAmount, newDaysDue);
      setShowAddForm(false);
      await loadPromises();
      if (onUpdate) onUpdate();
    } catch (err) {
      console.error(err);
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
            <h3 className="font-heading" style={{ fontSize: '1.25rem', fontWeight: '800', color: '#6366f1', letterSpacing: '-0.01em' }}>
              🤝 Promise-to-Pay Tracker (Module 4.8)
            </h3>
            <span style={{ background: '#e0e7ff', border: '1px solid #c7d2fe', color: '#4338ca', padding: '3px 10px', borderRadius: '12px', fontSize: '0.75rem', fontWeight: '700' }}>
              B2B Commitment Engine
            </span>
          </div>
          <p style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '4px' }}>
            Tracks customer payment commitments and triggers automated re-queueing into Detector on broken deadlines.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button className="btn-rz-secondary" onClick={() => setShowAddForm(!showAddForm)}>
            {showAddForm ? '✕ Close Form' : '➕ Log New Commitment'}
          </button>
          <button className="btn-rz-primary" onClick={handleRunDeadlineWatcher} disabled={loading}>
            {loading ? 'Scanning...' : '⏰ Run Deadline Watcher Scan'}
          </button>
        </div>
      </div>

      {/* New Commitment Registration Form */}
      {showAddForm && (
        <form onSubmit={handleCreatePromise} style={{ padding: '18px 20px', background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0', marginBottom: '24px' }}>
          <div style={{ fontSize: '0.85rem', fontWeight: '800', color: '#0284c7', marginBottom: '14px' }}>
            📝 Register Customer Payment Commitment:
          </div>
          <div style={{ display: 'flex', gap: '14px', flexWrap: 'wrap', alignItems: 'flex-end' }}>
            <div style={{ flex: '1', minWidth: '150px' }}>
              <label style={{ fontSize: '0.75rem', fontWeight: '700', color: '#475569' }}>Case ID</label>
              <input
                type="text"
                value={newCaseId}
                onChange={(e) => setNewCaseId(e.target.value)}
                placeholder="e.g. CASE_1002"
                style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '0.85rem' }}
                required
              />
            </div>
            <div style={{ flex: '1', minWidth: '150px' }}>
              <label style={{ fontSize: '0.75rem', fontWeight: '700', color: '#475569' }}>Promised Amount (INR)</label>
              <input
                type="number"
                value={newAmount}
                onChange={(e) => setNewAmount(parseFloat(e.target.value))}
                placeholder="14999"
                style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '0.85rem' }}
                required
              />
            </div>
            <div style={{ flex: '1', minWidth: '150px' }}>
              <label style={{ fontSize: '0.75rem', fontWeight: '700', color: '#475569' }}>Days Until Due</label>
              <input
                type="number"
                value={newDaysDue}
                onChange={(e) => setNewDaysDue(parseInt(e.target.value))}
                placeholder="3"
                style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '0.85rem' }}
                required
              />
            </div>
            <button className="btn-rz-primary" type="submit" disabled={creating} style={{ padding: '9px 18px', fontSize: '0.85rem' }}>
              {creating ? 'Registering...' : 'Save Commitment'}
            </button>
          </div>
        </form>
      )}

      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '18px' }}>
        {['all', 'promised', 'paid', 'broken'].map((f) => (
          <button
            key={f}
            className={filter === f ? 'btn-rz-primary' : 'btn-rz-secondary'}
            style={{ padding: '6px 14px', fontSize: '0.8rem', textTransform: 'uppercase' }}
            onClick={() => setFilter(f)}
          >
            {f}
          </button>
        ))}
      </div>

      <div className="table-container" style={{ border: '1px solid #e2e8f0', borderRadius: '12px', overflow: 'hidden' }}>
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
                <td colSpan="7" style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
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
                    {new Date(p.due_date).toLocaleDateString()}
                  </td>
                  <td>
                    <span className={`rz-badge ${
                      p.status === 'paid' ? 'badge-recovered' : (p.status === 'broken' ? 'badge-blocked' : 'badge-escalated')
                    }`}>
                      {p.status}
                    </span>
                  </td>
                  <td>
                    <span style={{ fontSize: '0.8rem', color: p.status === 'broken' ? '#b91c1c' : (p.status === 'paid' ? '#047857' : '#64748b'), fontWeight: '600' }}>
                      {p.status === 'broken' ? '⚠️ Re-queued to Detector Agent' : (p.status === 'paid' ? '🎉 Case Recovered' : '⏳ Monitoring Deadline')}
                    </span>
                  </td>
                  <td>
                    {p.status === 'promised' ? (
                      <div style={{ display: 'flex', gap: '6px' }}>
                        <button
                          className="btn-rz-secondary"
                          style={{ padding: '4px 10px', fontSize: '0.75rem', background: '#ecfdf5', color: '#047857', border: '1px solid #a7f3d0' }}
                          onClick={() => handleMarkPaid(p.promise_id)}
                        >
                          ✅ Paid
                        </button>
                        <button
                          className="btn-rz-secondary"
                          style={{ padding: '4px 10px', fontSize: '0.75rem', background: '#fff1f2', color: '#be123c', border: '1px solid #fecdd3' }}
                          onClick={() => handleMarkBroken(p.promise_id)}
                        >
                          ❌ Broken
                        </button>
                      </div>
                    ) : (
                      <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Completed</span>
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
