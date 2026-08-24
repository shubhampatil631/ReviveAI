import React, { useEffect, useState } from 'react';
import SummaryCards from '../components/SummaryCards';
import CaseTable from '../components/CaseTable';
import TimelineDrawer from '../components/TimelineDrawer';
import CompliancePanel from '../components/CompliancePanel';
import PromiseManager from '../components/PromiseManager';
import InterventionChart from '../components/InterventionChart';
import BatchUploadModal from '../components/BatchUploadModal';
import { fetchSummaryReport, fetchCases, fetchCaseDetail, triggerManualAction, exportBatchAuditCSV } from '../api/client';
import { Zap, Upload, Download, Search, RefreshCw, Layers, BarChart3, CalendarCheck, ShieldCheck, X, Sparkles, Filter, Activity } from 'lucide-react';

export default function Dashboard() {
  const [report, setReport] = useState(null);
  const [cases, setCases] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCaseDetail, setSelectedCaseDetail] = useState(null);
  const [statusFilter, setStatusFilter] = useState('all');
  const [eventTypeFilter, setEventTypeFilter] = useState('all');
  const [showBatchModal, setShowBatchModal] = useState(false);
  const [activeTab, setActiveTab] = useState('cases'); // 'cases' | 'charts' | 'promises' | 'compliance'

  useEffect(() => {
    loadDashboardData();

    // 4.11.6 Native SSE Live Stream channel subscriber
    const eventSource = new EventSource('/api/events/stream');
    eventSource.addEventListener('update', () => {
      loadDashboardData();
    });

    return () => {
      eventSource.close();
    };
  }, [statusFilter, eventTypeFilter, activeTab]);

  const loadDashboardData = async () => {
    try {
      const reportData = await fetchSummaryReport();
      setReport(reportData);

      const casesData = await fetchCases(statusFilter, eventTypeFilter);
      setCases(casesData.cases || []);
    } catch (err) {
      console.error('Error loading dashboard data:', err);
    }
  };

  const handleSelectCase = async (caseId) => {
    try {
      const detail = await fetchCaseDetail(caseId);
      setSelectedCaseDetail(detail);
    } catch (err) {
      console.error('Error fetching case detail:', err);
    }
  };

  const handleTriggerAction = async (caseId, action = 'RETRY_PAYMENT') => {
    try {
      await triggerManualAction(caseId, action);
      loadDashboardData();
    } catch (err) {
      console.error(err);
    }
  };

  // Filter cases by search query
  const filteredCases = cases.filter(c => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      (c.case_id && c.case_id.toLowerCase().includes(q)) ||
      (c.customer_name && c.customer_name.toLowerCase().includes(q)) ||
      (c.customer_email && c.customer_email.toLowerCase().includes(q)) ||
      (c.root_cause && c.root_cause.toLowerCase().includes(q)) ||
      (c.event_type && c.event_type.toLowerCase().includes(q))
    );
  });

  return (
    <div className="app-container">
      
      {/* Razorpay Dark Midnight Navy Hero Header */}
      <header className="rz-hero-bg rz-hero-grid" style={{ width: '100%', borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }}>
        
        {/* Navbar */}
        <div className="nav-container">
          
          {/* Brand Logo & Tagline */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div style={{ width: '42px', height: '42px', borderRadius: '12px', background: 'linear-gradient(135deg, #0284c7 0%, #00d2ff 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ffffff', boxShadow: '0 4px 20px rgba(2, 132, 199, 0.45)', flexShrink: 0 }}>
              <Zap size={24} fill="#ffffff" />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                <span className="font-heading" style={{ fontSize: '1.5rem', fontWeight: '800', color: '#ffffff', letterSpacing: '-0.02em', lineHeight: 1 }}>
                  REVIVE<span style={{ color: '#00d2ff' }}>AI</span>
                </span>
                <span style={{ fontSize: '0.65rem', background: 'rgba(2, 132, 199, 0.25)', border: '1px solid rgba(2, 132, 199, 0.4)', color: '#38bdf8', padding: '2px 8px', borderRadius: '12px', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                  PRO SaaS
                </span>
              </div>
              <div style={{ fontSize: '0.725rem', color: '#94a3b8', marginTop: '2px', fontWeight: '500' }}>
                Autonomous Revenue Recovery & MCP Compliance Engine
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <button className="btn-rz-outline-light" onClick={() => setShowBatchModal(true)}>
              <Upload size={16} /> Upload Batch CSV
            </button>
            <button className="btn-rz-primary" onClick={() => exportBatchAuditCSV(statusFilter)}>
              <Download size={16} /> Export Audit CSV
            </button>
          </div>
        </div>

        {/* Razorpay Hero Banner Intro */}
        <div className="hero-banner">
          <div style={{ maxWidth: '820px', flex: '1 1 300px' }}>
            
            {/* Live Indicator Pill */}
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '10px', background: 'rgba(2, 132, 199, 0.18)', border: '1px solid rgba(2, 132, 199, 0.35)', padding: '6px 16px', borderRadius: '20px', fontSize: '0.775rem', fontWeight: '700', color: '#38bdf8', marginBottom: '18px', maxWidth: '100%' }}>
              <span className="rz-pulse-dot"></span>
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>REAL-TIME AUTONOMOUS DUNNING & RECOVERY PIPELINE</span>
            </div>

            <h1 className="font-heading" style={{ fontSize: '2.5rem', fontWeight: '800', color: '#ffffff', lineHeight: 1.2, letterSpacing: '-0.025em', marginBottom: '14px' }}>
              Autonomous Revenue Recovery <br />
              <span className="gradient-text">Powered by Multi-Agent AI & MCP Policy Guardrails</span>
            </h1>
            
            <p style={{ fontSize: '1rem', color: '#94a3b8', lineHeight: 1.6, maxWidth: '720px' }}>
              Intelligent dunning pipeline engineered with LangGraph multi-agent orchestration, strict deterministic Model Context Protocol (MCP) compliance gates, and real-time Promise-to-Pay tracking.
            </p>
          </div>

          {/* Quick Metrics Badge Banner */}
          <div className="hero-metrics-banner" style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
            <div style={{ background: 'rgba(255, 255, 255, 0.04)', border: '1px solid rgba(255, 255, 255, 0.1)', padding: '16px 22px', borderRadius: '14px', backdropFilter: 'blur(12px)', flex: '1 1 150px' }}>
              <div style={{ fontSize: '0.725rem', color: '#94a3b8', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Compliance Policy</div>
              <div style={{ fontSize: '1.2rem', fontWeight: '800', color: '#10b981', marginTop: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <ShieldCheck size={18} /> 100% Enforced
              </div>
            </div>
            <div style={{ background: 'rgba(255, 255, 255, 0.04)', border: '1px solid rgba(255, 255, 255, 0.1)', padding: '16px 22px', borderRadius: '14px', backdropFilter: 'blur(12px)', flex: '1 1 150px' }}>
              <div style={{ fontSize: '0.725rem', color: '#94a3b8', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Multi-Agent Engine</div>
              <div style={{ fontSize: '1.2rem', fontWeight: '800', color: '#00d2ff', marginTop: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Sparkles size={18} /> LangGraph Core
              </div>
            </div>
          </div>
        </div>

      </header>

      {/* Main Body */}
      <main className="main-content">
        
        {/* Metric Cards */}
        <SummaryCards metrics={report?.metrics} />

        {/* Razorpay Styled Tab Navigation */}
        <div className="rz-tab-bar">
          <button
            className={activeTab === 'cases' ? 'btn-rz-primary' : 'btn-rz-secondary'}
            style={{ padding: '10px 22px', fontSize: '0.875rem', borderRadius: '10px' }}
            onClick={() => setActiveTab('cases')}
          >
            <Layers size={16} /> Revenue Cases ({filteredCases.length})
          </button>
          <button
            className={activeTab === 'charts' ? 'btn-rz-primary' : 'btn-rz-secondary'}
            style={{ padding: '10px 22px', fontSize: '0.875rem', borderRadius: '10px' }}
            onClick={() => setActiveTab('charts')}
          >
            <BarChart3 size={16} /> Intervention Telemetry
          </button>
          <button
            className={activeTab === 'promises' ? 'btn-rz-primary' : 'btn-rz-secondary'}
            style={{ padding: '10px 22px', fontSize: '0.875rem', borderRadius: '10px' }}
            onClick={() => setActiveTab('promises')}
          >
            <CalendarCheck size={16} /> Promise-to-Pay Tracker
          </button>
          <button
            className={activeTab === 'compliance' ? 'btn-rz-primary' : 'btn-rz-secondary'}
            style={{ padding: '10px 22px', fontSize: '0.875rem', borderRadius: '10px' }}
            onClick={() => setActiveTab('compliance')}
          >
            <ShieldCheck size={16} /> Compliance Panel (MCP Guard)
          </button>
        </div>

        {/* Cases Tab Content */}
        {activeTab === 'cases' && (
          <>
            {/* Toolbar & Filter Panel */}
            <div className="rz-card" style={{ padding: '20px 24px', marginBottom: '24px', background: '#ffffff', display: 'flex', gap: '20px', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between' }}>
              
              {/* Search Bar */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: '1 1 380px', maxWidth: '540px', position: 'relative' }}>
                <Search size={18} color="#0284c7" style={{ position: 'absolute', left: '14px' }} />
                <input 
                  type="text"
                  placeholder="Search by Case ID, Customer name, Email, Event, or Root Cause..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{ width: '100%', background: '#f8fafc', border: '1px solid #cbd5e1', padding: '10px 16px 10px 42px', borderRadius: '10px', fontSize: '0.875rem', color: '#0f172a' }}
                />
                {searchQuery && (
                  <button 
                    onClick={() => setSearchQuery('')}
                    style={{ position: 'absolute', right: '12px', border: 'none', background: 'transparent', cursor: 'pointer', color: '#94a3b8' }}
                  >
                    <X size={16} />
                  </button>
                )}
              </div>

              {/* Filters */}
              <div style={{ display: 'flex', gap: '16px', alignItems: 'center', flexWrap: 'wrap' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <label style={{ fontSize: '0.825rem', color: '#64748b', fontWeight: '700' }}>Status:</label>
                  <select 
                    value={statusFilter} 
                    onChange={(e) => setStatusFilter(e.target.value)}
                    style={{ background: '#ffffff', color: '#0f172a', border: '1px solid #cbd5e1', padding: '8px 14px', borderRadius: '8px', fontSize: '0.85rem', fontWeight: '600' }}
                  >
                    <option value="all">All Statuses</option>
                    <option value="recovered">Recovered</option>
                    <option value="blocked">Blocked (MCP)</option>
                    <option value="escalated">Escalated</option>
                    <option value="detected">Detected</option>
                  </select>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <label style={{ fontSize: '0.825rem', color: '#64748b', fontWeight: '700' }}>Event Type:</label>
                  <select 
                    value={eventTypeFilter} 
                    onChange={(e) => setEventTypeFilter(e.target.value)}
                    style={{ background: '#ffffff', color: '#0f172a', border: '1px solid #cbd5e1', padding: '8px 14px', borderRadius: '8px', fontSize: '0.85rem', fontWeight: '600' }}
                  >
                    <option value="all">All Types</option>
                    <option value="subscription_dunning">Subscription Dunning</option>
                    <option value="overdue_invoice">Overdue B2B Invoice</option>
                    <option value="payment_failure">Payment Failure</option>
                    <option value="checkout_abandonment">Checkout Abandonment</option>
                  </select>
                </div>

                <button className="btn-rz-secondary" onClick={loadDashboardData} style={{ padding: '8px 16px', fontSize: '0.85rem', display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                  <RefreshCw size={14} /> Refresh Stream
                </button>
              </div>
            </div>

            {/* Case Table */}
            <CaseTable 
              cases={filteredCases} 
              onSelectCase={handleSelectCase} 
              onTriggerAction={handleTriggerAction} 
            />
          </>
        )}

        {/* Intervention Chart Tab */}
        {activeTab === 'charts' && (
          <InterventionChart 
            actionBreakdown={report?.action_breakdown} 
            statusBreakdown={report?.status_breakdown} 
          />
        )}

        {/* Promise Manager Tab */}
        {activeTab === 'promises' && (
          <PromiseManager onUpdate={loadDashboardData} />
        )}

        {/* Compliance Panel Tab */}
        {activeTab === 'compliance' && (
          <CompliancePanel onUpdate={loadDashboardData} />
        )}
      </main>

      {/* Modals & Drawers */}
      {selectedCaseDetail && (
        <TimelineDrawer 
          caseDetail={selectedCaseDetail} 
          onClose={() => setSelectedCaseDetail(null)} 
        />
      )}

      {showBatchModal && (
        <BatchUploadModal 
          onClose={() => setShowBatchModal(false)} 
          onSuccess={loadDashboardData} 
        />
      )}
    </div>
  );
}
