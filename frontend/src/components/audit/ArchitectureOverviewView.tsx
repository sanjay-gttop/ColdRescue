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
          <h3 style={{ fontSize: '1.05rem', fontWeight: 600, margin: '6px 0 8px 0' }}>AWS IoT Core & EventBridge</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.4 }}>
            Reefer trucks emit MQTT telemetry to IoT topic <code>coldrescue/telemetry/#</code>. An IoT Topic Rule routes messages directly into an SQS buffer with managed encryption, processed by an idempotent consumer Lambda.
          </p>
        </div>

        <div style={{ padding: '16px', backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '6px' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#10b981', textTransform: 'uppercase' }}>2. Thermal & Routing Intelligence</div>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 600, margin: '6px 0 8px 0' }}>S3 ML Artifacts & Amazon Location</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.4 }}>
            Linear surrogate ML model archived in Amazon S3 predicts remaining safe preservation windows. Real truck routes (distance & transit time) are calculated via Amazon Location Service RouteCalculator with spherical Haversine fallback.
          </p>
        </div>

        <div style={{ padding: '16px', backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '6px' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#f59e0b', textTransform: 'uppercase' }}>3. Coordinated Optimization</div>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 600, margin: '6px 0 8px 0' }}>Kuhn-Munkres Exact Solver</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.4 }}>
            Pure-Python Hungarian linear sum assignment matches fleet incidents to candidate cold hubs. Formally proven to achieve a 0.0% optimality gap against exhaustive brute force with multi-parameter perturbation resilience.
          </p>
        </div>

        <div style={{ padding: '16px', backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '6px' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#ef4444', textTransform: 'uppercase' }}>4. Safety & Policy Authority</div>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 600, margin: '6px 0 8px 0' }}>Deterministic 6-Rule Policy</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.4 }}>
            Non-negotiable hard block gate. Evaluates temperature boundaries, capacity limits, backup runtimes, and transit margins. Machine learning models and optimizers can never override safety blocks.
          </p>
        </div>

        <div style={{ padding: '16px', backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '6px' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#a855f7', textTransform: 'uppercase' }}>5. Orchestration & RBAC</div>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 600, margin: '6px 0 8px 0' }}>Step Functions & Cognito User Pool</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.4 }}>
            10-stage state machine orchestrating end-to-end recovery. API Gateway secured with Cognito User Pool authorizer (4 roles: Operator, Approver, Driver, Receiver). Separation of duties strictly blocks drivers from approving recoveries.
          </p>
        </div>

        <div style={{ padding: '16px', backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '6px' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#ec4899', textTransform: 'uppercase' }}>6. Reliability & Alarms</div>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 600, margin: '6px 0 8px 0' }}>SQS DLQ & CloudWatch Metric Alarms</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.4 }}>
            SQS redrive policy automatically routes poison messages to a dedicated Dead-Letter Queue (retention 14 days). CloudWatch Alarm monitors Step Functions execution failures and executes SNS notification actions.
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
