import React, { useEffect, useState } from 'react';
import { fetchComplianceLogs, evaluateComplianceAction } from '../api/client';

export default function CompliancePanel({ onUpdate }) {
  const [logs, setLogs] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(false);

  // MCP Live Tester State
  const [testCaseId, setTestCaseId] = useState('CASE_1003');
  const [testCustomerId, setTestCustomerId] = useState('CUST_TEST_DND');
  const [testAction, setTestAction] = useState('RETRY_PAYMENT');
  const [evalResult, setEvalResult] = useState(null);
  const [evaluating, setEvaluating] = useState(false);

  useEffect(() => {
    loadLogs();
  }, [filter]);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const data = await fetchComplianceLogs(filter);
      setLogs(data.compliance_logs || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleEvaluate = async () => {
    if (!testCaseId || !testAction) return;
    setEvaluating(true);
    try {
      const res = await evaluateComplianceAction(testCaseId, testCustomerId, testAction);
      setEvalResult(res);
      await loadLogs();
      if (onUpdate) onUpdate();
    } catch (e) {
      console.error(e);
      setEvalResult({ allowed: false, decision: 'ERROR', rule_fired: 'CLIENT_ERROR', reason: e.message });
    } finally {
      setEvaluating(false);
    }
  };

  return (
    <div className="rz-card" style={{ padding: '28px', marginTop: '24px', background: '#ffffff' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h3 className="font-heading" style={{ fontSize: '1.25rem', fontWeight: '800', color: '#ef4444', letterSpacing: '-0.01em' }}>
              🛡️ Deterministic MCP Compliance Guard Logs
            </h3>
            <span style={{ background: '#fff1f2', border: '1px solid #fecdd3', color: '#b91c1c', padding: '3px 10px', borderRadius: '12px', fontSize: '0.75rem', fontWeight: '700' }}>
              Hard Non-LLM Gates
            </span>
          </div>
          <p style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '4px' }}>
            Hard policy gates preventing out-of-policy agent actions (Retry Limiter, Cooldown, DND Registry, Escalation Tiers, Blackout Window).
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          {['all', 'ALLOW', 'BLOCK', 'ESCALATE'].map((f) => (
            <button
              key={f}
              className={filter === f ? 'btn-rz-primary' : 'btn-rz-secondary'}
              style={{ padding: '6px 14px', fontSize: '0.8rem' }}
              onClick={() => setFilter(f)}
            >
              {f.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* MCP Live Tester Section */}
      <div style={{ padding: '18px 20px', background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0', marginBottom: '24px' }}>
        <div style={{ fontSize: '0.85rem', fontWeight: '800', color: '#0284c7', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span>⚙️ Live MCP Tool Evaluator:</span>
          <span style={{ fontSize: '0.775rem', color: '#64748b', fontWeight: 'normal' }}>
            Test hard guardrails in real-time
          </span>
        </div>
        <div style={{ display: 'flex', gap: '14px', flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <div style={{ flex: '1', minWidth: '150px' }}>
            <label style={{ fontSize: '0.75rem', fontWeight: '700', color: '#475569' }}>Case ID</label>
            <input
              type="text"
              value={testCaseId}
              onChange={(e) => setTestCaseId(e.target.value)}
              placeholder="e.g. CASE_1003"
              style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '0.85rem' }}
            />
          </div>
          <div style={{ flex: '1', minWidth: '150px' }}>
            <label style={{ fontSize: '0.75rem', fontWeight: '700', color: '#475569' }}>Customer ID</label>
            <input
              type="text"
              value={testCustomerId}
              onChange={(e) => setTestCustomerId(e.target.value)}
              placeholder="e.g. CUST_DND"
              style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '0.85rem' }}
            />
          </div>
          <div style={{ flex: '1.2', minWidth: '200px' }}>
            <label style={{ fontSize: '0.75rem', fontWeight: '700', color: '#475569' }}>Proposed Action</label>
            <select
              value={testAction}
              onChange={(e) => setTestAction(e.target.value)}
              style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '0.85rem', background: '#fff' }}
            >
              <option value="RETRY_PAYMENT">RETRY_PAYMENT</option>
              <option value="SEND_RECOVERY_MESSAGE">SEND_RECOVERY_MESSAGE</option>
              <option value="SEND_PAYMENT_METHOD_UPDATE_REQUEST">SEND_PAYMENT_METHOD_UPDATE_REQUEST</option>
              <option value="SEND_INVOICE_REMINDER">SEND_INVOICE_REMINDER</option>
              <option value="GENERATE_CHECKOUT_RECOVERY_LINK">GENERATE_CHECKOUT_RECOVERY_LINK</option>
              <option value="ESCALATE_TO_HUMAN">ESCALATE_TO_HUMAN</option>
              <option value="CLOSE_NO_ACTION">CLOSE_NO_ACTION</option>
            </select>
          </div>
          <button
            className="btn-rz-primary"
            disabled={evaluating}
            onClick={handleEvaluate}
            style={{ padding: '9px 18px', fontSize: '0.85rem' }}
          >
            {evaluating ? 'Evaluating...' : 'Evaluate via MCP Guard'}
          </button>
        </div>

        {evalResult && (
          <div style={{ marginTop: '16px', padding: '14px 18px', background: '#ffffff', borderRadius: '8px', borderLeft: `4px solid ${evalResult.allowed ? '#10b981' : '#ef4444'}`, border: '1px solid #e2e8f0' }}>
            <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '4px' }}>
              <span className={`rz-badge ${evalResult.decision === 'ALLOW' ? 'badge-recovered' : (evalResult.decision === 'BLOCK' ? 'badge-blocked' : 'badge-escalated')}`}>
                {evalResult.decision}
              </span>
              <span style={{ fontSize: '0.8rem', fontWeight: '700', color: '#7e22ce', fontFamily: 'Monaco, Consolas, monospace' }}>
                Rule: {evalResult.rule_fired}
              </span>
            </div>
            <p style={{ fontSize: '0.85rem', color: '#0f172a', margin: '6px 0 0 0' }}>
              <strong>MCP Result:</strong> {evalResult.reason}
            </p>
          </div>
        )}
      </div>

      <div className="table-container" style={{ border: '1px solid #e2e8f0', borderRadius: '12px', overflow: 'hidden' }}>
        <table>
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Case ID</th>
              <th>Action Attempted</th>
              <th>Decision</th>
              <th>Rule Fired</th>
              <th>Reasoning / Justification</th>
            </tr>
          </thead>
          <tbody>
            {logs.length === 0 ? (
              <tr>
                <td colSpan="6" style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
                  No compliance decision logs found for selected filter.
                </td>
              </tr>
            ) : (
              logs.map((log, i) => (
                <tr key={i}>
                  <td style={{ fontSize: '0.8rem', color: '#64748b', fontFamily: 'Monaco, Consolas, monospace' }}>
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </td>
                  <td style={{ fontWeight: '700', color: '#0284c7', fontFamily: 'Monaco, Consolas, monospace' }}>{log.case_id}</td>
                  <td style={{ fontWeight: '600', color: '#0f172a' }}>{log.action_attempted}</td>
                  <td>
                    <span className={`rz-badge ${
                      log.decision === 'ALLOW' ? 'badge-recovered' : (log.decision === 'BLOCK' ? 'badge-blocked' : 'badge-escalated')
                    }`}>
                      {log.decision}
                    </span>
                  </td>
                  <td>
                    <span style={{ background: '#f3e8ff', color: '#7e22ce', border: '1px solid #e9d5ff', padding: '3px 8px', borderRadius: '6px', fontSize: '0.775rem', fontFamily: 'Monaco, Consolas, monospace', fontWeight: '700' }}>
                      {log.rule_fired}
                    </span>
                  </td>
                  <td style={{ fontSize: '0.85rem', color: '#334155' }}>
                    {log.reason}
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
