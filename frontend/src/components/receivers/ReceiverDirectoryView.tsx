import React, { useState } from 'react';
import { Receiver, Incident } from '../../types';
import { StatusBadge } from '../common/StatusBadge';
import { evaluateColdChainPolicy } from '../../utils/policyEngine';
import {
  MapPinIcon,
  FilterIcon,
  CheckCircleIcon,
  XCircleIcon,
  AlertTriangleIcon,
} from '../common/Icons';

interface ReceiverDirectoryViewProps {
  receivers: Receiver[];
  activeIncident?: Incident;
  onSelectReceiverProposal: (receiverId: string) => void;
  onInspectPolicyBlock: (receiverId: string) => void;
}

export const ReceiverDirectoryView: React.FC<ReceiverDirectoryViewProps> = ({
  receivers,
  activeIncident,
  onSelectReceiverProposal,
  onInspectPolicyBlock,
}) => {
  const [filterCompat, setFilterCompat] = useState<string>('all');
  const [filterMinCap, setFilterMinCap] = useState<number>(0);
  const [filterAvailability, setFilterAvailability] = useState<string>('all');

  const filteredReceivers = receivers.filter((r) => {
    if (filterCompat !== 'all' && !r.compatible_cargo_types.includes(filterCompat)) {
      return false;
    }
    if (r.available_capacity_kg < filterMinCap) {
      return false;
    }
    if (filterAvailability !== 'all' && r.operational_availability !== filterAvailability) {
      return false;
    }
    return true;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Incident Context Indicator if an incident is in context */}
      {activeIncident && (
        <div
          className="card"
          style={{
            backgroundColor: 'var(--bg-elevated)',
            borderLeft: '4px solid var(--accent-cyan)',
            padding: '12px 18px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
            <div>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                EVALUATING RECEIVERS FOR ACTIVE INCIDENT:
              </span>
              <div style={{ fontWeight: 700, fontSize: '1rem' }}>
                {activeIncident.incident_id} — {activeIncident.title} ({activeIncident.cargo.cargo_type},{' '}
                {activeIncident.cargo.cargo_kg} kg)
              </div>
            </div>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              Required Temp: {activeIncident.cargo.safe_temperature_min}°C to {activeIncident.cargo.safe_temperature_max}°C
            </span>
          </div>
        </div>
      )}

      {/* Filter Toolbar */}
      <section className="card" aria-label="Receiver Filters">
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-secondary)', fontWeight: 600, fontSize: '0.9rem' }}>
            <FilterIcon size={18} /> Filters:
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', minWidth: '180px' }}>
            <label htmlFor="filter-compat" className="form-label" style={{ margin: 0 }}>
              Cargo Compatibility
            </label>
            <select
              id="filter-compat"
              className="form-select"
              value={filterCompat}
              onChange={(e) => setFilterCompat(e.target.value)}
              style={{ minHeight: '36px', padding: '4px 8px', fontSize: '0.85rem' }}
            >
              <option value="all">All Cargo Certifications</option>
              <option value="mRNA Vaccines">mRNA Vaccines</option>
              <option value="Biologics / Insulin">Biologics / Insulin</option>
              <option value="Fresh Platelets">Fresh Platelets</option>
              <option value="Frozen Seafood">Frozen Seafood</option>
            </select>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', minWidth: '160px' }}>
            <label htmlFor="filter-avail" className="form-label" style={{ margin: 0 }}>
              Operational Status
            </label>
            <select
              id="filter-avail"
              className="form-select"
              value={filterAvailability}
              onChange={(e) => setFilterAvailability(e.target.value)}
              style={{ minHeight: '36px', padding: '4px 8px', fontSize: '0.85rem' }}
            >
              <option value="all">All Statuses</option>
              <option value="available">Available Only</option>
              <option value="at_capacity">At Capacity</option>
              <option value="offline">Offline / Faulted</option>
            </select>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', minWidth: '160px' }}>
            <label htmlFor="filter-min-cap" className="form-label" style={{ margin: 0 }}>
              Min Available: {filterMinCap} kg
            </label>
            <input
              id="filter-min-cap"
              type="range"
              min={0}
              max={10000}
              step={500}
              value={filterMinCap}
              onChange={(e) => setFilterMinCap(Number(e.target.value))}
              style={{ accentColor: 'var(--accent-cyan)' }}
            />
          </div>

          {(filterCompat !== 'all' || filterMinCap > 0 || filterAvailability !== 'all') && (
            <button
              className="btn btn-secondary"
              onClick={() => {
                setFilterCompat('all');
                setFilterMinCap(0);
                setFilterAvailability('all');
              }}
              style={{ minHeight: '36px', padding: '4px 12px', fontSize: '0.8rem', alignSelf: 'flex-end' }}
            >
              Reset Filters
            </button>
          )}
        </div>
      </section>

      {/* Receiver Cards Grid */}
      <div className="grid-cols-2">
        {filteredReceivers.map((r) => {
          // Pre-evaluate policy if incident is active
          const policy = activeIncident ? evaluateColdChainPolicy(activeIncident, r) : null;
          const isFeasible = policy ? !policy.is_hard_blocked : r.operational_availability === 'available';

          return (
            <div key={r.receiver_id} className="card-3d-wrap">
              <article
                className="card card-3d"
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  borderLeft: `4px solid ${
                    !isFeasible ? 'var(--status-blocked-border)' : 'var(--status-safe-border)'
                  }`,
                }}
              >
              <div>
                <div className="card-header">
                  <div>
                    <span style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: 'var(--text-muted)' }}>
                      {r.receiver_id}
                    </span>
                    <h3 style={{ fontSize: '1.15rem', fontWeight: 700, margin: '2px 0' }}>{r.name}</h3>
                  </div>
                  <StatusBadge status={r.operational_availability} />
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.85rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-secondary)' }}>
                    <MapPinIcon size={16} /> {r.location} ({r.distance_km} km / {r.travel_time_min} mins transit)
                  </div>

                  {/* Capacity Bar */}
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span style={{ color: 'var(--text-secondary)' }}>Available Space:</span>
                      <strong>
                        {r.available_capacity_kg.toLocaleString()} / {r.total_capacity_kg.toLocaleString()} kg
                      </strong>
                    </div>
                    <div
                      style={{
                        height: '6px',
                        backgroundColor: 'var(--bg-elevated)',
                        borderRadius: 'var(--radius-full)',
                        overflow: 'hidden',
                      }}
                    >
                      <div
                        style={{
                          height: '100%',
                          width: `${Math.min(100, Math.round(((r.total_capacity_kg - r.available_capacity_kg) / r.total_capacity_kg) * 100))}%`,
                          backgroundColor: r.available_capacity_kg < 1000 ? 'var(--status-warning)' : 'var(--status-safe)',
                        }}
                      />
                    </div>
                  </div>

                  {/* Thermal Capability */}
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Thermal Range:</span>
                    <strong style={{ color: 'var(--accent-cyan)' }}>
                      {r.temp_range_min}°C to {r.temp_range_max}°C
                    </strong>
                  </div>

                  {/* Power & Cooling State */}
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Cooling Status:</span>
                    <StatusBadge status={r.cooling_status} />
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Backup Power:</span>
                    <span>
                      {r.backup_runtime_min !== null ? `${r.backup_runtime_min} min runtime` : 'UNKNOWN'}
                    </span>
                  </div>

                  {/* Certified Cargo Tags */}
                  <div>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', display: 'block', marginBottom: '4px' }}>
                      Certified Cargo Compatibility:
                    </span>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                      {r.compatible_cargo_types.map((type) => (
                        <span
                          key={type}
                          style={{
                            fontSize: '0.7rem',
                            padding: '2px 6px',
                            backgroundColor: 'var(--bg-elevated)',
                            borderRadius: 'var(--radius-sm)',
                            color: 'var(--text-secondary)',
                          }}
                        >
                          {type}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Incident Feasibility Warning / Notice */}
                  {activeIncident && policy && (
                    <div
                      style={{
                        marginTop: '8px',
                        padding: '8px 12px',
                        borderRadius: 'var(--radius-sm)',
                        backgroundColor: policy.is_hard_blocked ? 'rgba(239, 68, 68, 0.12)' : 'rgba(16, 185, 129, 0.12)',
                        border: `1px solid ${policy.is_hard_blocked ? 'var(--status-blocked-border)' : 'var(--status-safe-border)'}`,
                        fontSize: '0.8rem',
                      }}
                    >
                      {policy.is_hard_blocked ? (
                        <div style={{ color: '#fca5a5' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700 }}>
                            <XCircleIcon size={16} /> Hard Safety Policy Violation:
                          </div>
                          <div style={{ fontSize: '0.75rem', marginTop: '2px' }}>
                            {policy.hard_block_reasons[0]}
                          </div>
                        </div>
                      ) : (
                        <div style={{ color: '#6ee7b7', display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 600 }}>
                          <CheckCircleIcon size={16} /> Feasible & Safe for {activeIncident.incident_id}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Action Buttons */}
              <div style={{ marginTop: '16px', display: 'flex', gap: '8px' }}>
                {activeIncident && (
                  <>
                    {isFeasible ? (
                      <button
                        className="btn btn-primary"
                        onClick={() => onSelectReceiverProposal(r.receiver_id)}
                        style={{ flex: 1 }}
                      >
                        Propose Receiver For Incident
                      </button>
                    ) : (
                      <button
                        className="btn btn-danger"
                        onClick={() => onInspectPolicyBlock(r.receiver_id)}
                        style={{ flex: 1 }}
                      >
                        <AlertTriangleIcon size={16} /> Inspect Policy Block
                      </button>
                    )}
                  </>
                )}
                {!activeIncident && (
                  <button
                    className="btn btn-secondary"
                    onClick={() => onInspectPolicyBlock(r.receiver_id)}
                    style={{ flex: 1 }}
                  >
                    Inspect Facility Rules
                  </button>
                )}
              </div>
            </article>
          </div>
        );
      })}
    </div>
    </div>
  );
};
