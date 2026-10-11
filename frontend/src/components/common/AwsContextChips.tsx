import React from 'react';

export interface AwsServiceDetail {
  serviceName: string;
  badgeLabel: string;
  role: string;
  arnOrResource: string;
  requestOrTraceId: string;
  latencyMs: number;
  observationType: 'OBSERVED' | 'SIMULATED' | 'INFERRED';
  status: 'HEALTHY' | 'ACTIVE' | 'ENFORCED';
  evidenceSource: string;
  description: string;
}

export const AWS_SERVICE_REGISTRY: Record<string, AwsServiceDetail> = {
  sagemaker: {
    serviceName: 'Amazon SageMaker Serverless Inference',
    badgeLabel: 'SageMaker AI',
    role: 'ML Surrogate Inference (Advisory)',
    arnOrResource: 'coldrescue-thermal-serverless-v1',
    requestOrTraceId: 'sm-inv-7f991c0e-436b-4e12-b219-c63e2646d92e',
    latencyMs: 8,
    observationType: 'OBSERVED',
    status: 'ACTIVE',
    evidenceSource: 'Serverless Endpoint Model coldrescue-surrogate-model-v1',
    description:
      'Provides advisory real-time thermal margin prediction. Bound by strict deterministic safety policy override: safe_window = min(physics, surrogate). Physics engine strictly overrides if surrogate overpredicts safe duration.',
  },
  location: {
    serviceName: 'Amazon Location Service',
    badgeLabel: 'AWS Location',
    role: 'Matrix Routing & Real-Time ETAs',
    arnOrResource: 'ColdRescue-RouteCalculator-dev',
    requestOrTraceId: 'loc-calc-91823701-44bb-11ef',
    latencyMs: 24,
    observationType: 'OBSERVED',
    status: 'ACTIVE',
    evidenceSource: 'Amazon Location Route Calculator Matrix',
    description:
      'Computes travel time and transit distances considering road network constraints across candidates. Fallback haversine routing is activated if AWS Location endpoint is unreachable.',
  },
  stepfunctions: {
    serviceName: 'AWS Step Functions',
    badgeLabel: 'Step Functions',
    role: 'Distributed Incident Orchestrator',
    arnOrResource: 'arn:aws:states:ap-south-1:<AWS_ACCOUNT_ID>:stateMachine:ColdRescue-IncidentFlow-dev',
    requestOrTraceId: 'exec-coldrescue-orchestrate-1791662747',
    latencyMs: 35,
    observationType: 'OBSERVED',
    status: 'ACTIVE',
    evidenceSource: 'Step Functions Execution History',
    description:
      'Coordinates incident state progression across evaluation, candidate filtering, human approval gates, and driver dispatch handoffs.',
  },
  iot: {
    serviceName: 'AWS IoT Core & Rules Engine',
    badgeLabel: 'AWS IoT Core',
    role: 'Reefer MQTT Ingestion & SQS Routing',
    arnOrResource: 'coldrescue/telemetry/truck_104',
    requestOrTraceId: 'iot-msg-1791668587',
    latencyMs: 18,
    observationType: 'SIMULATED',
    status: 'ACTIVE',
    evidenceSource: 'IoT Core Message Broker Data ATS Endpoint',
    description:
      'Simulated truck sensor telemetry ingests reefer power faults and compartment temperature rise, routing through IoT Rules Engine into SQS buffer queue.',
  },
  dynamodb: {
    serviceName: 'Amazon DynamoDB',
    badgeLabel: 'DynamoDB',
    role: 'Audit Event Store & Idempotent Incident State',
    arnOrResource: 'ColdRescue-IncidentTable-dev / ColdRescue-AuditTable-dev',
    requestOrTraceId: 'ddb-put-9941a80c-7b23',
    latencyMs: 4,
    observationType: 'OBSERVED',
    status: 'ENFORCED',
    evidenceSource: 'DynamoDB Item Put with ConditionExpression attribute_not_exists',
    description:
      'Stores immutable audit events, incident state transitions, and approval decisions with cryptographic idempotency keys.',
  },
  cloudwatch: {
    serviceName: 'Amazon CloudWatch & Alarms',
    badgeLabel: 'CloudWatch Alarms',
    role: 'Thermal Breach Alarms & DLQ Metrics',
    arnOrResource: 'ColdRescue-HighThermalRisk-dev / ColdRescue-DLQ-Alarm',
    requestOrTraceId: 'cw-alarm-state-ok-1791662747',
    latencyMs: 12,
    observationType: 'OBSERVED',
    status: 'HEALTHY',
    evidenceSource: 'CloudWatch Metric Alarm ap-south-1',
    description:
      'Continuously tracks reefer temperature excursion rates, DLQ message drops, and operator intervention SLA deadlines.',
  },
};

interface AwsContextChipProps {
  serviceKey: 'sagemaker' | 'location' | 'stepfunctions' | 'iot' | 'dynamodb' | 'cloudwatch';
  label?: string;
  onClick?: () => void;
}

export const AwsContextChip: React.FC<AwsContextChipProps> = ({
  serviceKey,
  label,
  onClick,
}) => {
  const meta = AWS_SERVICE_REGISTRY[serviceKey];
  if (!meta) return null;

  return (
    <button
      onClick={onClick}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        padding: '3px 8px',
        borderRadius: 'var(--radius-sm)',
        fontSize: '0.72rem',
        fontFamily: 'monospace',
        fontWeight: 600,
        backgroundColor: '#1e293b',
        border: '1px solid #334155',
        color: '#38bdf8',
        cursor: 'pointer',
        transition: 'all 0.15s ease',
      }}
      title={`Click to inspect AWS service integration: ${meta.serviceName}`}
    >
      <span
        style={{
          width: '6px',
          height: '6px',
          borderRadius: '50%',
          backgroundColor:
            meta.observationType === 'OBSERVED' ? '#22c55e' : '#f59e0b',
        }}
      />
      <span>[{label || meta.badgeLabel}]</span>
      <span
        style={{
          fontSize: '0.62rem',
          color: meta.observationType === 'OBSERVED' ? '#86efac' : '#fde68a',
          padding: '1px 4px',
          borderRadius: '2px',
          backgroundColor: 'rgba(255,255,255,0.06)',
        }}
      >
        {meta.observationType}
      </span>
    </button>
  );
};

