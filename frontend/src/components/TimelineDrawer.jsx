import React from 'react';
import { exportCaseAuditCSV } from '../api/client';
import { X, Download, User, Bot, Wrench, ExternalLink, MessageSquare, Ticket, CheckCircle2, ShieldAlert, Sparkles, Clock } from 'lucide-react';

export default function TimelineDrawer({ caseDetail, onClose }) {
  if (!caseDetail) return null;
  const { case: c, timeline } = caseDetail;

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div className="drawer-content" onClick={(e) => e.stopPropagation()}>
        
        {/* Drawer Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', borderBottom: '1px solid #e2e8f0', paddingBottom: '20px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h2 className="font-heading" style={{ fontSize: '1.45rem', fontWeight: '800', color: '#0f172a', letterSpacing: '-0.02em' }}>
                Case Audit: {c.case_id}
              </h2>
              <span className={`rz-badge ${c.status === 'recovered' ? 'badge-recovered' : (c.status === 'blocked' ? 'badge-blocked' : 'badge-escalated')}`}>
                {c.status}
              </span>
            </div>
            <p style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <User size={14} color="#64748b" />
              Customer: <strong style={{ color: '#0f172a' }}>{c.customer_name}</strong> ({c.customer_id})
            </p>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              className="btn-rz-primary"
              style={{ padding: '8px 16px', fontSize: '0.825rem', display: 'inline-flex', alignItems: 'center', gap: '6px' }}
              onClick={() => exportCaseAuditCSV(c.case_id)}
            >
              <Download size={14} /> Export Audit CSV
            </button>
            <button 
              className="btn-rz-secondary" 
              onClick={onClose} 
              style={{ padding: '8px 12px', fontSize: '0.85rem', borderRadius: '10px' }}
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Case Overview Metrics Banner */}
        <div style={{ padding: '20px 24px', marginBottom: '28px', background: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)', borderRadius: '14px', border: '1px solid #cbd5e1' }}>
          <div className="drawer-overview-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '16px' }}>
            <div>
              <div style={{ fontSize: '0.725rem', color: '#64748b', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Amount at Risk</div>
              <div style={{ fontSize: '1.35rem', fontWeight: '800', fontFamily: 'Plus Jakarta Sans, sans-serif', color: '#0284c7', marginTop: '2px' }}>
                ₹{c.amount?.toLocaleString('en-IN')}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.725rem', color: '#64748b', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Event Type</div>
              <div style={{ fontSize: '0.875rem', fontWeight: '700', color: '#0f172a', marginTop: '4px', textTransform: 'capitalize' }}>
                {(c.event_type || '').replace(/_/g, ' ')}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.725rem', color: '#64748b', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Attempts</div>
              <div style={{ fontSize: '0.875rem', fontWeight: '800', color: '#0f172a', marginTop: '4px' }}>
                {c.attempts || 0} / 3 Retries
              </div>
            </div>
          </div>
        </div>

        <h3 className="font-heading" style={{ fontSize: '1.15rem', fontWeight: '800', marginBottom: '20px', color: '#0f172a', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Bot size={20} color="#0284c7" />
          <span>Multi-Agent LangGraph Execution Audit Trail</span>
        </h3>

        {/* Timeline Items */}
        <div style={{ marginTop: '16px' }}>
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
                    <span style={{ fontSize: '0.8rem', fontWeight: '800', color: '#0284c7', background: '#e0f2fe', padding: '3px 10px', borderRadius: '6px', border: '1px solid #bae6fd' }}>
                      [{item.agent} Agent]
                    </span>
                    <span style={{ fontSize: '0.775rem', color: '#94a3b8', fontFamily: 'Monaco, Consolas, monospace', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Clock size={12} />
                      {new Date(item.timestamp).toLocaleTimeString()}
                    </span>
                  </div>

                  <div style={{ fontSize: '0.975rem', fontWeight: '800', color: '#0f172a', marginBottom: '8px', letterSpacing: '-0.01em' }}>
                    {item.decision}
                  </div>

                  <div style={{ fontSize: '0.875rem', color: '#334155', background: '#f8fafc', padding: '14px 18px', borderRadius: '10px', borderLeft: `4px solid ${dotColor}`, border: '1px solid #e2e8f0', lineHeight: 1.5 }}>
                    {item.reason}
                  </div>

                  {item.tool_called && (
                    <div style={{ fontSize: '0.775rem', color: '#6366f1', marginTop: '10px', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Wrench size={14} /> Tool Invoked: <code style={{ background: '#e0e7ff', padding: '2px 8px', borderRadius: '4px', border: '1px solid #c7d2fe', fontFamily: 'Monaco, Consolas, monospace' }}>{item.tool_called}</code>
                    </div>
                  )}

                  {/* Provider Details */}
                  {res.delivered_content && (
                    <div style={{ fontSize: '0.825rem', color: '#1e293b', marginTop: '8px', padding: '10px 14px', background: '#f1f5f9', borderRadius: '8px', border: '1px solid #cbd5e1' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: '700', marginBottom: '4px', color: '#475569' }}>
                        <MessageSquare size={14} /> Delivered Communication Copy:
                      </div>
                      <div style={{ fontStyle: 'italic', color: '#0f172a' }}>"{res.delivered_content}"</div>
                    </div>
                  )}

                  {res.recovery_link && (
                    <div style={{ fontSize: '0.825rem', color: '#0284c7', marginTop: '8px', padding: '10px 14px', background: '#e0f2fe', borderRadius: '8px', border: '1px solid #bae6fd', wordBreak: 'break-all' }}>
                      <div style={{ fontWeight: '700', marginBottom: '2px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <ExternalLink size={14} /> Dedicated Recovery Link:
                      </div>
                      <a href={res.recovery_link} target="_blank" rel="noreferrer" style={{ textDecoration: 'underline', color: '#0284c7', fontWeight: '700' }}>
                        {res.recovery_link}
                      </a>
                    </div>
                  )}

                  {res.ticket_id && (
                    <div style={{ fontSize: '0.825rem', color: '#b45309', marginTop: '8px', padding: '10px 14px', background: '#fffbeb', borderRadius: '8px', border: '1px solid #fde68a' }}>
                      <div style={{ fontWeight: '700', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Ticket size={14} /> Human Escalation Ticket Created:
                      </div>
                      <div style={{ fontWeight: '800', marginTop: '2px' }}>
                        {res.ticket_id} (Assigned: {res.assigned_team})
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          ) : (
            <p style={{ color: '#64748b', fontSize: '0.9rem' }}>No audit timeline records found for this case.</p>
          )}
        </div>
      </div>
    </div>
  );
}
