import React, { useState } from 'react';
import { Incident, Receiver } from '../../types';
import { runGreedyAllocation, runGlobalAllocation } from '../../utils/allocationAlgorithms';
import {
  LayersIcon,
  CheckCircleIcon,
  XCircleIcon,
  RefreshCwIcon,
  ArrowRightIcon,
} from '../common/Icons';

interface AllocationComparisonViewProps {
  incidents: Incident[];
  receivers: Receiver[];
  onSelectProposedAssignment: (incidentId: string, receiverId: string) => void;
}

export const AllocationComparisonView: React.FC<AllocationComparisonViewProps> = ({
  incidents,
  receivers,
  onSelectProposedAssignment,
}) => {
  const [selectedScenario, setSelectedScenario] = useState<string>('Standard Multi-Incident Fleet');

  const greedyPlan = runGreedyAllocation(incidents, receivers, selectedScenario);
  const globalPlan = runGlobalAllocation(incidents, receivers, selectedScenario);

  const handleRunComparison = () => {
    // Re-evaluates allocations
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Overview & Scenario Controls */}
      <section className="card" aria-label="Allocation Optimizer Configuration">
        <div className="card-header">
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <LayersIcon size={22} /> Greedy vs. Global Fleet Recovery Allocation
            </h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Evaluate trade-offs between localized fast-first heuristics and multi-incident global risk minimization.
            </p>
          </div>
          <button className="btn btn-primary" onClick={handleRunComparison}>
            <RefreshCwIcon size={16} /> Re-evaluate Optimization
          </button>
        </div>

        <div style={{ display: 'flex', gap: '16px', alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <label htmlFor="scenario-select" className="form-label" style={{ margin: 0 }}>
              Active Evaluation Scenario:
            </label>
            <select
              id="scenario-select"
              className="form-select"
              value={selectedScenario}
              onChange={(e) => setSelectedScenario(e.target.value)}
              style={{ minWidth: '280px' }}
            >
              <option value="Standard Multi-Incident Fleet">Scenario 1: Standard Fleet (3 Concurrent Incidents)</option>
              <option value="Severe Multi-Truck Heat Ingress">Scenario 2: Cascading Heat Wave (Constrained Ultra-Cold)</option>
              <option value="High-Density Urban Outage">Scenario 3: Dense Urban Outage (Traffic Congestion)</option>
            </select>
          </div>

          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', flex: 1 }}>
            ℹ️ All strategies are evaluated against identical cold chain safety policies and real-world receiving facility capacities.
          </div>
        </div>
      </section>

      {/* Side-by-side Strategy Cards */}
      <div className="grid-cols-2">
        {/* Strategy 1: Greedy Allocation */}
        <section
          className="card"
          aria-label="Greedy Allocation Strategy Results"
          style={{ borderTop: '4px solid var(--status-warning-border)' }}
        >
          <div className="card-header">
            <div>
              <span className="badge badge-warning">LOCAL HEURISTIC BASELINE</span>
              <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginTop: '4px' }}>Greedy Strategy</h3>
            </div>
            <div style={{ textAlign: 'right' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>SYSTEM RISK SCORE</span>
              <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--status-warning)' }}>
                {greedyPlan.total_spoilage_risk_score}/100
              </div>
            </div>
          </div>

          {/* Key Metrics */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', margin: '14px 0' }}>
            <div style={{ backgroundColor: 'var(--bg-elevated)', padding: '10px', borderRadius: 'var(--radius-sm)' }}>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block' }}>AVG TRAVEL TIME</span>
              <strong style={{ fontSize: '1.1rem' }}>{greedyPlan.average_travel_time_min} mins</strong>
            </div>
            <div style={{ backgroundColor: 'var(--bg-elevated)', padding: '10px', borderRadius: 'var(--radius-sm)' }}>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block' }}>CAPACITY UTILIZATION</span>
              <strong style={{ fontSize: '1.1rem' }}>{greedyPlan.capacity_utilization_pct}%</strong>
            </div>
            <div style={{ backgroundColor: 'var(--bg-elevated)', padding: '10px', borderRadius: 'var(--radius-sm)' }}>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block' }}>UNASSIGNED CARGO</span>
              <strong style={{ fontSize: '1.1rem', color: greedyPlan.unassigned_incidents.length > 0 ? 'var(--status-critical)' : 'var(--status-safe)' }}>
                {greedyPlan.unassigned_incidents.length}
              </strong>
            </div>
          </div>

          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '14px' }}>
            {greedyPlan.explanation}
          </p>

          {/* Assignments Table */}
          <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '10px' }}>
            <h4 style={{ fontSize: '0.9rem', marginBottom: '8px' }}>Proposed Cargo Dispatches:</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {greedyPlan.assignments.map((a, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '8px 12px',
                    borderRadius: 'var(--radius-sm)',
                    backgroundColor: 'var(--bg-elevated)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    fontSize: '0.8rem',
                  }}
                >
                  <div>
                    <strong>{a.incident_id}</strong> →{' '}
                    <span style={{ color: a.feasible ? 'var(--accent-cyan)' : 'var(--status-critical)' }}>
                      {a.receiver_id}
                    </span>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                      {a.feasible ? `${a.travel_time_min} min transit (+${a.spoilage_margin_min}m margin)` : a.rejection_reason}
                    </div>
                  </div>
                  {a.feasible ? (
                    <span style={{ color: 'var(--status-safe)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <CheckCircleIcon size={14} /> Feasible
                    </span>
                  ) : (
                    <span style={{ color: 'var(--status-critical)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <XCircleIcon size={14} /> Infeasible
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Documented Assumptions & Limitations */}
          <div style={{ marginTop: '16px', fontSize: '0.75rem', color: 'var(--text-muted)', borderTop: '1px solid var(--border-subtle)', paddingTop: '10px' }}>
            <strong>Assumptions & Limitations:</strong>
            <ul style={{ paddingLeft: '16px', marginTop: '4px' }}>
              {greedyPlan.limitations.map((lim, i) => (
                <li key={i}>{lim}</li>
              ))}
            </ul>
          </div>
        </section>

        {/* Strategy 2: Global Optimization */}
        <section
          className="card"
          aria-label="Global Allocation Strategy Results"
          style={{ borderTop: '4px solid var(--status-safe-border)', backgroundColor: 'var(--bg-card)' }}
        >
          <div className="card-header">
            <div>
              <span className="badge badge-safe">BALANCED MULTI-INCIDENT OPTIMIZATION</span>
              <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginTop: '4px' }}>Global Strategy</h3>
            </div>
            <div style={{ textAlign: 'right' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>SYSTEM RISK SCORE</span>
              <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--status-safe)' }}>
                {globalPlan.total_spoilage_risk_score}/100
              </div>
            </div>
          </div>

          {/* Key Metrics */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', margin: '14px 0' }}>
            <div style={{ backgroundColor: 'var(--bg-elevated)', padding: '10px', borderRadius: 'var(--radius-sm)' }}>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block' }}>AVG TRAVEL TIME</span>
              <strong style={{ fontSize: '1.1rem' }}>{globalPlan.average_travel_time_min} mins</strong>
            </div>
            <div style={{ backgroundColor: 'var(--bg-elevated)', padding: '10px', borderRadius: 'var(--radius-sm)' }}>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block' }}>CAPACITY UTILIZATION</span>
              <strong style={{ fontSize: '1.1rem' }}>{globalPlan.capacity_utilization_pct}%</strong>
            </div>
            <div style={{ backgroundColor: 'var(--bg-elevated)', padding: '10px', borderRadius: 'var(--radius-sm)' }}>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block' }}>UNASSIGNED CARGO</span>
              <strong style={{ fontSize: '1.1rem', color: 'var(--status-safe)' }}>
                {globalPlan.unassigned_incidents.length}
              </strong>
            </div>
          </div>

          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '14px' }}>
            {globalPlan.explanation}
          </p>

          {/* Assignments Table */}
          <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '10px' }}>
            <h4 style={{ fontSize: '0.9rem', marginBottom: '8px' }}>Optimized Cargo Dispatches:</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {globalPlan.assignments.map((a, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '8px 12px',
                    borderRadius: 'var(--radius-sm)',
                    backgroundColor: 'var(--bg-elevated)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    fontSize: '0.8rem',
                  }}
                >
                  <div>
                    <strong>{a.incident_id}</strong> →{' '}
                    <span style={{ color: 'var(--accent-cyan)' }}>{a.receiver_id}</span>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                      {a.travel_time_min} min transit (+{a.spoilage_margin_min}m safety buffer)
                    </div>
                  </div>
                  <button
                    className="btn btn-secondary"
                    onClick={() => onSelectProposedAssignment(a.incident_id, a.receiver_id)}
                    style={{ minHeight: '30px', padding: '2px 8px', fontSize: '0.75rem' }}
                  >
                    Select Proposal <ArrowRightIcon size={12} />
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Documented Assumptions & Limitations */}
          <div style={{ marginTop: '16px', fontSize: '0.75rem', color: 'var(--text-muted)', borderTop: '1px solid var(--border-subtle)', paddingTop: '10px' }}>
            <strong>Assumptions & Limitations:</strong>
            <ul style={{ paddingLeft: '16px', marginTop: '4px' }}>
              {globalPlan.limitations.map((lim, i) => (
                <li key={i}>{lim}</li>
              ))}
            </ul>
          </div>
        </section>
      </div>
    </div>
  );
};
