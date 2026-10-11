import React from 'react';
import { Incident, Receiver, PolicyAssessment } from '../../types';
import { evaluateColdChainPolicy } from '../../utils/policyEngine';
import {
  XCircleIcon,
  ArrowRightIcon,
  ArrowLeftIcon,
  ShieldAlertIcon,
} from '../common/Icons';

interface PolicyBlockDetailViewProps {
  incident: Incident;
  receiver: Receiver;
  alternativeReceivers: Receiver[];
  onBack: () => void;
  onSelectAlternative: (receiverId: string) => void;
  onReevaluate: () => void;
}

export const PolicyBlockDetailView: React.FC<PolicyBlockDetailViewProps> = ({
  incident,
  receiver,
  alternativeReceivers,
  onBack,
  onSelectAlternative,
  onReevaluate,
}) => {
  const assessment: PolicyAssessment = evaluateColdChainPolicy(incident, receiver);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Banner */}
      <div
        className="card"
        style={{
          borderLeft: '6px solid var(--status-blocked-border)',
          backgroundColor: 'rgba(225, 29, 72, 0.08)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="badge badge-blocked">MANDATORY POLICY HARD-BLOCK</span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                RULE ENGINE ENFORCEMENT
              </span>
            </div>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 800, marginTop: '6px', color: '#fda4af' }}>
              Action Blocked: Proposed Allocation to {receiver.name} is Infeasible
            </h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Incident: <strong>{incident.incident_id}</strong> ({incident.cargo.cargo_type},{' '}
              {incident.cargo.cargo_kg} kg) → Target: <strong>{receiver.receiver_id}</strong>
            </p>
          </div>

          <button className="btn btn-secondary" onClick={onBack}>
            <ArrowLeftIcon size={16} /> Return to Directory
          </button>
        </div>
      </div>

      {/* Main Analysis Grid */}
      <div className="grid-cols-2">
        {/* Left: Violated Rules and Scientific Rationale */}
        <section className="card" aria-label="Specific Policy Rule Violations">
          <div className="card-header">
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--status-critical)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <XCircleIcon size={18} /> Hard Safety Violations
            </h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              {assessment.hard_block_reasons.length} Blocking Rules Triggered
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {assessment.hard_block_reasons.map((reason, idx) => (
              <div
                key={idx}
                style={{
                  padding: '12px',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: 'var(--status-critical-bg)',
                  border: '1px solid var(--status-critical-border)',
                  color: '#fca5a5',
                  fontSize: '0.85rem',
                }}
              >
                <div style={{ fontWeight: 700, display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <ShieldAlertIcon size={16} /> Violation #{idx + 1}
                </div>
                <div style={{ marginTop: '4px', lineHeight: 1.4 }}>{reason}</div>
              </div>
            ))}

            <div style={{ marginTop: '8px' }}>
              <h4 style={{ fontSize: '0.9rem', marginBottom: '8px' }}>Detailed Rule Matrix:</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {assessment.rule_evaluations.map((rule) => (
                  <div
                    key={rule.rule_id}
                    style={{
                      padding: '10px',
                      borderRadius: 'var(--radius-sm)',
                      backgroundColor: 'var(--bg-elevated)',
                      fontSize: '0.8rem',
                      borderLeft: `3px solid ${rule.passed ? 'var(--status-safe-border)' : 'var(--status-critical-border)'}`,
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <strong>{rule.rule_name}</strong>
                      <span style={{ color: rule.passed ? 'var(--status-safe)' : 'var(--status-critical)', fontWeight: 700 }}>
                        {rule.passed ? 'PASSED' : 'FAILED'}
                      </span>
                    </div>
                    <div style={{ color: 'var(--text-secondary)', marginTop: '2px' }}>{rule.details}</div>
                  </div>
                ))}
              </div>
            </div>

            <div
              style={{
                marginTop: '12px',
                padding: '12px',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--bg-secondary)',
                border: '1px solid var(--border-strong)',
                fontSize: '0.8rem',
                color: 'var(--text-muted)',
              }}
            >
              🔒 <strong>Safety Assurance:</strong> ColdRescue does NOT provide a manual override button for hard physical safety blocks. Cargo cannot be dispatched to a facility with failed cooling or insufficient capacity.
            </div>
          </div>
        </section>

        {/* Right: Feasible Alternatives and Next Permitted Actions */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <section className="card" aria-label="Feasible Alternative Facilities">
            <div className="card-header">
              <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>Next Permitted Action: Select Alternative</h3>
              <span style={{ fontSize: '0.75rem', color: 'var(--status-safe)' }}>Feasible Facilities</span>
            </div>

            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>
              The following facilities satisfy all thermal, capacity, and operational safety criteria for {incident.incident_id}:
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {alternativeReceivers.map((alt) => (
                <div
                  key={alt.receiver_id}
                  style={{
                    padding: '12px',
                    borderRadius: 'var(--radius-sm)',
                    backgroundColor: 'var(--bg-elevated)',
                    border: '1px solid var(--status-safe-border)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <div>
                    <strong style={{ fontSize: '0.95rem' }}>{alt.name}</strong>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      Available: <strong>{alt.available_capacity_kg.toLocaleString()} kg</strong> | Transit: {alt.travel_time_min} mins
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--status-safe)' }}>
                      ✓ Full -80C to +10C Envelope & Active Cooling
                    </div>
                  </div>

                  <button
                    className="btn btn-primary"
                    onClick={() => onSelectAlternative(alt.receiver_id)}
                    style={{ minHeight: '36px', padding: '6px 12px', fontSize: '0.8rem' }}
                  >
                    Select Alternative <ArrowRightIcon size={14} />
                  </button>
                </div>
              ))}
            </div>
          </section>

          <section className="card" aria-label="Re-evaluation Options">
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '8px' }}>Telemetry Re-evaluation</h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '10px' }}>
              If facility engineers at {receiver.name} have restored auxiliary generators or cleared intake dock space, re-run policy evaluation against live telemetry.
            </p>
            <button className="btn btn-secondary" onClick={onReevaluate} style={{ width: '100%' }}>
              Re-evaluate Facility Telemetry
            </button>
          </section>
        </div>
      </div>
    </div>
  );
};
