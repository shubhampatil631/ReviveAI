const API_BASE = '/api';

export async function fetchSummaryReport() {
  const res = await fetch(`${API_BASE}/batch/report`);
  if (!res.ok) throw new Error('Failed to fetch summary report');
  return res.json();
}

export async function fetchCases(status = 'all', eventType = 'all') {
  const params = new URLSearchParams();
  if (status !== 'all') params.append('status', status);
  if (eventType !== 'all') params.append('event_type', eventType);
  
  const res = await fetch(`${API_BASE}/cases?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch cases');
  return res.json();
}

export async function fetchCaseDetail(caseId) {
  const res = await fetch(`${API_BASE}/cases/${caseId}`);
  if (!res.ok) throw new Error('Failed to fetch case detail');
  return res.json();
}

export async function fetchComplianceLogs(decision = 'all') {
  const params = new URLSearchParams();
  if (decision !== 'all') params.append('decision', decision);
  
  const res = await fetch(`${API_BASE}/compliance/logs?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch compliance logs');
  return res.json();
}

export async function checkRetryAllowed(caseId) {
  const res = await fetch(`${API_BASE}/compliance/check-retry`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ case_id: caseId })
  });
  if (!res.ok) throw new Error('Failed to check retry allowed');
  return res.json();
}

export async function checkContactAllowed(customerId, caseId = '') {
  const res = await fetch(`${API_BASE}/compliance/check-contact`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ customer_id: customerId, case_id: caseId })
  });
  if (!res.ok) throw new Error('Failed to check contact allowed');
  return res.json();
}

export async function fetchEscalationTier(caseId) {
  const res = await fetch(`${API_BASE}/compliance/escalation-tier/${caseId}`);
  if (!res.ok) throw new Error('Failed to fetch escalation tier');
  return res.json();
}

export async function evaluateComplianceAction(caseId, customerId, action) {
  const res = await fetch(`${API_BASE}/compliance/evaluate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ case_id: caseId, customer_id: customerId, action })
  });
  if (!res.ok) throw new Error('Failed to evaluate compliance action');
  return res.json();
}

export async function fetchPromises(status = 'all') {
  const params = new URLSearchParams();
  if (status !== 'all') params.append('status', status);
  
  const res = await fetch(`${API_BASE}/promises?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch promises');
  return res.json();
}

export async function createPromise(caseId, promisedAmount, daysDue) {
  const res = await fetch(`${API_BASE}/promises/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ case_id: caseId, promised_amount: promisedAmount, days_due: daysDue })
  });
  if (!res.ok) throw new Error('Failed to create promise');
  return res.json();
}

export async function markPromisePaid(promiseId) {
  const res = await fetch(`${API_BASE}/promises/${promiseId}/mark-paid`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to mark promise paid');
  return res.json();
}

export async function markPromiseBroken(promiseId) {
  const res = await fetch(`${API_BASE}/promises/${promiseId}/mark-broken`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to mark promise broken');
  return res.json();
}

export async function runDeadlineWatcher() {
  const res = await fetch(`${API_BASE}/promises/check-deadlines`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to run deadline watcher');
  return res.json();
}

export async function uploadBatchCSV(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const res = await fetch(`${API_BASE}/events/batch-upload`, {
    method: 'POST',
    body: formData
  });
  if (!res.ok) throw new Error('Failed to upload batch CSV');
  return res.json();
}

export async function triggerManualAction(caseId, action) {
  const res = await fetch(`${API_BASE}/cases/${caseId}/actions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action })
  });
  if (!res.ok) throw new Error('Failed to trigger action');
  return res.json();
}

export function exportCaseAuditCSV(caseId) {
  window.open(`${API_BASE}/cases/${caseId}/export/csv`, '_blank');
}

export function exportBatchAuditCSV(status = 'all') {
  window.open(`${API_BASE}/cases/export/batch/csv?status=${status}`, '_blank');
}
