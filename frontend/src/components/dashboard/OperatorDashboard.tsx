import React from 'react';
import { Incident, Receiver, ApprovalRequest, AuditEvent } from '../../types';
import { StatusBadge } from '../common/StatusBadge';
import {
  ShieldAlertIcon,
  ThermometerIcon,
  WarehouseIcon,
  UserCheckIcon,
  ChevronRightIcon,
  ZapIcon,
  SnowflakeIcon,
} from '../common/Icons';

interface OperatorDashboardProps {
  incidents: Incident[];
  receivers: Receiver[];
  approvals: ApprovalRequest[];
  auditEvents: AuditEvent[];
  onSelectIncident: (incidentId: string) => void;
  onNavigateToApprovals: () => void;
  onNavigateToReceivers: () => void;
  onNavigateToAllocation: () => void;
  onNavigateToAudit: () => void;
  onNavigateToLiveTrace?: () => void;
}

export const OperatorDashboard: React.FC<OperatorDashboardProps> = ({
  incidents,
  receivers,
  approvals,
  auditEvents,
  onSelectIncident,
  onNavigateToApprovals,
  onNavigateToReceivers,
  onNavigateToAllocation,
  onNavigateToAudit,
  onNavigateToLiveTrace,
}) => {
  // Aggregate Metrics
  const activeIncidents = incidents.filter((i) => i.status !== 'resolved' && i.status !== 'delivered');
  const criticalOrHighCount = incidents.filter((i) => i.severity === 'critical' || i.severity === 'high').length;
  const totalCargoKgAtRisk = incidents.reduce((sum, i) => sum + i.cargo.cargo_kg, 0);

  const availableReceiversCount = receivers.filter((r) => r.operational_availability === 'available').length;
  const totalAvailableCapKg = receivers.reduce((sum, r) => sum + r.available_capacity_kg, 0);
  const pendingApprovalsCount = approvals.filter((a) => a.status === 'pending').length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Level Metric Cards */}
      <section aria-label="Key Operational Indicators" className="grid-cols-4">
        {/* Card 1: Active Incidents */}
        <div className="card" style={{ borderLeft: '4px solid var(--status-critical-border)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>ACTIVE INCIDENTS</span>
            <ShieldAlertIcon size={18} />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '10px', marginTop: '8px' }}>
            <span style={{ fontSize: '2.2rem', fontWeight: 800 }}>{activeIncidents.length}</span>
            <span style={{ fontSize: '0.85rem', color: 'var(--status-critical)', fontWeight: 700 }}>
              {criticalOrHighCount} CRITICAL / HIGH
            </span>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Power & cooling disruptions in transit
          </div>
        </div>

        {/* Card 2: Cargo at Risk */}
        <div className="card" style={{ borderLeft: '4px solid var(--status-warning-border)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>CARGO AT RISK</span>
            <ThermometerIcon size={18} />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '8px' }}>
            <span style={{ fontSize: '2.2rem', fontWeight: 800 }}>{totalCargoKgAtRisk.toLocaleString()}</span>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>KG TOTAL</span>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            mRNA, platelets, biologics undergoing heat ingress
          </div>
        </div>

        {/* Card 3: Receiving Vault Availability */}
        <div className="card" style={{ borderLeft: '4px solid var(--status-safe-border)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>RECEIVERS ONLINE</span>
            <WarehouseIcon size={18} />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '8px' }}>
            <span style={{ fontSize: '2.2rem', fontWeight: 800 }}>{availableReceiversCount}</span>
            <span style={{ fontSize: '0.85rem', color: 'var(--status-safe)', fontWeight: 600 }}>
              / {receivers.length} OPERATIONAL
            </span>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            {totalAvailableCapKg.toLocaleString()} kg total capacity reserve
          </div>
        </div>

        {/* Card 4: Pending Approvals */}
        <div className="card" style={{ borderLeft: '4px solid var(--status-pending-border)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>PENDING APPROVALS</span>
            <UserCheckIcon size={18} />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '8px' }}>
            <span style={{ fontSize: '2.2rem', fontWeight: 800 }}>{pendingApprovalsCount}</span>
            <span style={{ fontSize: '0.85rem', color: 'var(--status-pending)', fontWeight: 600 }}>AWAITING ACTION</span>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Operator review needed for recovery dispatch
          </div>
        </div>
      </section>

      {/* Main Grid: Active Incident Queue & Operational Overview */}
      <div className="grid-cols-3" style={{ alignItems: 'start' }}>
        {/* Left Column (2 span): Incident Queue */}
        <div style={{ gridColumn: 'span 2', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <section className="card" aria-label="Active Incident Queue">
            <div className="card-header">
              <div>
                <h2 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Active Incident Queue</h2>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  Click an incident row to inspect thermal telemetry and initiate recovery assignment
                </p>
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                {onNavigateToLiveTrace && (
                  <button
                    className="btn btn-primary"
                    onClick={onNavigateToLiveTrace}
                    style={{ fontSize: '0.8rem', padding: '6px 12px', display: 'flex', alignItems: 'center', gap: '6px' }}
                  >
                    <ZapIcon size={14} /> Run Live AWS Drill
                  </button>
                )}
                <button
                  className="btn btn-secondary"
                  onClick={onNavigateToAllocation}
                  style={{ fontSize: '0.8rem', padding: '6px 12px' }}
                >
                  Compare Allocations
                </button>
              </div>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-strong)', textAlign: 'left', color: 'var(--text-secondary)' }}>
                    <th style={{ padding: '10px 8px' }}>Incident / Truck</th>
                    <th style={{ padding: '10px 8px' }}>Cargo Type</th>
                    <th style={{ padding: '10px 8px' }}>Severity</th>
                    <th style={{ padding: '10px 8px' }}>Power / Cooling</th>
                    <th style={{ padding: '10px 8px' }}>Safe Window</th>
                    <th style={{ padding: '10px 8px', textAlign: 'right' }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {incidents.map((inc) => (
                    <tr
                      key={inc.incident_id}
                      style={{
                        borderBottom: '1px solid var(--border-subtle)',
                        cursor: 'pointer',
                        transition: 'background 0.15s ease',
                      }}
                      onClick={() => onSelectIncident(inc.incident_id)}
                      onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'var(--bg-card-hover)')}
                      onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          onSelectIncident(inc.incident_id);
                        }
                      }}
                      aria-label={`Inspect incident ${inc.incident_id}: ${inc.title}`}
                    >
                      <td style={{ padding: '12px 8px' }}>
                        <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{inc.incident_id}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{inc.location}</div>
                      </td>
                      <td style={{ padding: '12px 8px' }}>
                        <div>{inc.cargo.cargo_type}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{inc.cargo.cargo_kg} kg</div>
                      </td>
                      <td style={{ padding: '12px 8px' }}>
                        <StatusBadge status={inc.severity} />
                      </td>
                      <td style={{ padding: '12px 8px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <ZapIcon size={14} color={inc.power_state === 'operational' ? '#10b981' : '#f59e0b'} />
                          <span style={{ fontSize: '0.75rem' }}>{inc.power_state.toUpperCase()}</span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '2px' }}>
                          <SnowflakeIcon size={14} color={inc.cooling_status === 'operational' ? '#10b981' : '#ef4444'} />
                          <span style={{ fontSize: '0.75rem' }}>{inc.cooling_status.toUpperCase()}</span>
                        </div>
                      </td>
                      <td style={{ padding: '12px 8px' }}>
                        <div style={{ fontWeight: 600, color: inc.severity === 'critical' ? 'var(--status-critical)' : 'var(--text-primary)' }}>
                          {inc.cargo.spoilage_deadline ? '45 min est.' : 'Unknown'}
                        </div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{inc.cargo.estimate_source}</div>
                      </td>
                      <td style={{ padding: '12px 8px', textAlign: 'right' }}>
                        <button
                          className="btn btn-secondary"
                          style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectIncident(inc.incident_id);
                          }}
                        >
                          Details <ChevronRightIcon size={14} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>

        {/* Right Column: Approvals, Receivers & Recent Audits */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Pending Approvals Widget */}
          <section className="card" aria-label="Approvals Quick View">
            <div className="card-header">
              <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>Pending Approvals</h3>
              <button onClick={onNavigateToApprovals} style={{ fontSize: '0.75rem', color: 'var(--accent-cyan)' }}>
                View All ({approvals.length})
              </button>
            </div>
            {approvals.length === 0 ? (
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>No pending approvals.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {approvals.slice(0, 2).map((app) => (
                  <div
                    key={app.approval_id}
                    style={{
                      padding: '10px',
                      borderRadius: 'var(--radius-sm)',
                      backgroundColor: 'var(--bg-elevated)',
                      border: '1px solid var(--border-subtle)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontWeight: 700, fontSize: '0.85rem' }}>{app.approval_id}</span>
                      <StatusBadge status={app.status} />
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                      Target: <strong>{app.proposed_receiver_id}</strong>
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                      Safety: {app.policy_assessment.is_safe ? '✅ Verified Safe' : '⚠️ Requires Review'}
                    </div>
                    <button
                      className="btn btn-primary"
                      onClick={onNavigateToApprovals}
                      style={{ width: '100%', marginTop: '8px', minHeight: '34px', padding: '4px', fontSize: '0.75rem' }}
                    >
                      Review & Decide
                    </button>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Receiver Capacity Summary */}
          <section className="card" aria-label="Receiver Capacity Summary">
            <div className="card-header">
              <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>Receiver Facilities</h3>
              <button onClick={onNavigateToReceivers} style={{ fontSize: '0.75rem', color: 'var(--accent-cyan)' }}>
                Directory
              </button>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {receivers.slice(0, 3).map((r) => (
                <div
                  key={r.receiver_id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    fontSize: '0.85rem',
                    padding: '6px 0',
                    borderBottom: '1px solid var(--border-subtle)',
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 600 }}>{r.name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {r.available_capacity_kg.toLocaleString()} kg avail ({r.travel_time_min}m)
                    </div>
                  </div>
                  <StatusBadge status={r.operational_availability} />
                </div>
              ))}
            </div>
          </section>

          {/* Recent Audit Activity */}
          <section className="card" aria-label="Recent Audit Activity">
            <div className="card-header">
              <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>Recent System Audits</h3>
              <button onClick={onNavigateToAudit} style={{ fontSize: '0.75rem', color: 'var(--accent-cyan)' }}>
                Full Log
              </button>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {auditEvents.slice(0, 3).map((ev) => (
                <div key={ev.event_id} style={{ fontSize: '0.8rem', borderLeft: '2px solid var(--border-strong)', paddingLeft: '8px' }}>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{ev.event_type}</div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>{ev.description}</div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>
                    Actor: {ev.actor} ({ev.source})
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};
