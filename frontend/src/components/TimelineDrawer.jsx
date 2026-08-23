import React from 'react';
import { exportCaseAuditCSV } from '../api/client';

export default function TimelineDrawer({ caseDetail, onClose }) {
  if (!caseDetail) return null;
  const { case: c, timeline } = caseDetail;

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div className="drawer-content" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', borderBottom: '1px solid #e2e8f0', paddingBottom: '18px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h2 className="font-heading" style={{ fontSize: '1.4rem', fontWeight: '800', color: '#0f172a', letterSpacing: '-0.01em' }}>
                Case Audit: {c.case_id}
              </h2>
              <span className={`rz-badge ${c.status === 'recovered' ? 'badge-recovered' : (c.status === 'blocked' ? 'badge-blocked' : 'badge-escalated')}`}>
                {c.status}
              </span>
            </div>
            <p style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '3px' }}>
              Customer: <strong style={{ color: '#0f172a' }}>{c.customer_name}</strong> ({c.customer_id})
            </p>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              className="btn-rz-primary"
              style={{ padding: '6px 14px', fontSize: '0.825rem' }}
              onClick={() => exportCaseAuditCSV(c.case_id)}
            >
              📥 Export Case CSV
            </button>
            <button className="btn-rz-secondary" onClick={onClose} style={{ padding: '6px 14px', fontSize: '0.85rem' }}>
              ✕ Close
            </button>
          </div>
        </div>

        {/* Overview Banner */}
        <div style={{ padding: '18px 20px', marginBottom: '28px', background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
            <div>
              <div style={{ fontSize: '0.725rem', color: '#64748b', fontWeight: '800', textTransform: 'uppercase' }}>Amount at Risk</div>
              <div style={{ fontSize: '1.25rem', fontWeight: '800', fontFamily: 'Plus Jakarta Sans, sans-serif', color: '#0284c7', marginTop: '2px' }}>
                ₹{c.amount?.toLocaleString('en-IN')}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.725rem', color: '#64748b', fontWeight: '800', textTransform: 'uppercase' }}>Event Type</div>
              <div style={{ fontSize: '0.875rem', fontWeight: '700', color: '#0f172a', marginTop: '4px', textTransform: 'capitalize' }}>
                {(c.event_type || '').replace(/_/g, ' ')}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.725rem', color: '#64748b', fontWeight: '800', textTransform: 'uppercase' }}>Attempts</div>
              <div style={{ fontSize: '0.875rem', fontWeight: '800', color: '#0f172a', marginTop: '4px' }}>
                {c.attempts || 0} / 3
              </div>
            </div>
          </div>
        </div>

        <h3 className="font-heading" style={{ fontSize: '1.15rem', fontWeight: '800', marginBottom: '20px', color: '#0f172a' }}>
          🤖 Multi-Agent Orchestration Audit Trail
        </h3>

        <div style={{ marginTop: '12px' }}>
          {timeline && timeline.length > 0 ? (
            timeline.map((item, idx) => {
              const isBlocked = item.agent === 'ComplianceGuard' && item.decision === 'BLOCK';
              const isRecovered = item.agent === 'Execution' && (item.decision === 'RECOVERED' || item.decision === 'SUCCESS');
              const dotColor = isBlocked ? '#ef4444' : (isRecovered ? '#10b981' : '#0284c7');
              const res = item.result || {};

              return (
                <div key={idx} className="timeline-item">
                  <div className="timeline-dot" style={{ background: dotColor }}></div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <span style={{ fontSize: '0.85rem', fontWeight: '800', color: '#0284c7', background: '#e0f2fe', padding: '2px 8px', borderRadius: '6px' }}>
                      [{item.agent} Agent]
                    </span>
                    <span style={{ fontSize: '0.775rem', color: '#94a3b8', fontFamily: 'Monaco, Consolas, monospace' }}>
                      {new Date(item.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.95rem', fontWeight: '800', color: '#0f172a', marginBottom: '6px' }}>
                    {item.decision}
                  </div>
                  <div style={{ fontSize: '0.85rem', color: '#334155', background: '#f8fafc', padding: '12px 16px', borderRadius: '8px', borderLeft: `4px solid ${dotColor}`, border: '1px solid #e2e8f0' }}>
                    {item.reason}
                  </div>

                  {item.tool_called && (
                    <div style={{ fontSize: '0.775rem', color: '#6366f1', marginTop: '8px', fontWeight: '700' }}>
                      🛠 Tool Invoked: <code style={{ background: '#e0e7ff', padding: '2px 6px', borderRadius: '4px', border: '1px solid #c7d2fe' }}>{item.tool_called}</code>
                    </div>
                  )}

                  {/* Render Execution Provider Details */}
                  {res.delivered_content && (
                    <div style={{ fontSize: '0.8rem', color: '#1e293b', marginTop: '6px', padding: '8px 12px', background: '#f1f5f9', borderRadius: '6px', border: '1px solid #cbd5e1' }}>
                      💬 <strong>Delivered Copy:</strong> "{res.delivered_content}"
                    </div>
                  )}
                  {res.recovery_link && (
                    <div style={{ fontSize: '0.8rem', color: '#0284c7', marginTop: '6px', wordBreak: 'break-all' }}>
                      🔗 <strong>Recovery Link:</strong> <a href={res.recovery_link} target="_blank" rel="noreferrer" style={{ textDecoration: 'underline', color: '#0284c7' }}>{res.recovery_link}</a>
                    </div>
                  )}
                  {res.ticket_id && (
                    <div style={{ fontSize: '0.8rem', color: '#b45309', marginTop: '6px' }}>
                      🎫 <strong>Human Escalation Ticket:</strong> {res.ticket_id} ({res.assigned_team})
                    </div>
                  )}
                </div>
              );
            })
          ) : (
            <p style={{ color: '#64748b', fontSize: '0.9rem' }}>No audit timeline records found.</p>
          )}
        </div>
      </div>
    </div>
  );
}
