import React, { useState } from 'react';
import { User, Play, ChevronRight, Copy, Check, ShieldAlert, Sparkles, Filter, Clock, ArrowRight } from 'lucide-react';

export default function CaseTable({ cases, onSelectCase, onTriggerAction }) {
  const [copiedId, setCopiedId] = useState(null);

  const getBadgeClass = (status) => {
    switch (status) {
      case 'recovered': return 'badge-recovered';
      case 'blocked': return 'badge-blocked';
      case 'escalated': return 'badge-escalated';
      default: return 'badge-detected';
    }
  };

  const handleCopy = (e, id) => {
    e.stopPropagation();
    navigator.clipboard.writeText(id);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const getInitials = (name) => {
    if (!name) return 'CU';
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .substring(0, 2)
      .toUpperCase();
  };

  return (
    <div className="rz-card" style={{ padding: '28px', background: '#ffffff' }}>
      {/* Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '22px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h3 className="font-heading" style={{ fontSize: '1.25rem', fontWeight: '800', color: '#0f172a', letterSpacing: '-0.01em', display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <span>Active & Historical Revenue Cases</span>
            <span style={{ fontSize: '0.75rem', color: '#0284c7', background: '#e0f2fe', padding: '2px 8px', borderRadius: '12px', fontWeight: '700' }}>
              Autonomous Stream
            </span>
          </h3>
          <p style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '2px' }}>
            Click any row or card to inspect LangGraph agent audit trail, execution logs, and compliance records.
          </p>
        </div>
        <span style={{ fontSize: '0.8rem', fontWeight: '700', color: '#0284c7', background: '#e0f2fe', padding: '6px 16px', borderRadius: '20px', border: '1px solid #bae6fd', display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
          <Filter size={14} />
          {cases.length} Total Records
        </span>
      </div>

      {cases.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '54px 20px', color: '#64748b', background: '#ffffff', borderRadius: '14px', border: '1px solid #e2e8f0' }}>
          <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: '#f1f5f9', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px auto', color: '#94a3b8' }}>
            <ShieldAlert size={24} />
          </div>
          <div style={{ fontWeight: '700', color: '#334155', marginBottom: '4px', fontSize: '1rem' }}>No revenue cases match criteria</div>
          <div style={{ fontSize: '0.825rem' }}>Try adjusting active filters or upload a synthetic batch CSV.</div>
        </div>
      ) : (
        <>
          {/* DESKTOP TABLE VIEW (> 768px) */}
          <div className="desktop-table-view table-container">
            <table>
              <thead>
                <tr>
                  <th>Case ID</th>
                  <th>Customer</th>
                  <th>Event Type</th>
                  <th>Amount at Risk</th>
                  <th>Root Cause Diagnosis</th>
                  <th>Bounded Action</th>
                  <th>Attempts</th>
                  <th>Status</th>
                  <th>Manual Trigger</th>
                </tr>
              </thead>
              <tbody>
                {cases.map((c) => (
                  <tr 
                    key={c.case_id} 
                    style={{ cursor: 'pointer', transition: 'all 0.15s ease' }} 
                    onClick={() => onSelectCase(c.case_id)}
                  >
                    <td style={{ fontWeight: '700', color: '#0284c7', fontFamily: 'Monaco, Consolas, monospace', fontSize: '0.85rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span>{c.case_id}</span>
                        <button 
                          onClick={(e) => handleCopy(e, c.case_id)} 
                          title="Copy Case ID"
                          style={{ border: 'none', background: 'transparent', cursor: 'pointer', color: copiedId === c.case_id ? '#10b981' : '#94a3b8', padding: '2px' }}
                        >
                          {copiedId === c.case_id ? <Check size={13} /> : <Copy size={13} />}
                        </button>
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: 'linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%)', color: '#0284c7', fontWeight: '800', fontSize: '0.75rem', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                          {getInitials(c.customer_name)}
                        </div>
                        <div>
                          <div style={{ fontWeight: '700', color: '#0f172a', fontSize: '0.875rem' }}>{c.customer_name || c.customer_id}</div>
                          <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{c.customer_email}</div>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span style={{ fontSize: '0.8rem', color: '#475569', fontWeight: '600', textTransform: 'capitalize', background: '#f8fafc', padding: '4px 10px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                        {(c.event_type || '').replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td style={{ fontWeight: '800', fontFamily: 'Plus Jakarta Sans, sans-serif', color: '#0f172a', fontSize: '0.95rem' }}>
                      ₹{(c.amount || 0).toLocaleString('en-IN')}
                    </td>
                    <td>
                      <span style={{ fontSize: '0.8rem', color: '#334155', background: '#f1f5f9', padding: '4px 10px', borderRadius: '6px', border: '1px solid #e2e8f0', fontWeight: '600', display: 'inline-block', maxWidth: '200px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {c.root_cause || 'Diagnosing...'}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontSize: '0.825rem', fontWeight: '700', color: '#0284c7' }}>
                        {c.selected_action || 'Pending'}
                      </span>
                    </td>
                    <td style={{ textAlign: 'center', fontWeight: '700', color: '#475569' }}>
                      <span style={{ background: '#f8fafc', padding: '3px 8px', borderRadius: '6px', border: '1px solid #e2e8f0', fontSize: '0.8rem' }}>
                        {c.attempts || 0}/3
                      </span>
                    </td>
                    <td>
                      <span className={`rz-badge ${getBadgeClass(c.status)}`}>
                        {c.status}
                      </span>
                    </td>
                    <td onClick={(e) => e.stopPropagation()}>
                      <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                        <select 
                          id={`action-select-${c.case_id}`}
                          defaultValue="RETRY_PAYMENT"
                          style={{ padding: '6px 10px', fontSize: '0.775rem', borderRadius: '8px', border: '1px solid #cbd5e1', background: '#ffffff', fontWeight: '600', color: '#0f172a', outline: 'none' }}
                        >
                          <option value="RETRY_PAYMENT">⚡ Retry Payment</option>
                          <option value="SEND_RECOVERY_MESSAGE">💬 Send Message</option>
                          <option value="GENERATE_CHECKOUT_RECOVERY_LINK">🔗 Checkout Link</option>
                          <option value="SEND_INVOICE_REMINDER">📄 Invoice Reminder</option>
                          <option value="ESCALATE_TO_HUMAN">🚨 Escalate</option>
                        </select>
                        <button 
                          className="btn-rz-secondary" 
                          style={{ padding: '6px 12px', fontSize: '0.775rem', borderRadius: '8px', whiteSpace: 'nowrap', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                          onClick={() => {
                            const sel = document.getElementById(`action-select-${c.case_id}`);
                            const chosenAction = sel ? sel.value : 'RETRY_PAYMENT';
                            onTriggerAction(c.case_id, chosenAction);
                          }}
                        >
                          <Play size={12} /> Run
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* MOBILE CARD VIEW (<= 768px) */}
          <div className="mobile-card-view">
            {cases.map((c) => (
              <div 
                key={`mobile-${c.case_id}`}
                className="mobile-case-card"
                onClick={() => onSelectCase(c.case_id)}
              >
                {/* Top Row: Case ID & Status Badge */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ fontWeight: '800', color: '#0284c7', fontFamily: 'Monaco, Consolas, monospace', fontSize: '0.85rem' }}>
                      {c.case_id}
                    </span>
                    <button 
                      onClick={(e) => handleCopy(e, c.case_id)} 
                      title="Copy Case ID"
                      style={{ border: 'none', background: 'transparent', cursor: 'pointer', color: copiedId === c.case_id ? '#10b981' : '#94a3b8', padding: '2px' }}
                    >
                      {copiedId === c.case_id ? <Check size={13} /> : <Copy size={13} />}
                    </button>
                  </div>
                  <span className={`rz-badge ${getBadgeClass(c.status)}`}>
                    {c.status}
                  </span>
                </div>

                {/* Customer & Amount at Risk */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', background: '#f8fafc', padding: '12px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: 'linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%)', color: '#0284c7', fontWeight: '800', fontSize: '0.8rem', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      {getInitials(c.customer_name)}
                    </div>
                    <div>
                      <div style={{ fontWeight: '700', color: '#0f172a', fontSize: '0.875rem' }}>{c.customer_name || c.customer_id}</div>
                      <div style={{ fontSize: '0.75rem', color: '#64748b' }}>{c.customer_email}</div>
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: '700', textTransform: 'uppercase' }}>Exposure</div>
                    <div style={{ fontWeight: '800', fontFamily: 'Plus Jakarta Sans, sans-serif', color: '#0284c7', fontSize: '1.05rem' }}>
                      ₹{(c.amount || 0).toLocaleString('en-IN')}
                    </div>
                  </div>
                </div>

                {/* Event & Root Cause Pills */}
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '14px' }}>
                  <span style={{ fontSize: '0.775rem', color: '#475569', fontWeight: '600', textTransform: 'capitalize', background: '#f1f5f9', padding: '4px 10px', borderRadius: '6px', border: '1px solid #cbd5e1' }}>
                    Event: {(c.event_type || '').replace(/_/g, ' ')}
                  </span>
                  <span style={{ fontSize: '0.775rem', color: '#334155', background: '#f1f5f9', padding: '4px 10px', borderRadius: '6px', border: '1px solid #cbd5e1', fontWeight: '600' }}>
                    Cause: {c.root_cause || 'Diagnosing...'}
                  </span>
                </div>

                {/* Retries & Action Summary */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.8rem', color: '#475569', marginBottom: '14px', paddingTop: '10px', borderTop: '1px solid #f1f5f9' }}>
                  <span>Bounded Action: <strong style={{ color: '#0284c7' }}>{c.selected_action || 'Pending'}</strong></span>
                  <span>Attempts: <strong style={{ color: '#0f172a' }}>{c.attempts || 0}/3</strong></span>
                </div>

                {/* Trigger Action Controls */}
                <div onClick={(e) => e.stopPropagation()} style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <select 
                    id={`action-select-mobile-${c.case_id}`}
                    defaultValue="RETRY_PAYMENT"
                    style={{ flex: 1, padding: '8px 10px', fontSize: '0.8rem', borderRadius: '8px', border: '1px solid #cbd5e1', background: '#ffffff', fontWeight: '600', color: '#0f172a', outline: 'none' }}
                  >
                    <option value="RETRY_PAYMENT">⚡ Retry Payment</option>
                    <option value="SEND_RECOVERY_MESSAGE">💬 Send Message</option>
                    <option value="GENERATE_CHECKOUT_RECOVERY_LINK">🔗 Checkout Link</option>
                    <option value="SEND_INVOICE_REMINDER">📄 Invoice Reminder</option>
                    <option value="ESCALATE_TO_HUMAN">🚨 Escalate</option>
                  </select>
                  <button 
                    className="btn-rz-primary" 
                    style={{ padding: '8px 14px', fontSize: '0.8rem', borderRadius: '8px', whiteSpace: 'nowrap' }}
                    onClick={() => {
                      const sel = document.getElementById(`action-select-mobile-${c.case_id}`);
                      const chosenAction = sel ? sel.value : 'RETRY_PAYMENT';
                      onTriggerAction(c.case_id, chosenAction);
                    }}
                  >
                    <Play size={12} /> Run
                  </button>
                </div>

                {/* Audit view hint */}
                <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '4px', fontSize: '0.75rem', color: '#0284c7', fontWeight: '700', marginTop: '12px' }}>
                  View LangGraph Audit <ArrowRight size={12} />
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
