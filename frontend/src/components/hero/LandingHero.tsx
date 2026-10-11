import React from 'react';
import { ActiveTab } from '../layout/Navigation';
import { Incident } from '../../types';
import { TruckHero } from './TruckHero';
import { ShieldAlertIcon, ZapIcon, SnowflakeIcon } from '../common/Icons';

interface LandingHeroProps {
  activeIncident: Incident;
  onNavigateToCommandCenter: () => void;
  onNavigateToWorkflow: (tab: ActiveTab) => void;
}

export const LandingHero: React.FC<LandingHeroProps> = ({
  activeIncident,
  onNavigateToCommandCenter,
  onNavigateToWorkflow,
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px', marginBottom: '32px' }}>
      {/* 1. Cinematic Truck Hero Split Section */}
      <TruckHero
        incidentId={activeIncident.incident_id}
        cargoDesc={`${activeIncident.cargo.cargo_kg} kg ${activeIncident.cargo.cargo_type}`}
        currentTempC={activeIncident.cargo.current_temperature_c ?? 4.5}
        safeLimitC={activeIncident.cargo.safe_temperature_max ?? 8.0}
        onLaunchCommandCenter={onNavigateToCommandCenter}
        onExploreWorkflow={() => onNavigateToWorkflow('incidents')}
      />

      {/* 2. Frame.io Bento Grid Architecture & Feature Highlights */}
      <section aria-label="Feature Architecture Navigation">
        <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
          <div>
            <span className="micro-label">COLDRESCUE COLD-CHAIN CAPABILITIES</span>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em', marginTop: '4px' }}>
              Built for zero-compromise emergency resilience.
            </h2>
          </div>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Track 03 • Waste & Energy Reduction
          </span>
        </div>

        <div className="grid-cols-3">
          {/* Bento Card 1: Thermal Prediction (M3/M6) */}
          <div
            className="card"
            style={{
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              cursor: 'pointer',
              background: 'radial-gradient(circle at top right, rgba(56, 189, 248, 0.08) 0%, rgba(17, 24, 39, 0.95) 100%)',
            }}
            onClick={() => onNavigateToWorkflow('incidents')}
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <span className="badge badge-cyan">M3 / M6 • THERMAL PRECEDENCE</span>
                <SnowflakeIcon size={18} />
              </div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '8px', color: 'var(--text-primary)' }}>
                Surrogate Thermal Risk Engine
              </h3>
              <p style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                Predicts perishable core breach times using SageMaker Serverless with authoritative physics model clamping to eliminate false-safe risk.
              </p>
            </div>
            <div style={{ marginTop: '20px', paddingTop: '12px', borderTop: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--accent-cyan)' }}>Inspect Telemetry & Safety →</span>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{activeIncident.incident_id}</span>
            </div>
          </div>

          {/* Bento Card 2: Kuhn-Munkres Optimization (M5) */}
          <div
            className="card"
            style={{
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              cursor: 'pointer',
              background: 'radial-gradient(circle at top right, rgba(16, 185, 129, 0.08) 0%, rgba(17, 24, 39, 0.95) 100%)',
            }}
            onClick={() => onNavigateToWorkflow('allocation')}
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <span className="badge badge-safe">M5 • GLOBAL SOLVER</span>
                <ZapIcon size={18} />
              </div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '8px', color: 'var(--text-primary)' }}>
                Kuhn-Munkres Hungarian Matching
              </h3>
              <p style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                Global bipartite matching out-allocates greedy heuristics under high fleet contention while mathematically enforcing zero capacity or power violations.
              </p>
            </div>
            <div style={{ marginTop: '20px', paddingTop: '12px', borderTop: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--status-safe)' }}>Compare Solvers →</span>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>50 Scenarios Tested</span>
            </div>
          </div>

          {/* Bento Card 3: Deterministic Safety Gate (M3/M11) */}
          <div
            className="card"
            style={{
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              cursor: 'pointer',
              background: 'radial-gradient(circle at top right, rgba(244, 63, 94, 0.08) 0%, rgba(17, 24, 39, 0.95) 100%)',
            }}
            onClick={() => onNavigateToWorkflow('policy-block')}
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <span className="badge badge-critical">M3 • SAFETY GATE</span>
                <ShieldAlertIcon size={18} />
              </div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '8px', color: 'var(--text-primary)' }}>
                Authoritative Hard Safety Invariants
              </h3>
              <p style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                6 hard-block policy invariants override optimization and ML. Preempts over-capacity vaults, expired backup runtimes, and impossible transit ETAs.
              </p>
            </div>
            <div style={{ marginTop: '20px', paddingTop: '12px', borderTop: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--status-critical)' }}>Inspect Policy Block →</span>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>0 Overrides Allowed</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};
