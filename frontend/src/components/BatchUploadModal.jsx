import React, { useState } from 'react';
import { uploadBatchCSV } from '../api/client';

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
    <div className="drawer-overlay" onClick={onClose} style={{ justifyContent: 'center', alignItems: 'center', padding: '16px' }}>
      <div className="rz-card" style={{ width: '100%', maxWidth: '520px', padding: '36px', background: '#ffffff', boxShadow: '0 25px 60px rgba(2, 4, 43, 0.25)' }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <h3 className="font-heading" style={{ fontSize: '1.4rem', fontWeight: '800', color: '#0f172a', letterSpacing: '-0.01em' }}>
            📥 Batch Ingest Revenue Events
          </h3>
          <button className="btn-rz-secondary" onClick={onClose} style={{ padding: '4px 10px', fontSize: '0.8rem' }}>
            ✕
          </button>
        </div>

        <p style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '24px' }}>
          Upload a synthetic or production transaction CSV file to trigger the multi-agent detection and autonomous recovery pipeline.
        </p>

        {error && (
          <div style={{ padding: '12px 16px', borderRadius: '8px', background: '#fff1f2', border: '1px solid #fecdd3', color: '#b91c1c', fontSize: '0.85rem', marginBottom: '20px', fontWeight: '600' }}>
            ⚠️ {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ border: '2px dashed #0284c7', borderRadius: '14px', padding: '36px 20px', textAlign: 'center', marginBottom: '24px', background: '#f0f9ff', transition: 'all 0.2s ease' }}>
            <input 
              type="file" 
              accept=".csv" 
              onChange={(e) => setFile(e.target.files[0])}
              style={{ display: 'none' }}
              id="csv-input"
            />
            <label htmlFor="csv-input" style={{ cursor: 'pointer', display: 'block' }}>
              <div style={{ fontSize: '2.5rem', marginBottom: '10px' }}>📄</div>
              <div style={{ fontWeight: '800', color: '#0284c7', marginBottom: '4px', fontSize: '0.95rem' }}>
                {file ? file.name : 'Click or Drag synthetic_transactions.csv'}
              </div>
              <div style={{ fontSize: '0.775rem', color: '#64748b' }}>Format: CSV file containing event metadata</div>
            </label>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
            <button type="button" className="btn-rz-secondary" onClick={onClose} disabled={loading}>
              Cancel
            </button>
            <button type="submit" className="btn-rz-primary" disabled={!file || loading}>
              {loading ? 'Processing Pipeline...' : 'Upload & Process Batch'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
