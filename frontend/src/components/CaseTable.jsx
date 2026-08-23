import React from 'react';

export default function CaseTable({ cases, onSelectCase, onTriggerAction }) {
  const getBadgeClass = (status) => {
    switch (status) {
      case 'recovered': return 'badge-recovered';
      case 'blocked': return 'badge-blocked';
      case 'escalated': return 'badge-escalated';
      default: return 'badge-detected';
    }
  };

  return (
    <div className="rz-card" style={{ padding: '28px', background: '#ffffff' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '22px' }}>
        <div>
          <h3 className="font-heading" style={{ fontSize: '1.25rem', fontWeight: '800', color: '#0f172a', letterSpacing: '-0.01em' }}>
            Active & Historical Revenue Cases
          </h3>
          <p style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '2px' }}>
            Click any row to inspect autonomous agent audit trail, LangGraph steps, and execution logs.
          </p>
        </div>
        <span style={{ fontSize: '0.8rem', fontWeight: '700', color: '#0284c7', background: '#e0f2fe', padding: '6px 14px', borderRadius: '20px', border: '1px solid #bae6fd' }}>
          {cases.length} Total Records
        </span>
      </div>

      <div className="table-container" style={{ border: '1px solid #e2e8f0', borderRadius: '12px', overflow: 'hidden' }}>
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
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {cases.length === 0 ? (
              <tr>
                <td colSpan="9" style={{ textAlign: 'center', padding: '48px', color: '#64748b', background: '#ffffff' }}>
                  <div style={{ fontSize: '2rem', marginBottom: '8px' }}>📂</div>
                  <div style={{ fontWeight: '700', color: '#334155', marginBottom: '4px' }}>No revenue cases matching filters</div>
                  <div style={{ fontSize: '0.825rem' }}>Upload a batch CSV or adjust active filters above.</div>
                </td>
              </tr>
            ) : (
              cases.map((c) => (
                <tr 
                  key={c.case_id} 
                  style={{ cursor: 'pointer', transition: 'background-color 0.15s ease' }} 
                  onClick={() => onSelectCase(c.case_id)}
                >
                  <td style={{ fontWeight: '700', color: '#0284c7', fontFamily: 'Monaco, Consolas, monospace', fontSize: '0.85rem' }}>
                    {c.case_id}
                  </td>
                  <td>
                    <div style={{ fontWeight: '700', color: '#0f172a' }}>{c.customer_name || c.customer_id}</div>
                    <div style={{ fontSize: '0.775rem', color: '#94a3b8' }}>{c.customer_email}</div>
                  </td>
                  <td>
                    <span style={{ fontSize: '0.825rem', color: '#475569', fontWeight: '600', textTransform: 'capitalize' }}>
                      {(c.event_type || '').replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td style={{ fontWeight: '800', fontFamily: 'Plus Jakarta Sans, sans-serif', color: '#0f172a', fontSize: '0.95rem' }}>
                    ₹{(c.amount || 0).toLocaleString('en-IN')}
                  </td>
                  <td>
                    <span style={{ fontSize: '0.8rem', color: '#475569', background: '#f1f5f9', padding: '4px 10px', borderRadius: '6px', border: '1px solid #e2e8f0', fontWeight: '500' }}>
                      {c.root_cause || 'Diagnosing...'}
                    </span>
                  </td>
                  <td>
                    <span style={{ fontSize: '0.825rem', fontWeight: '700', color: '#0284c7' }}>
                      {c.selected_action || 'Pending'}
                    </span>
                  </td>
                  <td style={{ textAlign: 'center', fontWeight: '700', color: '#475569' }}>
                    {c.attempts || 0}/3
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
                        style={{ padding: '5px 8px', fontSize: '0.75rem', borderRadius: '6px', border: '1px solid #cbd5e1', background: '#f8fafc', fontWeight: '600', color: '#0f172a' }}
                      >
                        <option value="RETRY_PAYMENT">⚡ Retry Payment</option>
                        <option value="SEND_RECOVERY_MESSAGE">💬 Send Message</option>
                        <option value="GENERATE_CHECKOUT_RECOVERY_LINK">🔗 Checkout Link</option>
                        <option value="SEND_INVOICE_REMINDER">📄 Invoice Reminder</option>
                        <option value="ESCALATE_TO_HUMAN">🚨 Escalate</option>
                      </select>
                      <button 
                        className="btn-rz-secondary" 
                        style={{ padding: '5px 10px', fontSize: '0.75rem', borderRadius: '6px', whiteSpace: 'nowrap' }}
                        onClick={() => {
                          const sel = document.getElementById(`action-select-${c.case_id}`);
                          const chosenAction = sel ? sel.value : 'RETRY_PAYMENT';
                          onTriggerAction(c.case_id, chosenAction);
                        }}
                      >
                        Run
                      </button>
                    </div>
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
