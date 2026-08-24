import React, { useState } from 'react';
import { uploadBatchCSV } from '../api/client';
import { UploadCloud, FileText, X, AlertTriangle, CheckCircle2 } from 'lucide-react';

export default function BatchUploadModal({ onClose, onSuccess }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setError('');

    try {
      await uploadBatchCSV(file);
      onSuccess();
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to upload batch CSV.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="drawer-overlay" onClick={onClose} style={{ justifyContent: 'center', alignItems: 'center', padding: '20px' }}>
      <div className="rz-card" style={{ width: '100%', maxWidth: '540px', padding: '36px', background: '#ffffff', boxShadow: 'var(--rz-glass-shadow)', borderRadius: '20px' }} onClick={(e) => e.stopPropagation()}>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <h3 className="font-heading" style={{ fontSize: '1.4rem', fontWeight: '800', color: '#0f172a', letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <UploadCloud size={24} color="#0284c7" />
            <span>Batch Ingest Revenue Events</span>
          </h3>
          <button className="btn-rz-secondary" onClick={onClose} style={{ padding: '6px 12px', fontSize: '0.8rem', borderRadius: '8px' }}>
            <X size={16} />
          </button>
        </div>

        <p style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '24px', lineHeight: 1.5 }}>
          Upload synthetic or production transaction CSV datasets to trigger the multi-agent detection, MCP policy validation, and autonomous recovery pipeline.
        </p>

        {error && (
          <div style={{ padding: '14px 18px', borderRadius: '10px', background: '#fff1f2', border: '1px solid #fecdd3', color: '#b91c1c', fontSize: '0.85rem', marginBottom: '20px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={18} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ border: '2px dashed #0284c7', borderRadius: '16px', padding: '40px 24px', textAlign: 'center', marginBottom: '28px', background: 'linear-gradient(180deg, #f0f9ff 0%, #e0f2fe 100%)', transition: 'all 0.2s ease', cursor: 'pointer' }}>
            <input 
              type="file" 
              accept=".csv" 
              onChange={(e) => setFile(e.target.files[0])}
              style={{ display: 'none' }}
              id="csv-input"
            />
            <label htmlFor="csv-input" style={{ cursor: 'pointer', display: 'block' }}>
              <div style={{ width: '56px', height: '56px', borderRadius: '50%', background: '#ffffff', color: '#0284c7', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 14px auto', boxShadow: '0 4px 14px rgba(2, 132, 199, 0.2)' }}>
                <FileText size={28} />
              </div>
              <div style={{ fontWeight: '800', color: '#0284c7', marginBottom: '4px', fontSize: '1rem' }}>
                {file ? file.name : 'Click to select synthetic_transactions.csv'}
              </div>
              <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
                {file ? `${(file.size / 1024).toFixed(1)} KB CSV file selected` : 'Supports standard ReviveAI event schema CSV format'}
              </div>
            </label>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
            <button type="button" className="btn-rz-secondary" onClick={onClose} disabled={loading} style={{ padding: '10px 20px' }}>
              Cancel
            </button>
            <button type="submit" className="btn-rz-primary" disabled={!file || loading} style={{ padding: '10px 24px' }}>
              {loading ? 'Processing Pipeline...' : 'Upload & Execute Pipeline'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
