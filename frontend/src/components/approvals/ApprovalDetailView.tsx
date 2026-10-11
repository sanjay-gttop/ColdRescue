import React, { useState } from 'react';
import { ApprovalRequest, Incident, Receiver } from '../../types';
import { StatusBadge } from '../common/StatusBadge';
import { Modal } from '../common/Modal';
import {
  UserCheckIcon,
  CheckCircleIcon,
  XCircleIcon,
} from '../common/Icons';
import { AwsContextChip, AwsServiceDrawer } from '../common/AwsContextChips';

interface ApprovalDetailViewProps {
  approval: ApprovalRequest;
  incident: Incident;
  receiver: Receiver;
  alternativeReceivers: Receiver[];
  onApprove: (approvalId: string, approverName: string) => void;
  onReject: (approvalId: string, reason: string) => void;
  onRequestReassessment: (approvalId: string) => void;
  onSelectAlternative: (receiverId: string) => void;
}

export const ApprovalDetailView: React.FC<ApprovalDetailViewProps> = ({
  approval,
  incident,
  receiver,
  alternativeReceivers,
  onApprove,
  onReject,
  onRequestReassessment,
  onSelectAlternative,
}) => {
  const [selectedAwsService, setSelectedAwsService] = useState<string | null>(null);
  const [approverName, setApproverName] = useState<string>('OpsManager_SarahJ');
  const [rejectReason, setRejectReason] = useState<string>('');
  const [showConfirmApprove, setShowConfirmApprove] = useState<boolean>(false);
  const [showRejectModal, setShowRejectModal] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const isHardBlocked = approval.policy_assessment.is_hard_blocked;
  const isDecided = approval.status !== 'pending';

  const handleConfirmApprove = () => {
    if (isHardBlocked || isSubmitting) return;
    setIsSubmitting(true);
    onApprove(approval.approval_id, approverName);
    setIsSubmitting(false);
    setShowConfirmApprove(false);
  };

  const handleConfirmReject = () => {
    if (rejectReason.trim().length < 5 || isSubmitting) return;
    setIsSubmitting(true);
    onReject(approval.approval_id, rejectReason.trim());
    setIsSubmitting(false);
    setShowRejectModal(false);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <AwsServiceDrawer
        serviceKey={selectedAwsService}
        onClose={() => setSelectedAwsService(null)}
      />

      {/* Top Banner */}
      <div className="card" style={{ borderLeft: `6px solid ${isHardBlocked ? 'var(--status-blocked-border)' : 'var(--status-pending-border)'}` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.85rem', fontFamily: 'monospace', color: 'var(--text-muted)' }}>
                {approval.approval_id}
              </span>
              <StatusBadge status={approval.status} />
              {isHardBlocked && <span className="badge badge-blocked">POLICY HARD-BLOCKED</span>}
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <AwsContextChip serviceKey="stepfunctions" onClick={() => setSelectedAwsService('stepfunctions')} />
                <AwsContextChip serviceKey="dynamodb" onClick={() => setSelectedAwsService('dynamodb')} />
              </div>
            </div>
            <h2 style={{ fontSize: '1.35rem', fontWeight: 800, marginTop: '6px' }}>
              Recovery Dispatch Review: {incident.incident_id} → {receiver.name}
            </h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Requester: <strong>{approval.requester}</strong> | Proposed Assignment:{' '}
              <span style={{ fontFamily: 'monospace' }}>{approval.assignment_id}</span>
            </p>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              className="btn btn-secondary"
              onClick={() => onRequestReassessment(approval.approval_id)}
              disabled={isDecided || isSubmitting}
            >
              Request Reassessment
            </button>
            <button
              className="btn btn-danger"
              onClick={() => setShowRejectModal(true)}
              disabled={isDecided || isSubmitting}
            >
              Reject Proposal
            </button>
            <button
              className="btn btn-primary"
              onClick={() => setShowConfirmApprove(true)}
              disabled={isDecided || isHardBlocked || isSubmitting}
              title={isHardBlocked ? 'Cannot approve: Hard safety rules violated' : 'Review and approve dispatch'}
            >
              <UserCheckIcon size={16} /> Approve & Dispatch
            </button>
          </div>
        </div>

        {isHardBlocked && (
          <div
            style={{
              marginTop: '14px',
              padding: '12px',
              borderRadius: 'var(--radius-sm)',
              backgroundColor: 'var(--status-blocked-bg)',
              border: '1px solid var(--status-blocked-border)',
              color: '#fda4af',
              fontSize: '0.85rem',
            }}
          >
            <strong>⚠️ HARD SAFETY BLOCK ACTIVE:</strong> This recovery proposal cannot be approved. The proposed receiver violates mandatory thermal, capacity, or cooling safety policies. Approval actions are locked.
          </div>
        )}
      </div>

      {/* Main Grid: Policy Checks & Alternative Facilities */}
      <div className="grid-cols-2">
        {/* Left Column: Safety Rule Evaluations */}
        <section className="card" aria-label="Policy Rules and Compliance Checks">
          <div className="card-header">
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>Cold Chain Safety Assessment</h3>
            <span style={{ fontSize: '0.8rem', color: approval.policy_assessment.is_safe ? 'var(--status-safe)' : 'var(--status-blocked)' }}>
              {approval.policy_assessment.is_safe ? 'All Critical Rules Passed' : 'Safety Failures Present'}
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {approval.policy_assessment.rule_evaluations.map((rule) => (
              <div
                key={rule.rule_id}
                style={{
                  padding: '12px',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: 'var(--bg-elevated)',
                  borderLeft: `4px solid ${rule.passed ? 'var(--status-safe-border)' : 'var(--status-critical-border)'}`,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <strong style={{ fontSize: '0.9rem' }}>{rule.rule_name}</strong>
                  {rule.passed ? (
                    <span style={{ color: 'var(--status-safe)', fontSize: '0.75rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <CheckCircleIcon size={14} /> PASSED
                    </span>
                  ) : (
                    <span style={{ color: 'var(--status-critical)', fontSize: '0.75rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <XCircleIcon size={14} /> FAILED
                    </span>
                  )}
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                  {rule.details}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                  Measured: <strong>{rule.measured_value}</strong> | Threshold: {rule.required_threshold}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Right Column: Receiver Details and Alternatives */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <section className="card" aria-label="Selected Receiver Snapshot">
            <div className="card-header">
              <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>Proposed Facility Snapshot</h3>
              <StatusBadge status={receiver.operational_availability} />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.85rem' }}>
              <div>
                <strong>{receiver.name}</strong> ({receiver.receiver_id})
                <div style={{ color: 'var(--text-muted)' }}>{receiver.location}</div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Available Capacity:</span>
                <strong>{receiver.available_capacity_kg.toLocaleString()} kg (Needs {incident.cargo.cargo_kg} kg)</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Transit Duration:</span>
                <strong>{receiver.travel_time_min} mins</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Backup Power:</span>
                <strong>{receiver.backup_runtime_min} mins</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Cooling Status:</span>
                <StatusBadge status={receiver.cooling_status} />
              </div>
            </div>
          </section>

          {/* Alternative Receivers (Why they rank lower or are infeasible) */}
          <section className="card" aria-label="Alternative Receiving Facilities">
            <div className="card-header">
              <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>Alternative Facilities Comparison</h3>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Evaluated Options</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {alternativeReceivers.map((alt) => (
                <div
                  key={alt.receiver_id}
                  style={{
                    padding: '10px 12px',
                    borderRadius: 'var(--radius-sm)',
                    backgroundColor: 'var(--bg-elevated)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    fontSize: '0.8rem',
                  }}
                >
                  <div>
                    <strong>{alt.name}</strong> ({alt.travel_time_min}m away)
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      Available: {alt.available_capacity_kg} kg | Cooling: {alt.cooling_status}
                    </div>
                  </div>
                  <button
                    className="btn btn-secondary"
                    onClick={() => onSelectAlternative(alt.receiver_id)}
                    style={{ minHeight: '32px', padding: '4px 10px', fontSize: '0.75rem' }}
                  >
                    Select Alternative
                  </button>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>

      {/* Confirmation Modal for Approval */}
      <Modal
        isOpen={showConfirmApprove}
        onClose={() => setShowConfirmApprove(false)}
        title="Confirm Recovery Dispatch Approval"
        footer={
          <>
            <button className="btn btn-secondary" onClick={() => setShowConfirmApprove(false)}>
              Cancel
            </button>
            <button className="btn btn-primary" onClick={handleConfirmApprove} disabled={isSubmitting}>
              {isSubmitting ? 'Recording...' : 'Authorize Dispatch'}
            </button>
          </>
        }
      >
        <p style={{ fontSize: '0.9rem', marginBottom: '12px' }}>
          You are authorizing emergency cargo redirection of <strong>{incident.cargo.cargo_kg} kg</strong> of{' '}
          <strong>{incident.cargo.cargo_type}</strong> to <strong>{receiver.name}</strong>.
        </p>

        <div style={{ marginBottom: '12px' }}>
          <label htmlFor="approver-input" className="form-label">
            Operator Name / Signature:
          </label>
          <input
            id="approver-input"
            className="form-input"
            value={approverName}
            onChange={(e) => setApproverName(e.target.value)}
          />
        </div>

        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', backgroundColor: 'var(--bg-elevated)', padding: '8px', borderRadius: 'var(--radius-sm)' }}>
          ℹ️ This action records a non-reversible APPROVAL_GRANTED event in the audit trail and generates driver dispatch orders.
        </div>
      </Modal>

      {/* Rejection Modal */}
      <Modal
        isOpen={showRejectModal}
        onClose={() => setShowRejectModal(false)}
        title="Reject Proposed Recovery Assignment"
        footer={
          <>
            <button className="btn btn-secondary" onClick={() => setShowRejectModal(false)}>
              Cancel
            </button>
            <button
              className="btn btn-danger"
              onClick={handleConfirmReject}
              disabled={rejectReason.trim().length < 5 || isSubmitting}
            >
              Confirm Rejection
            </button>
          </>
        }
      >
        <p style={{ fontSize: '0.9rem', marginBottom: '12px' }}>
          Please document the operational rationale for rejecting this allocation. This justification is required for the audit trail.
        </p>

        <div style={{ marginBottom: '12px' }}>
          <label htmlFor="reject-reason" className="form-label">
            Rejection Reason (minimum 5 characters):
          </label>
          <textarea
            id="reject-reason"
            className="form-textarea"
            rows={3}
            placeholder="e.g. Inbound highway closure reported on I-80; facility docking staff unavailable."
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
          />
        </div>
      </Modal>
    </div>
  );
};
