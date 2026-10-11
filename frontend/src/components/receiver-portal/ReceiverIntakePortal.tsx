import React, { useState } from 'react';
import { Assignment, Incident, Receiver } from '../../types';
import { StatusBadge } from '../common/StatusBadge';
import { Modal } from '../common/Modal';
import {
  CheckCircleIcon,
  XCircleIcon,
  ZapIcon,
  SnowflakeIcon,
} from '../common/Icons';

interface ReceiverIntakePortalProps {
  assignment: Assignment;
  incident: Incident;
  receiver: Receiver;
  onAcceptDelivery: (assignmentId: string, dockId: string, notes: string) => void;
  onRejectDelivery: (assignmentId: string, reason: string) => void;
}

export const ReceiverIntakePortal: React.FC<ReceiverIntakePortalProps> = ({
  assignment,
  incident,
  receiver,
  onAcceptDelivery,
  onRejectDelivery,
}) => {
  const [showRejectModal, setShowRejectModal] = useState<boolean>(false);
  const [showAcceptModal, setShowAcceptModal] = useState<boolean>(false);
  const [rejectReason, setRejectReason] = useState<string>('');
  const [dockId, setDockId] = useState<string>('DOCK-B2 (Cryo Inflow)');
  const [acceptanceNotes, setAcceptanceNotes] = useState<string>('Temperature within nominal -70C boundary. Intake into cryogenic chamber completed.');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const isCompleted = assignment.status === 'completed';
  const isRejectedByReceiver = assignment.status === 'rejected';

  // Receiver can accept if status is 'handoff_submitted', 'arrived', or 'en_route'
  const canAcceptOrReject =
    assignment.status === 'handoff_submitted' ||
    assignment.status === 'arrived' ||
    assignment.status === 'en_route';

  const handleConfirmAccept = () => {
    setIsSubmitting(true);
    onAcceptDelivery(assignment.assignment_id, dockId, acceptanceNotes);
    setIsSubmitting(false);
    setShowAcceptModal(false);
  };

  const handleConfirmReject = () => {
    if (rejectReason.trim().length < 5) return;
    setIsSubmitting(true);
    onRejectDelivery(assignment.assignment_id, rejectReason.trim());
    setIsSubmitting(false);
    setShowRejectModal(false);
  };

  return (
    <div
      style={{
        maxWidth: '540px',
        margin: '0 auto',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
        padding: '8px 0',
      }}
    >
      {/* Facility Header */}
      <div className="card" style={{ borderLeft: '6px solid var(--accent-cyan)', padding: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>RECEIVING VAULT INTAKE</span>
          <StatusBadge status={receiver.operational_availability} />
        </div>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 800, marginTop: '4px' }}>
          {receiver.name}
        </h2>
        <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          {receiver.location} | Dock Telemetry Online
        </div>
      </div>

      {/* Facility Operational Capabilities Check */}
      <section className="card" aria-label="Receiver Plant Status">
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '10px' }}>Facility Safety Health</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px', fontSize: '0.85rem' }}>
          <div style={{ backgroundColor: 'var(--bg-elevated)', padding: '10px', borderRadius: 'var(--radius-sm)' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', display: 'block' }}>COOLING PLANT</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '2px', fontWeight: 700 }}>
              <SnowflakeIcon size={16} color="var(--status-safe)" />
              {receiver.cooling_status.toUpperCase()}
            </div>
          </div>
          <div style={{ backgroundColor: 'var(--bg-elevated)', padding: '10px', borderRadius: 'var(--radius-sm)' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', display: 'block' }}>BACKUP POWER</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '2px', fontWeight: 700 }}>
              <ZapIcon size={16} color="var(--status-safe)" />
              {receiver.backup_runtime_min} MINS
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '10px', fontSize: '0.85rem' }}>
          <span style={{ color: 'var(--text-secondary)' }}>Available Chamber Space:</span>
          <strong>{receiver.available_capacity_kg.toLocaleString()} kg</strong>
        </div>
      </section>

      {/* Incoming Delivery Details */}
      <section className="card" aria-label="Incoming Delivery Cargo Details">
        <div className="card-header">
          <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>Incoming Cargo Dispatch</h3>
          <StatusBadge status={assignment.status} />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.85rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-secondary)' }}>Assignment ID:</span>
            <span style={{ fontFamily: 'monospace' }}>{assignment.assignment_id}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-secondary)' }}>Incident Ref:</span>
            <span style={{ fontFamily: 'monospace' }}>{assignment.incident_id}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-secondary)' }}>Cargo Type:</span>
            <strong>{incident.cargo.cargo_type}</strong>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-secondary)' }}>Cargo Mass:</span>
            <strong>{assignment.cargo_kg.toLocaleString()} kg</strong>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-secondary)' }}>Assigned Driver:</span>
            <span>{assignment.driver_name}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-secondary)' }}>Estimated ETA:</span>
            <strong>{assignment.estimated_arrival}</strong>
          </div>
        </div>
      </section>

      {/* Receiver Intake Decision Controls */}
      <section className="card" aria-label="Intake Acceptance Controls">
        <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '10px' }}>Receiver Intake Decision</h3>

        {canAcceptOrReject && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <button
              className="btn btn-primary"
              onClick={() => setShowAcceptModal(true)}
              style={{ width: '100%', minHeight: '48px', fontSize: '1rem' }}
            >
              <CheckCircleIcon size={20} /> Accept & Confirm Cargo Intake
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => setShowRejectModal(true)}
              style={{ width: '100%', minHeight: '44px', color: 'var(--status-critical)' }}
            >
              <XCircleIcon size={18} /> Reject Cargo Intake
            </button>
          </div>
        )}

        {isCompleted && (
          <div style={{ backgroundColor: 'var(--status-safe-bg)', padding: '12px', borderRadius: 'var(--radius-sm)', color: '#6ee7b7' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700 }}>
              <CheckCircleIcon size={20} /> INTAKE COMPLETED & SAFELY STORED
            </div>
            <p style={{ fontSize: '0.8rem', marginTop: '4px' }}>
              Cargo transfer confirmed. Available facility capacity has been updated in audit records.
            </p>
          </div>
        )}

        {isRejectedByReceiver && (
          <div style={{ backgroundColor: 'var(--status-critical-bg)', padding: '12px', borderRadius: 'var(--radius-sm)', color: '#fca5a5' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700 }}>
              <XCircleIcon size={20} /> INTAKE REJECTED BY RECEIVER
            </div>
            <p style={{ fontSize: '0.8rem', marginTop: '4px' }}>
              Reason: {assignment.receiver_rejection_reason || 'Facility rejected delivery upon inspection.'}
            </p>
          </div>
        )}
      </section>

      {/* Acceptance Modal */}
      <Modal
        isOpen={showAcceptModal}
        onClose={() => setShowAcceptModal(false)}
        title="Confirm Intake & Vault Transfer"
        footer={
          <>
            <button className="btn btn-secondary" onClick={() => setShowAcceptModal(false)}>
              Cancel
            </button>
            <button className="btn btn-primary" onClick={handleConfirmAccept} disabled={isSubmitting}>
              Confirm Intake
            </button>
          </>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div>
            <label htmlFor="dock-selection" className="form-label">
              Receiving Dock Chamber:
            </label>
            <input
              id="dock-selection"
              className="form-input"
              value={dockId}
              onChange={(e) => setDockId(e.target.value)}
            />
          </div>

          <div>
            <label htmlFor="intake-notes" className="form-label">
              Intake Inspection Notes:
            </label>
            <textarea
              id="intake-notes"
              className="form-textarea"
              rows={3}
              value={acceptanceNotes}
              onChange={(e) => setAcceptanceNotes(e.target.value)}
            />
          </div>
        </div>
      </Modal>

      {/* Rejection Modal */}
      <Modal
        isOpen={showRejectModal}
        onClose={() => setShowRejectModal(false)}
        title="Reject Delivery Intake"
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
        <p style={{ fontSize: '0.85rem', marginBottom: '10px' }}>
          Document why the receiving facility cannot accept this delivery (e.g. Broken temperature seal, sudden chamber fault).
        </p>
        <label htmlFor="receiver-reject-reason" className="form-label">
          Rejection Justification (Required):
        </label>
        <textarea
          id="receiver-reject-reason"
          className="form-textarea"
          rows={3}
          placeholder="e.g. Temperature recorder logged 4C above safety limit; seal tampered."
          value={rejectReason}
          onChange={(e) => setRejectReason(e.target.value)}
        />
      </Modal>
    </div>
  );
};
