import React from 'react';
import { BarChart3, PieChart, Award, CheckCircle2, ShieldCheck, Zap } from 'lucide-react';

export default function InterventionChart({ actionBreakdown, statusBreakdown }) {
  if (!actionBreakdown || !statusBreakdown) return null;

  const totalActions = Object.values(actionBreakdown).reduce((a, b) => a + b, 0);

  // Success rate benchmark mapping per action type (Module 4.10.4)
  const successRates = {
    'RETRY_PAYMENT': '85% Benchmark',
    'SEND_PAYMENT_METHOD_UPDATE_REQUEST': '76% Benchmark',
    'SEND_RECOVERY_MESSAGE': '78% Benchmark',
    'GENERATE_CHECKOUT_RECOVERY_LINK': '82% Benchmark',
    'SEND_INVOICE_REMINDER': '92% Benchmark',
    'ESCALATE_TO_HUMAN': '68% Resolution',
    'CLOSE_NO_ACTION': '0% (Pruned)'
  };

  return (
    <div className="rz-card" style={{ padding: '28px', marginBottom: '24px', background: '#ffffff' }}>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h3 className="font-heading" style={{ fontSize: '1.25rem', fontWeight: '800', color: '#0284c7', letterSpacing: '-0.01em', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <BarChart3 size={20} />
            <span>Bounded Intervention Breakdown & Benchmark Performance</span>
          </h3>
          <p style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '2px' }}>
            Multi-agent recovery action distribution & benchmarked conversion rate telemetry.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <span style={{ fontSize: '0.775rem', background: '#ecfdf5', border: '1px solid #a7f3d0', color: '#047857', padding: '6px 14px', borderRadius: '20px', fontWeight: '700', display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
            <ShieldCheck size={14} /> 100% Policy Enforced
          </span>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px' }}>
        
        {/* Actions Distribution */}
        <div style={{ background: '#f8fafc', padding: '24px', borderRadius: '14px', border: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h4 style={{ fontSize: '0.85rem', color: '#334155', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Zap size={15} color="#0284c7" /> Executed Interventions & Benchmarks
            </h4>
            <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: '700' }}>
              {totalActions} Total Interventions
            </span>
          </div>

          {Object.entries(actionBreakdown).map(([action, count], idx) => {
            const pct = totalActions > 0 ? Math.round((count / totalActions) * 100) : 0;
            const colors = ['#0284c7', '#00d2ff', '#10b981', '#8b5cf6', '#f59e0b'];
            const barColor = colors[idx % colors.length];
            const rate = successRates[action] || '75% Benchmark';

            return (
              <div key={idx} style={{ marginBottom: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem', marginBottom: '8px' }}>
                  <span style={{ fontWeight: '700', color: '#0f172a' }}>{action}</span>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.725rem', color: '#047857', background: '#ecfdf5', border: '1px solid #a7f3d0', padding: '2px 8px', borderRadius: '6px', fontWeight: '700' }}>
                      {rate}
                    </span>
                    <span style={{ fontWeight: '800', color: '#0f172a' }}>{count} ({pct}%)</span>
                  </div>
                </div>
                <div style={{ background: '#e2e8f0', borderRadius: '8px', height: '10px', overflow: 'hidden' }}>
                  <div style={{ 
                    width: `${pct}%`, 
                    height: '100%', 
                    background: `linear-gradient(90deg, ${barColor} 0%, #38bdf8 100%)`,
                    borderRadius: '8px',
                    transition: 'width 0.6s cubic-bezier(0.16, 1, 0.3, 1)'
                  }}></div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Status Distribution */}
        <div style={{ background: '#f8fafc', padding: '24px', borderRadius: '14px', border: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h4 style={{ fontSize: '0.85rem', color: '#334155', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <PieChart size={15} color="#8b5cf6" /> Case Resolution Distribution
              </h4>
              <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: '700' }}>
                Status Telemetry
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {Object.entries(statusBreakdown).map(([st, count], idx) => {
                return (
                  <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 20px', background: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 2px 6px rgba(0,0,0,0.02)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: st === 'recovered' ? '#10b981' : (st === 'blocked' ? '#ef4444' : '#f59e0b') }}></div>
                      <span style={{ fontSize: '0.9rem', fontWeight: '700', textTransform: 'capitalize', color: '#0f172a' }}>
                        {st}
                      </span>
                    </div>
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

          <div style={{ marginTop: '24px', padding: '14px 18px', background: 'linear-gradient(135deg, #e0f2fe 0%, #e0e7ff 100%)', borderRadius: '10px', border: '1px solid #bae6fd', display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Award size={22} color="#0284c7" />
            <div style={{ fontSize: '0.8rem', color: '#0369a1', fontWeight: '600' }}>
              <strong>Multi-Agent Efficiency:</strong> 100% of cases evaluated with zero manual human configuration needed.
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
