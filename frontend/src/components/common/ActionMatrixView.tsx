import React, { useState } from 'react';
import { ACTION_MATRIX } from '../../data/mockData';
import { FileTextIcon } from './Icons';

export const ActionMatrixView: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState<string>('');

  const filteredActions = ACTION_MATRIX.filter((a) => {
    if (!searchTerm.trim()) return true;
    const term = searchTerm.toLowerCase();
    return (
      a.action_name.toLowerCase().includes(term) ||
      a.screen.toLowerCase().includes(term) ||
      a.initiating_control.toLowerCase().includes(term) ||
      a.audit_effect.toLowerCase().includes(term)
    );
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <section className="card" aria-label="Action Matrix Overview">
        <div className="card-header">
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FileTextIcon size={22} /> Consequential Action Contracts Matrix
            </h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Complete behavioral specification of every consequential UI state transition, validation boundary, and audit side effect.
            </p>
          </div>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            {filteredActions.length} Actions Specified
          </span>
        </div>

        <div style={{ maxWidth: '400px' }}>
          <input
            type="text"
            className="form-input"
            placeholder="Filter action contracts by name or screen..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ minHeight: '36px' }}
          />
        </div>
      </section>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {filteredActions.map((act, idx) => (
          <article
            key={idx}
            className="card"
            style={{
              borderLeft: '4px solid var(--accent-cyan)',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 700, margin: 0 }}>
                {idx + 1}. {act.action_name}
              </h3>
              <div style={{ display: 'flex', gap: '6px' }}>
                <span className="badge badge-pending">{act.screen}</span>
                <span
                  style={{
                    fontSize: '0.7rem',
                    padding: '2px 6px',
                    borderRadius: 'var(--radius-sm)',
                    backgroundColor: act.source_type === 'demo_local' ? 'var(--bg-elevated)' : 'var(--status-safe-bg)',
                    color: act.source_type === 'demo_local' ? 'var(--text-secondary)' : 'var(--status-safe)',
                    fontWeight: 600,
                  }}
                >
                  {act.source_type === 'demo_local' ? 'Demo Local Engine' : 'Live API Connected'}
                </span>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px', fontSize: '0.85rem', marginTop: '6px' }}>
              <div>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', display: 'block' }}>INITIATING CONTROL:</span>
                <strong>{act.initiating_control}</strong>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', display: 'block' }}>REQUIRED INPUTS:</span>
                <strong>{act.required_input}</strong>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', display: 'block' }}>PRECONDITIONS:</span>
                <div>{act.preconditions}</div>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', display: 'block' }}>EXPECTED SUCCESS OUTCOME:</span>
                <div style={{ color: 'var(--status-safe)' }}>{act.expected_success}</div>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', display: 'block' }}>VALIDATION FAILURES:</span>
                <div style={{ color: 'var(--status-critical)' }}>{act.validation_failure}</div>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', display: 'block' }}>DUPLICATE SUBMISSION PROTECTION:</span>
                <div>{act.duplicate_behavior}</div>
              </div>
            </div>

            <div
              style={{
                marginTop: '6px',
                paddingTop: '6px',
                borderTop: '1px solid var(--border-subtle)',
                fontSize: '0.75rem',
                color: 'var(--text-muted)',
              }}
            >
              Audit Impact: <strong>{act.audit_effect}</strong>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
};
