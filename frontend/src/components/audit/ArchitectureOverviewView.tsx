import React from 'react';

export const ArchitectureOverviewView: React.FC = () => {
  return (
    <div className="container" style={{ padding: '24px 16px' }}>
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '1.4rem', fontWeight: 700, margin: '0 0 8px 0', color: 'var(--text-primary)' }}>
          ColdRescue Architecture & Deep AWS Integration
        </h2>
        <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          Detailed technical breakdown of deployed services, decision authorities, data flows, and security guardrails across Track 03 (Waste & Energy).
        </p>
      </div>

      {/* Highlights Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '16px',
          marginBottom: '28px',
        }}
      >
        <div style={{ padding: '16px', backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '6px' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase' }}>1. Telemetry Ingestion</div>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 600, margin: '6px 0 8px 0' }}>EventBridge & SQS Buffer</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.4 }}>
            Synthetic telemetry flows through <code>ColdRescue-Bus-dev</code> with rules routing incidents to encrypted SQS queue <code>ColdRescue-ProcessingQueue-dev</code> and redrive DLQ <code>ColdRescue-DLQ-dev</code>.
          </p>
        </div>

        <div style={{ padding: '16px', backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '6px' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#10b981', textTransform: 'uppercase' }}>2. AI & Thermal Intelligence</div>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 600, margin: '6px 0 8px 0' }}>Amazon SageMaker Serverless</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.4 }}>
            Live serverless endpoint <code>coldrescue-thermal-serverless-v1</code> delivers sub-second surrogate predictions (warm latency: 107.8 ms), strictly clamped by deterministic Newton cooling physics.
          </p>
        </div>

        <div style={{ padding: '16px', backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '6px' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase' }}>3. Real-World Routing</div>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 600, margin: '6px 0 8px 0' }}>Amazon Location Service</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.4 }}>
            Route calculator <code>ColdRescue-RouteCalculator-dev</code> calculates live commercial truck driving distances and transit durations using real Indian highway networks.
          </p>
        </div>

        <div style={{ padding: '16px', backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '6px' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#f59e0b', textTransform: 'uppercase' }}>4. Coordinated Allocation</div>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 600, margin: '6px 0 8px 0' }}>Kuhn-Munkres Exact Solver</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.4 }}>
            Global bipartite matching eliminates greedy local contention. Evaluated across 50-scenario benchmark suites with +314.3 kg simulated lift and 0.0% optimality gap vs brute force.
          </p>
        </div>

        <div style={{ padding: '16px', backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '6px' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#ef4444', textTransform: 'uppercase' }}>5. Safety Authority Gate</div>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 600, margin: '6px 0 8px 0' }}>Deterministic 6-Rule Policy</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.4 }}>
            Authoritative gate enforcing temperature boundaries, capacity caps, and transit buffers. Emits <code>PolicyBlockedCount</code> and <code>PolicyPassedCount</code> without triggering false incident alarms.
          </p>
        </div>

        <div style={{ padding: '16px', backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '6px' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#a855f7', textTransform: 'uppercase' }}>6. Orchestration & RBAC</div>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 600, margin: '6px 0 8px 0' }}>Step Functions & Cognito</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.4 }}>
            10-stage state machine <code>ColdRescue-IncidentRecovery-dev</code> with X-Ray active tracing, transient error retries, and Cognito User Pool RBAC groups (Operator, Approver, Driver, Receiver).
          </p>
        </div>

        <div style={{ padding: '16px', backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '6px' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#ec4899', textTransform: 'uppercase' }}>7. Storage & Streams</div>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 600, margin: '6px 0 8px 0' }}>DynamoDB Streams & S3 Glacier</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.4 }}>
            Audit trails persist to S3 with 30-day Glacier Instant Retrieval lifecycle and EventBridge notifications. DynamoDB Streams pipe events to a passive consumer emitting <code>EventsPersistedCount</code>.
          </p>
        </div>

        <div style={{ padding: '16px', backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '6px' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#3b82f6', textTransform: 'uppercase' }}>8. Telemetry Simulator</div>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 600, margin: '6px 0 8px 0' }}>Amazon ECS Fargate</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.4 }}>
            Containerized continuous fleet simulator <code>ColdRescue-SimulatorService-dev</code> deployed with public subnets and zero NAT gateways for total cost containment (default desired_count=0).
          </p>
        </div>
      </div>

      {/* Illustrative Disclaimer */}
      <div
        style={{
          padding: '14px 18px',
          backgroundColor: '#1e293b',
          borderLeft: '4px solid #3b82f6',
          borderRadius: '4px',
          fontSize: '0.85rem',
          color: '#cbd5e1',
          lineHeight: 1.4,
        }}
      >
        <strong>Mandatory Regulatory Disclosure:</strong><br />
        <em>"Illustrative estimate based on stated simulation assumptions, not measured real-world savings."</em>
        <br />
        ColdRescue provides algorithmic decision support and does not constitute certified food safety or medical compliance testing.
      </div>
    </div>
  );
};
