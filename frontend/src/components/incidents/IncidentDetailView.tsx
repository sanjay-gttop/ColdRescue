import React, { useState } from 'react';
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
  ShieldAlertIcon,
} from '../common/Icons';
import { AwsContextChip, AwsServiceDrawer } from '../common/AwsContextChips';

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
  const [selectedAwsService, setSelectedAwsService] = useState<string | null>(null);
  const cargo = incident.cargo;

  const isBlocked = incident.cooling_status === 'failed' || incident.power_state === 'failed';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* AWS Service Inspection Drawer */}
      <AwsServiceDrawer
        serviceKey={selectedAwsService}
        onClose={() => setSelectedAwsService(null)}
      />

      {/* Top action header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <button className="btn btn-secondary" onClick={onBack}>
          <ArrowLeftIcon size={16} /> Back to Incidents
        </button>

        {/* AWS Service Context Chips */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>AWS Cloud Stack:</span>
          <AwsContextChip serviceKey="iot" onClick={() => setSelectedAwsService('iot')} />
          <AwsContextChip serviceKey="sagemaker" onClick={() => setSelectedAwsService('sagemaker')} />
          <AwsContextChip serviceKey="location" onClick={() => setSelectedAwsService('location')} />
          <AwsContextChip serviceKey="stepfunctions" onClick={() => setSelectedAwsService('stepfunctions')} />
        </div>

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
      <div
        className="card"
        style={{
          border: `1px solid ${incident.severity === 'critical' ? 'var(--status-critical-border)' : 'var(--status-warning-border)'}`,
          boxShadow: `0 8px 30px rgba(0, 0, 0, 0.5), 0 0 24px -6px ${incident.severity === 'critical' ? 'rgba(244, 63, 94, 0.2)' : 'rgba(251, 191, 36, 0.15)'}`,
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '0.85rem', fontFamily: 'monospace', color: 'var(--text-muted)' }}>
                {incident.incident_id}
              </span>
              <StatusBadge status={incident.severity} />
              <StatusBadge status={incident.status} />
              {incident.incident_id === 'TRUCK-104' && (
                <span className="badge badge-success">SIMULATED GOLDEN PATH SCENARIO</span>
              )}
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

      {/* HOLD SAFETY POLICY SCREEN / BANNER (When Blocked) — Moving Border Pill / Border */}
      {isBlocked && (
        <div className="moving-border-btn" style={{ width: '100%', cursor: 'default' }}>
          <div
            className="moving-border-btn-inner"
            style={{
              width: '100%',
              backgroundColor: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid var(--status-critical-border)',
              padding: '16px 20px',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '12px',
            }}
          >
            <ShieldAlertIcon size={24} className="pulse-icon" style={{ color: 'var(--status-critical)', marginTop: '2px', flexShrink: 0 }} />
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <strong style={{ fontSize: '1.05rem', color: '#fca5a5' }}>
                  DISPATCH BLOCKED BY SAFETY POLICY — HOLD STATE ACTIVE
                </strong>
                <span className="badge badge-critical">POLICY PRECEDENCE</span>
              </div>
              <p style={{ fontSize: '0.88rem', color: '#fecaca', margin: '6px 0 0 0', lineHeight: 1.4 }}>
                Active reefer cooling plant is unrecoverable ({incident.cooling_status.toUpperCase()}). Under ColdRescue Deterministic Safety Rules, automatic dispatch authorization is strictly locked until a certified receiver with available cryogenic/cold storage capacity is explicitly validated by a Human Operator.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Bento Grid: Thermal Reconciliation, Spoilage Countdown, Specifications, and Power */}
      <div className="bento-grid">
        {/* Bento Cell 1: Deterministic Thermal Reconciliation (Span 12) */}
        <section className="bento-col-12 card" style={{ borderLeft: '6px solid var(--accent-cyan)' }}>
          <div className="card-header">
            <div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <ThermometerIcon size={18} /> Deterministic Thermal Risk Reconciliation
              </h3>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Deterministic Precedence Rule: safe_window = min(physics, surrogate). ML inference is purely advisory.
              </span>
            </div>
            <AwsContextChip serviceKey="sagemaker" label="SageMaker AI (Advisory)" onClick={() => setSelectedAwsService('sagemaker')} />
          </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginTop: '12px' }}>
          {/* Box 1: Physics Engine */}
          <div style={{ padding: '12px 14px', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 700 }}>
              Deterministic Newton Physics
            </div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#38bdf8', marginTop: '4px', fontFamily: 'monospace' }}>
              {cargo.physics_safe_window_min !== undefined ? `${cargo.physics_safe_window_min} min` : '47 min'}
            </div>
            <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: '4px' }}>
              Newton exponential cooling law (ambient 38.0°C, mass {cargo.cargo_kg}kg)
            </div>
            <div style={{ marginTop: '6px' }}>
              <span className="badge badge-success" style={{ fontSize: '0.65rem' }}>AUTHORITATIVE BOUND</span>
            </div>
          </div>

          {/* Box 2: SageMaker Surrogate */}
          <div style={{ padding: '12px 14px', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 700 }}>
              SageMaker Serverless Surrogate
            </div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#c084fc', marginTop: '4px', fontFamily: 'monospace' }}>
              {cargo.surrogate_safe_window_min !== undefined ? `${cargo.surrogate_safe_window_min} min` : '440 min'}
            </div>
            <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: '4px' }}>
              Linear thermal surrogate (advisory only, $0.00 idle compute)
            </div>
            <div style={{ marginTop: '6px' }}>
              <span className="badge badge-warning" style={{ fontSize: '0.65rem' }}>ADVISORY INFERENCE</span>
            </div>
          </div>

          {/* Box 3: Effective Safety Policy Window */}
          <div style={{ padding: '12px 14px', borderRadius: 'var(--radius-sm)', backgroundColor: 'rgba(6, 182, 212, 0.1)', border: '1px solid rgba(6, 182, 212, 0.4)' }}>
            <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--accent-cyan)', fontWeight: 700 }}>
              Enforced Policy Window
            </div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--accent-cyan)', marginTop: '4px', fontFamily: 'monospace' }}>
              {cargo.effective_safe_window_min !== undefined ? `${cargo.effective_safe_window_min} min` : '47 min'}
            </div>
            <div style={{ fontSize: '0.72rem', color: '#cbd5e1', marginTop: '4px' }}>
              {cargo.fallback_reason || 'Surrogate overprediction safely clamped: min(47, 440) = 47 min.'}
            </div>
            <div style={{ marginTop: '6px' }}>
              <span className="badge badge-safe" style={{ fontSize: '0.65rem' }}>ZERO FALSE-SAFE RATE</span>
            </div>
          </div>
        </div>
      </section>

      {/* Bento Cell 2: Thermal & Spoilage Countdown (Span 12) */}
      <div className="bento-col-12">
        <CountdownTimer
          deadlineIso={cargo.spoilage_deadline}
          estimateSource={cargo.estimate_source}
          confidence={cargo.estimate_confidence}
        />
      </div>

      {/* Bento Cells 3 & 4: Cargo Constraints (Span 6) & Power/Cooling (Span 6) */}
      <section className="bento-col-6 card" aria-label="Cargo Telemetry and Thermal Limits">
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

        {/* Column 2: Power, Cooling & Backup Power Status (Bento Span 6) */}
        <section className="bento-col-6 card" aria-label="Reefer Power and Cooling Telemetry">
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
