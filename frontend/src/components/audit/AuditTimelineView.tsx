import React, { useState } from 'react';
import { AuditEvent } from '../../types';
import {
  FileTextIcon,
  FilterIcon,
  ClockIcon,
} from '../common/Icons';

interface AuditTimelineViewProps {
  events: AuditEvent[];
}

export const AuditTimelineView: React.FC<AuditTimelineViewProps> = ({ events }) => {
  const [filterType, setFilterType] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const filteredEvents = events.filter((ev) => {
    if (filterType !== 'all' && ev.event_type !== filterType) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        ev.description.toLowerCase().includes(q) ||
        ev.actor.toLowerCase().includes(q) ||
        (ev.incident_id && ev.incident_id.toLowerCase().includes(q)) ||
        ev.entity_reference.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const uniqueEventTypes = Array.from(new Set(events.map((e) => e.event_type)));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header and Filter Controls */}
      <section className="card" aria-label="Audit Timeline Controls">
        <div className="card-header">
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FileTextIcon size={22} /> Chronological Operational Audit Trail
            </h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Deterministic log of telemetry alerts, algorithm evaluations, operator approvals, driver dispatch, and intake events.
            </p>
          </div>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Showing {filteredEvents.length} of {events.length} events
          </span>
        </div>

        <div style={{ display: 'flex', gap: '16px', alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-secondary)', fontWeight: 600 }}>
            <FilterIcon size={16} /> Filters:
          </div>

          <div style={{ minWidth: '220px' }}>
            <label htmlFor="audit-type-filter" className="sr-only">
              Filter Event Type
            </label>
            <select
              id="audit-type-filter"
              className="form-select"
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              style={{ minHeight: '36px', padding: '4px 8px', fontSize: '0.85rem' }}
            >
              <option value="all">All Event Types</option>
              {uniqueEventTypes.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          <div style={{ flex: 1, minWidth: '220px' }}>
            <label htmlFor="audit-search" className="sr-only">
              Search by actor or reference
            </label>
            <input
              id="audit-search"
              type="text"
              className="form-input"
              placeholder="Search description, actor, incident, or reference..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ minHeight: '36px', padding: '4px 10px', fontSize: '0.85rem' }}
            />
          </div>

          {(filterType !== 'all' || searchQuery.trim()) && (
            <button
              className="btn btn-secondary"
              onClick={() => {
                setFilterType('all');
                setSearchQuery('');
              }}
              style={{ minHeight: '36px', padding: '4px 12px', fontSize: '0.8rem' }}
            >
              Reset
            </button>
          )}
        </div>
      </section>

      {/* Timeline Stream */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {filteredEvents.map((ev) => {
          const outcomeColor =
            ev.outcome === 'success'
              ? 'var(--status-safe-border)'
              : ev.outcome === 'blocked'
              ? 'var(--status-blocked-border)'
              : 'var(--status-critical-border)';

          return (
            <div
              key={ev.event_id}
              className="card"
              style={{
                borderLeft: `4px solid ${outcomeColor}`,
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
                padding: '14px 18px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: 'var(--text-muted)' }}>
                    {ev.event_id}
                  </span>
                  <span className="badge badge-pending">{ev.event_type}</span>
                  {ev.incident_id && (
                    <span
                      style={{
                        fontSize: '0.75rem',
                        fontFamily: 'monospace',
                        color: 'var(--accent-cyan)',
                        backgroundColor: 'var(--bg-elevated)',
                        padding: '2px 6px',
                        borderRadius: 'var(--radius-sm)',
                      }}
                    >
                      {ev.incident_id}
                    </span>
                  )}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  <ClockIcon size={14} />
                  <span>{new Date(ev.occurred_at).toLocaleTimeString()} UTC</span>
                  <span
                    style={{
                      fontSize: '0.7rem',
                      padding: '2px 6px',
                      borderRadius: 'var(--radius-sm)',
                      backgroundColor: 'var(--bg-secondary)',
                      color: 'var(--text-secondary)',
                    }}
                  >
                    {ev.source === 'simulated_local' ? 'Local Demo' : 'Live AWS'}
                  </span>
                </div>
              </div>

              <div style={{ fontSize: '0.9rem', color: 'var(--text-primary)', fontWeight: 500 }}>
                {ev.description}
              </div>

              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  fontSize: '0.75rem',
                  color: 'var(--text-secondary)',
                  borderTop: '1px solid var(--border-subtle)',
                  paddingTop: '6px',
                  marginTop: '2px',
                }}
              >
                <div>
                  Actor: <strong>{ev.actor}</strong> | Ref:{' '}
                  <span style={{ fontFamily: 'monospace' }}>{ev.entity_reference}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  Outcome:{' '}
                  {ev.outcome === 'success' ? (
                    <span style={{ color: 'var(--status-safe)', fontWeight: 700 }}>SUCCESS</span>
                  ) : ev.outcome === 'blocked' ? (
                    <span style={{ color: 'var(--status-blocked)', fontWeight: 700 }}>POLICY BLOCKED</span>
                  ) : (
                    <span style={{ color: 'var(--status-critical)', fontWeight: 700 }}>FAILURE</span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