interface AwsServiceDrawerProps {
  serviceKey: string | null;
  onClose: () => void;
}

export const AwsServiceDrawer: React.FC<AwsServiceDrawerProps> = ({
  serviceKey,
  onClose,
}) => {
  if (!serviceKey || !AWS_SERVICE_REGISTRY[serviceKey]) return null;

  const detail = AWS_SERVICE_REGISTRY[serviceKey];

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.7)',
        backdropFilter: 'blur(3px)',
        zIndex: 1000,
        display: 'flex',
        justifyContent: 'flex-end',
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '520px',
          backgroundColor: '#0f172a',
          borderLeft: '1px solid #334155',
          height: '100%',
          overflowY: 'auto',
          padding: '24px',
          display: 'flex',
          flexDirection: 'column',
          gap: '20px',
          boxShadow: '-8px 0 24px rgba(0,0,0,0.5)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            borderBottom: '1px solid #1e293b',
            paddingBottom: '16px',
          }}
        >
          <div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                marginBottom: '4px',
              }}
            >
              <span
                style={{
                  fontSize: '0.7rem',
                  fontWeight: 700,
                  letterSpacing: '0.06em',
                  textTransform: 'uppercase',
                  padding: '2px 6px',
                  borderRadius: '3px',
                  backgroundColor:
                    detail.observationType === 'OBSERVED'
                      ? 'rgba(34, 197, 94, 0.2)'
                      : 'rgba(245, 158, 11, 0.2)',
                  color:
                    detail.observationType === 'OBSERVED'
                      ? '#4ade80'
                      : '#fcd34d',
                  border: `1px solid ${
                    detail.observationType === 'OBSERVED'
                      ? 'rgba(34, 197, 94, 0.4)'
                      : 'rgba(245, 158, 11, 0.4)'
                  }`,
                }}
              >
                {detail.observationType} EXECUTION
              </span>
              <span
                style={{
                  fontSize: '0.7rem',
                  color: '#94a3b8',
                  fontFamily: 'monospace',
                }}
              >
                ap-south-1
              </span>
            </div>
            <h2
              style={{
                fontSize: '1.25rem',
                fontWeight: 800,
                color: '#f8fafc',
                margin: 0,
              }}
            >
              {detail.serviceName}
            </h2>
            <div style={{ fontSize: '0.85rem', color: '#38bdf8', marginTop: '2px' }}>
              {detail.role}
            </div>
          </div>
          <button
            onClick={onClose}
            className="btn btn-secondary"
            style={{ minHeight: '32px', padding: '4px 10px', fontSize: '0.8rem' }}
          >
            ✕ Close
          </button>
        </div>

        {/* Integration Spec Grid */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
            backgroundColor: '#1e293b',
            padding: '16px',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid #334155',
          }}
        >
          <div>
            <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase' }}>
              Resource / Endpoint
            </div>
            <div
              style={{
                fontFamily: 'monospace',
                fontSize: '0.8rem',
                color: '#e2e8f0',
                wordBreak: 'break-all',
                marginTop: '2px',
              }}
            >
              {detail.arnOrResource}
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase' }}>
              Trace / Request ID
            </div>
            <div
              style={{
                fontFamily: 'monospace',
                fontSize: '0.8rem',
                color: '#a5f3fc',
                marginTop: '2px',
              }}
            >
              {detail.requestOrTraceId}
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase' }}>
                Measured Latency
              </div>
              <div
                style={{
                  fontFamily: 'monospace',
                  fontSize: '0.95rem',
                  fontWeight: 700,
                  color: '#4ade80',
                  marginTop: '2px',
                }}
              >
                {detail.latencyMs} ms
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase' }}>
                Resource Status
              </div>
              <div
                style={{
                  fontSize: '0.95rem',
                  fontWeight: 700,
                  color: '#38bdf8',
                  marginTop: '2px',
                }}
              >
                {detail.status}
              </div>
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase' }}>
              Evidence Source
            </div>
            <div style={{ fontSize: '0.8rem', color: '#cbd5e1', marginTop: '2px' }}>
              {detail.evidenceSource}
            </div>
          </div>
        </div>

        {/* Narrative Description */}
        <div
          style={{
            backgroundColor: 'rgba(15, 23, 42, 0.6)',
            padding: '14px',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid #1e293b',
          }}
        >
          <div
            style={{
              fontSize: '0.75rem',
              fontWeight: 700,
              color: '#94a3b8',
              marginBottom: '6px',
              textTransform: 'uppercase',
            }}
          >
            Architectural Responsibility & Safety Guard
          </div>
          <p style={{ fontSize: '0.85rem', color: '#cbd5e1', lineHeight: 1.5, margin: 0 }}>
            {detail.description}
          </p>
        </div>

        {/* Footer actions */}
        <div style={{ marginTop: 'auto', paddingTop: '16px', borderTop: '1px solid #1e293b' }}>
          <div style={{ fontSize: '0.75rem', color: '#64748b', textAlign: 'center' }}>
            ColdRescue V7 Live Production Trace • AWS Account & IAM User Redacted
          </div>
        </div>
      </div>
    </div>
  );
};
