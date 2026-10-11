import React from 'react';
import { ActiveTab } from '../layout/Navigation';

interface GoldenPathStepperProps {
  activeTab: ActiveTab;
  onNavigate: (tab: ActiveTab) => void;
  incidentId: string;
}

interface StepDef {
  key: string;
  number: number;
  label: string;
  sublabel: string;
  targetTab: ActiveTab;
  activeWhen: ActiveTab[];
}

const STEPS: StepDef[] = [
  {
    key: 'detect',
    number: 1,
    label: 'Detect',
    sublabel: 'Telemetry Alert',
    targetTab: 'dashboard',
    activeWhen: ['dashboard', 'live-trace'],
  },
  {
    key: 'evaluate',
    number: 2,
    label: 'Evaluate',
    sublabel: 'Thermal Precedence',
    targetTab: 'incidents',
    activeWhen: ['incidents'],
  },
  {
    key: 'allocate',
    number: 3,
    label: 'Allocate',
    sublabel: 'Kuhn-Munkres vs Greedy',
    targetTab: 'allocation',
    activeWhen: ['receivers', 'allocation'],
  },
  {
    key: 'approve',
    number: 4,
    label: 'Approve',
    sublabel: 'Safety Policy Gate',
    targetTab: 'approvals',
    activeWhen: ['approvals', 'policy-block'],
  },
  {
    key: 'verify',
    number: 5,
    label: 'Verify',
    sublabel: 'Audit & Handoff',
    targetTab: 'audit',
    activeWhen: ['driver', 'receiver-portal', 'audit', 'architecture', 'action-matrix'],
  },
];

export const GoldenPathStepper: React.FC<GoldenPathStepperProps> = ({
  activeTab,
  onNavigate,
  incidentId,
}) => {
  // Determine current active step index
  const currentStepIndex = STEPS.findIndex((s) => s.activeWhen.includes(activeTab));
  const activeIdx = currentStepIndex >= 0 ? currentStepIndex : 0;

  return (
    <nav
      aria-label="Incident Recovery Golden Path"
      style={{
        backgroundColor: '#0f172a',
        borderBottom: '1px solid #1e293b',
        padding: '10px 16px',
      }}
    >
      <div
        className="container"
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        {/* Incident Context Tag */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span
            style={{
              fontSize: '0.68rem',
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
              color: '#94a3b8',
              fontWeight: 700,
            }}
          >
            Golden Path Workflow:
          </span>
          <span
            style={{
              fontFamily: 'monospace',
              fontSize: '0.8rem',
              fontWeight: 700,
              padding: '2px 8px',
              borderRadius: 'var(--radius-sm)',
              backgroundColor: '#1e293b',
              color: 'var(--accent-cyan)',
              border: '1px solid rgba(6, 182, 212, 0.3)',
            }}
          >
            {incidentId}
          </span>
        </div>

        {/* Stepper Nodes */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            flexWrap: 'wrap',
          }}
        >
          {STEPS.map((step, idx) => {
            const isCurrent = idx === activeIdx;
            const isCompleted = idx < activeIdx;

            return (
              <React.Fragment key={step.key}>
                <button
                  onClick={() => onNavigate(step.targetTab)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '4px 10px',
                    borderRadius: 'var(--radius-full)',
                    background: isCurrent
                      ? 'rgba(6, 182, 212, 0.15)'
                      : isCompleted
                      ? 'rgba(34, 197, 94, 0.1)'
                      : 'transparent',
                    border: isCurrent
                      ? '1px solid var(--accent-cyan)'
                      : isCompleted
                      ? '1px solid rgba(34, 197, 94, 0.4)'
                      : '1px solid transparent',
                    cursor: 'pointer',
                    color: isCurrent
                      ? '#ffffff'
                      : isCompleted
                      ? '#86efac'
                      : '#94a3b8',
                    transition: 'all 0.15s ease',
                  }}
                  title={`Step ${step.number}: ${step.label} (${step.sublabel})`}
                >
                  <span
                    style={{
                      width: '20px',
                      height: '20px',
                      borderRadius: '50%',
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '0.72rem',
                      fontWeight: 800,
                      backgroundColor: isCurrent
                        ? 'var(--accent-cyan)'
                        : isCompleted
                        ? '#22c55e'
                        : '#334155',
                      color: isCurrent || isCompleted ? '#0f172a' : '#94a3b8',
                    }}
                  >
                    {isCompleted ? '✓' : step.number}
                  </span>
                  <div style={{ textAlign: 'left', lineHeight: 1.1 }}>
                    <div
                      style={{
                        fontSize: '0.78rem',
                        fontWeight: isCurrent ? 800 : 600,
                        letterSpacing: '0.02em',
                      }}
                    >
                      {step.label}
                    </div>
                    <div
                      style={{
                        fontSize: '0.65rem',
                        color: isCurrent ? '#a5f3fc' : '#64748b',
                      }}
                    >
                      {step.sublabel}
                    </div>
                  </div>
                </button>

                {idx < STEPS.length - 1 && (
                  <span
                    style={{
                      color: isCompleted ? '#22c55e' : '#334155',
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      userSelect: 'none',
                    }}
                  >
                    →
                  </span>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </nav>
  );
};
