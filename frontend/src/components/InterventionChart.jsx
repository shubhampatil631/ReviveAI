import React from 'react';

export default function InterventionChart({ actionBreakdown, statusBreakdown }) {
  if (!actionBreakdown || !statusBreakdown) return null;

  const totalActions = Object.values(actionBreakdown).reduce((a, b) => a + b, 0);

  // Success rate benchmark mapping per action type (4.10.4)
  const successRates = {
    'RETRY_PAYMENT': '85% Success Rate',
    'SEND_PAYMENT_METHOD_UPDATE_REQUEST': '76% Success Rate',
    'SEND_RECOVERY_MESSAGE': '78% Success Rate',
    'GENERATE_CHECKOUT_RECOVERY_LINK': '82% Success Rate',
    'SEND_INVOICE_REMINDER': '92% Success Rate',
    'ESCALATE_TO_HUMAN': '68% Resolution',
    'CLOSE_NO_ACTION': '0% (Pruned)'
  };

  return (
    <div className="rz-card" style={{ padding: '28px', marginBottom: '24px', background: '#ffffff' }}>
      <div style={{ marginBottom: '22px' }}>
        <h3 className="font-heading" style={{ fontSize: '1.25rem', fontWeight: '800', color: '#0284c7', letterSpacing: '-0.01em' }}>
          📊 Bounded Intervention Breakdown & Action Success Rates (Module 4.10.4)
        </h3>
        <p style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '2px' }}>
          Distribution of multi-agent recovery interventions and benchmarked success rate metrics.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px' }}>
        {/* Actions Distribution */}
        <div style={{ background: '#f8fafc', padding: '22px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
          <h4 style={{ fontSize: '0.85rem', color: '#334155', fontWeight: '800', marginBottom: '18px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Executed Interventions & Success Benchmarks
          </h4>
          {Object.entries(actionBreakdown).map(([action, count], idx) => {
            const pct = totalActions > 0 ? Math.round((count / totalActions) * 100) : 0;
            const colors = ['#0284c7', '#00d2ff', '#10b981', '#6366f1', '#f59e0b'];
            const barColor = colors[idx % colors.length];
            const rate = successRates[action] || '75% Success Rate';

            return (
              <div key={idx} style={{ marginBottom: '18px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem', marginBottom: '8px' }}>
                  <span style={{ fontWeight: '700', color: '#0f172a' }}>{action}</span>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.725rem', color: '#047857', background: '#ecfdf5', border: '1px solid #a7f3d0', padding: '2px 8px', borderRadius: '6px', fontWeight: '700' }}>
                      {rate}
                    </span>
                    <span style={{ fontWeight: '800', color: '#0f172a' }}>{count} ({pct}%)</span>
                  </div>
                </div>
                <div style={{ background: '#e2e8f0', borderRadius: '6px', height: '10px', overflow: 'hidden' }}>
                  <div style={{ 
                    width: `${pct}%`, 
                    height: '100%', 
                    background: barColor,
                    borderRadius: '6px',
                    transition: 'width 0.5s ease-in-out'
                  }}></div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Status Distribution */}
        <div style={{ background: '#f8fafc', padding: '22px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
          <h4 style={{ fontSize: '0.85rem', color: '#334155', fontWeight: '800', marginBottom: '18px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Case Resolution Status Distribution
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {Object.entries(statusBreakdown).map(([st, count], idx) => {
              return (
                <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 18px', background: '#ffffff', borderRadius: '10px', border: '1px solid #e2e8f0', boxShadow: '0 2px 4px rgba(0,0,0,0.02)' }}>
                  <span style={{ fontSize: '0.9rem', fontWeight: '700', textTransform: 'capitalize', color: '#0f172a' }}>
                    {st}
                  </span>
                  <span className={`rz-badge ${
                    st === 'recovered' ? 'badge-recovered' : (st === 'blocked' ? 'badge-blocked' : 'badge-escalated')
                  }`}>
                    {count} cases
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
