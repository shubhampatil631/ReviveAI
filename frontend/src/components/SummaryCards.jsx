import React from 'react';
import { Zap, CheckCircle2, TrendingUp, Layers, ShieldAlert, Sparkles, ShieldCheck } from 'lucide-react';

export default function SummaryCards({ metrics }) {
  if (!metrics) return null;

  const cards = [
    {
      title: "Revenue at Risk",
      value: `₹${(metrics.total_at_risk_inr || 0).toLocaleString('en-IN')}`,
      sub: "Active Pipeline Exposure",
      accent: "#0284c7",
      bgLight: "#e0f2fe",
      Icon: Zap,
      trend: "Real-time SSE Stream",
      trendColor: "#0284c7"
    },
    {
      title: "Autonomously Recovered",
      value: `₹${(metrics.total_recovered_inr || 0).toLocaleString('en-IN')}`,
      sub: "Verified Saved Capital",
      accent: "#10b981",
      bgLight: "#ecfdf5",
      Icon: CheckCircle2,
      trend: "Target Exceeded",
      trendColor: "#047857"
    },
    {
      title: "Recovery Rate",
      value: `${metrics.recovery_rate_pct || 0}%`,
      sub: "Industry Benchmark: ≥80%",
      accent: "#00d2ff",
      bgLight: "#ecfeff",
      Icon: TrendingUp,
      trend: "Optimal Performance",
      trendColor: "#0284c7"
    },
    {
      title: "Processed Cases",
      value: metrics.total_cases || 0,
      sub: "LangGraph Orchestrated",
      accent: "#8b5cf6",
      bgLight: "#f3e8ff",
      Icon: Layers,
      trend: "100% Automated",
      trendColor: "#6d28d9"
    },
    {
      title: "MCP Policy Enforced",
      value: metrics.blocked_by_compliance || 0,
      sub: "Zero Violation Guarantee",
      accent: "#ef4444",
      bgLight: "#fff1f2",
      Icon: ShieldCheck,
      trend: "Hard Guard active",
      trendColor: "#b91c1c"
    }
  ];

  return (
    <div className="kpi-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px', marginBottom: '32px' }}>
      {cards.map((card, i) => {
        const IconComponent = card.Icon;
        return (
          <div 
            key={i} 
            className="kpi-card"
          >
            <div style={{ position: 'absolute', top: 0, left: 0, width: '4px', height: '100%', background: card.accent }}></div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <span style={{ fontSize: '0.725rem', color: '#64748b', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                {card.title}
              </span>
              <div style={{ width: '40px', height: '40px', borderRadius: '12px', background: card.bgLight, display: 'flex', alignItems: 'center', justifyContent: 'center', color: card.accent }}>
                <IconComponent size={20} strokeWidth={2.2} />
              </div>
            </div>

            <div style={{ fontSize: '2.05rem', fontWeight: '800', fontFamily: 'Plus Jakarta Sans, sans-serif', color: '#0f172a', marginBottom: '8px', letterSpacing: '-0.03em' }}>
              {card.value}
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.775rem', paddingTop: '10px', borderTop: '1px solid #f1f5f9' }}>
              <span style={{ color: '#475569', fontWeight: '500' }}>{card.sub}</span>
              <span style={{ color: card.trendColor, fontWeight: '700', fontSize: '0.7rem', background: card.bgLight, padding: '3px 10px', borderRadius: '12px' }}>
                {card.trend}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
