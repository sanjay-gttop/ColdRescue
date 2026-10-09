import React from 'react';
import { Incident } from '../../types';
import { StatusBadge } from '../common/StatusBadge';
import { CountdownTimer } from '../common/CountdownTimer';
import {
  ThermometerIcon,
  ZapIcon,
  BatteryChargingIcon,
  MapPinIcon,
  ClockIcon,
  WarehouseIcon,
  ArrowLeftIcon,
} from '../common/Icons';

interface IncidentDetailViewProps {
  incident: Incident;
  onBack: () => void;
  onSelectReceiverForIncident: (incidentId: string) => void;
  onCompareAllocation: () => void;
}

export const IncidentDetailView: React.FC<IncidentDetailViewProps> = ({
  incident,
  onBack,
  onSelectReceiverForIncident,
  onCompareAllocation,
}) => {
  const cargo = incident.cargo;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top action header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <button className="btn btn-secondary" onClick={onBack}>
          <ArrowLeftIcon size={16} /> Back to Incidents
        </button>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button className="btn btn-secondary" onClick={onCompareAllocation}>
            Compare Recovery Allocation
          </button>
          <button className="btn btn-primary" onClick={() => onSelectReceiverForIncident(incident.incident_id)}>
            <WarehouseIcon size={16} /> Select Candidate Receiver
          </button>
        </div>
      </div>

      {/* Main Incident Banner */}
      <div className="card" style={{ borderLeft: `6px solid ${incident.severity === 'critical' ? 'var(--status-critical-border)' : 'var(--status-warning-border)'}` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '0.85rem', fontFamily: 'monospace', color: 'var(--text-muted)' }}>
                {incident.incident_id}
              </span>
              <StatusBadge status={incident.severity} />
              <StatusBadge status={incident.status} />
            </div>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 800, marginTop: '6px' }}>{incident.title}</h2>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginTop: '6px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <MapPinIcon size={16} /> {incident.location}
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <ClockIcon size={16} /> Detected: {new Date(incident.detected_at).toLocaleTimeString()} UTC
              </span>
            </div>
          </div>

          <div style={{ textAlign: 'right' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>POWER FAILURE CATEGORY</span>
            <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--status-warning)', textTransform: 'uppercase' }}>
              {incident.power_failure_type.replace(/_/g, ' ')}
            </div>
          </div>
        </div>
      </div>

      {/* Thermal & Spoilage Countdown Card */}
      <CountdownTimer
        deadlineIso={cargo.spoilage_deadline}
        estimateSource={cargo.estimate_source}
        confidence={cargo.estimate_confidence}
      />

      {/* Two Column Grid: Cargo Constraints & Power/Cooling State */}
      <div className="grid-cols-2">
        {/* Column 1: Cargo Specifications */}
        <section className="card" aria-label="Cargo Telemetry and Thermal Limits">
          <div className="card-header">
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ThermometerIcon size={18} /> Cargo Thermal Constraints
            </h3>
            <span style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: 'var(--accent-cyan)' }}>
              {cargo.cargo_id}
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '8px', borderBottom: '1px solid var(--border-subtle)' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Cargo Classification:</span>
              <strong style={{ color: 'var(--text-primary)' }}>{cargo.cargo_type}</strong>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '8px', borderBottom: '1px solid var(--border-subtle)' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Verified Cargo Mass:</span>
              <strong style={{ color: 'var(--text-primary)' }}>{cargo.cargo_kg.toLocaleString()} kg</strong>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '8px', borderBottom: '1px solid var(--border-subtle)' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Current Sensor Temp:</span>
              <strong
                style={{
                  color:
                    cargo.current_temperature_c === null
                      ? 'var(--status-unknown)'
                      : cargo.current_temperature_c > cargo.safe_temperature_max || cargo.current_temperature_c < cargo.safe_temperature_min
                      ? 'var(--status-critical)'
                      : 'var(--status-safe)',
                  fontSize: '1.1rem',
                }}
              >
                {cargo.current_temperature_c !== null ? `${cargo.current_temperature_c.toFixed(1)}°C` : 'SENSOR UNREACHABLE'}
              </strong>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '8px', borderBottom: '1px solid var(--border-subtle)' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Mandatory Safe Range:</span>
              <strong style={{ color: 'var(--accent-cyan)' }}>
                {cargo.safe_temperature_min}°C to {cargo.safe_temperature_max}°C
              </strong>
            </div>

            <div style={{ backgroundColor: 'var(--bg-elevated)', padding: '10px', borderRadius: 'var(--radius-sm)', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              ℹ️ Strict biological tolerance. Any excursion above {cargo.safe_temperature_max}°C exceeding 60 cumulative minutes triggers irreversible denaturation.
            </div>
          </div>
        </section>

        {/* Column 2: Power, Cooling & Backup Power Status (Requirement 3) */}
        <section className="card" aria-label="Reefer Power and Cooling Telemetry">
          <div className="card-header">
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ZapIcon size={18} /> Electrical & Cooling Plant Status
            </h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Freshness: {new Date(incident.runtime_last_updated).toLocaleTimeString()}
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '8px', borderBottom: '1px solid var(--border-subtle)' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Power Grid / Bus State:</span>
              <StatusBadge status={incident.power_state} />
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '8px', borderBottom: '1px solid var(--border-subtle)' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Active Compressor Cooling:</span>
              <StatusBadge status={incident.cooling_status} />
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '8px', borderBottom: '1px solid var(--border-subtle)' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Backup Power Source:</span>
              <strong>{incident.backup_power_source || 'None / Inoperable'}</strong>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '8px', borderBottom: '1px solid var(--border-subtle)' }}>
              <span style={{ color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <BatteryChargingIcon size={16} /> Remaining Backup Runtime:
              </span>
              <strong
                style={{
                  color:
                    incident.backup_runtime_min === null
                      ? 'var(--status-unknown)'
                      : incident.backup_runtime_min < 60
                      ? 'var(--status-critical)'
                      : 'var(--status-safe)',
                  fontSize: '1.05rem',
                }}
              >
                {incident.backup_runtime_min !== null ? `${incident.backup_runtime_min} mins` : 'UNKNOWN (Sensor Offline)'}
              </strong>
            </div>

            <div
              style={{
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid rgba(239, 68, 68, 0.25)',
                padding: '10px',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.8rem',
                color: '#fca5a5',
              }}
            >
              ⚠️ <strong>Safety Rule Enforced:</strong> Backup power presence does not infer operational cooling. Cooling is confirmed {incident.cooling_status.toUpperCase()}.
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};
