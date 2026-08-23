import React from 'react';

export default function SummaryCards({ metrics }) {
  if (!metrics) return null;

  const cards = [
    {
      title: "Total Revenue at Risk",
      value: `₹${(metrics.total_at_risk_inr || 0).toLocaleString('en-IN')}`,
      sub: "Active Pipeline Exposure",
      accent: "#0284c7",
      bgLight: "#e0f2fe",
      icon: "⚡",
      trend: "Real-time Stream"
    },
    {
      title: "Autonomously Recovered",
      value: `₹${(metrics.total_recovered_inr || 0).toLocaleString('en-IN')}`,
      sub: "Verified Revenue Saved",
      accent: "#10b981",
      bgLight: "#ecfdf5",
      icon: "💰",
      trend: "Target Achieved"
    },
    {
      title: "Recovery Rate",
      value: `${metrics.recovery_rate_pct || 0}%`,
      sub: "Benchmark: ≥80%",
      accent: "#00d2ff",
      bgLight: "#ecfeff",
      icon: "📈",
      trend: "High Efficiency"
    },
    {
      title: "Total Cases Processed",
      value: metrics.total_cases || 0,
      sub: "Multi-Agent Handled",
      accent: "#6366f1",
      bgLight: "#e0e7ff",
      icon: "📋",
      trend: "100% Automated"
    },
    {
      title: "MCP Compliance Blocked",
      value: metrics.blocked_by_compliance || 0,
      sub: "Zero Out-of-Policy Actions",
      accent: "#ef4444",
      bgLight: "#fff1f2",
      icon: "🛡️",
      trend: "100% Policy Enforced"
    }
  ];

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '20px', marginBottom: '32px' }}>
      {cards.map((card, i) => (
        <div key={i} className="rz-card" style={{ padding: '22px 24px', position: 'relative', overflow: 'hidden', background: '#ffffff' }}>
          <div style={{ position: 'absolute', top: 0, left: 0, width: '4px', height: '100%', background: card.accent }}></div>
          
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              {card.title}
            </span>
            <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: card.bgLight, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem' }}>
              {card.icon}
            </div>
          </div>

          <div style={{ fontSize: '1.95rem', fontWeight: '800', fontFamily: 'Plus Jakarta Sans, sans-serif', color: '#0f172a', marginBottom: '8px', letterSpacing: '-0.02em' }}>
            {card.value}
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.775rem', paddingTop: '10px', borderTop: '1px solid #f1f5f9' }}>
            <span style={{ color: '#475569', fontWeight: '500' }}>{card.sub}</span>
            <span style={{ color: card.accent, fontWeight: '700', fontSize: '0.725rem', background: card.bgLight, padding: '3px 10px', borderRadius: '12px' }}>
              {card.trend}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
