import React, { useState } from 'react';
import { Assignment, Incident } from '../../types';
import { StatusBadge } from '../common/StatusBadge';
import { Modal } from '../common/Modal';
import {
  TruckIcon,
  MapPinIcon,
  ThermometerIcon,
  CheckCircleIcon,
  PhoneIcon,
  FileTextIcon,
} from '../common/Icons';

interface DriverMobilePortalProps {
  assignment: Assignment;
  incident: Incident;
  onAcknowledge: (assignmentId: string) => void;
  onDecline: (assignmentId: string, reason: string) => void;
  onUpdateProgress: (assignmentId: string, stage: 'departed' | 'halfway' | 'arriving' | 'arrived') => void;
  onSubmitHandoff: (assignmentId: string, tempC: number, notes: string) => void;
}

export const DriverMobilePortal: React.FC<DriverMobilePortalProps> = ({
  assignment,
  incident,
  onAcknowledge,
  onDecline,
  onUpdateProgress,
  onSubmitHandoff,
}) => {
  const [showDeclineModal, setShowDeclineModal] = useState<boolean>(false);
  const [showHandoffModal, setShowHandoffModal] = useState<boolean>(false);
  const [declineReason, setDeclineReason] = useState<string>('');
  const [arrivalTempC, setArrivalTempC] = useState<string>('-67.2');
  const [handoffNotes, setHandoffNotes] = useState<string>('Intact cryogenic seal. Handed off to intake dock supervisor.');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const isAcknowledged = assignment.status === 'acknowledged';
  const isEnRoute = assignment.status === 'en_route';
  const isArrived = assignment.status === 'arrived';
  const isHandoffSubmitted = assignment.status === 'handoff_submitted' || assignment.status === 'completed';
  const isDeclined = assignment.status === 'declined';

  const handleDeclineSubmit = () => {
    if (declineReason.trim().length < 5) return;
    setIsSubmitting(true);
    onDecline(assignment.assignment_id, declineReason.trim());
    setIsSubmitting(false);
    setShowDeclineModal(false);
  };

  const handleHandoffSubmit = () => {
    setIsSubmitting(true);
    onSubmitHandoff(assignment.assignment_id, parseFloat(arrivalTempC) || 0, handoffNotes);
    setIsSubmitting(false);
    setShowHandoffModal(false);
  };

  return (
    <div
      style={{
        maxWidth: '520px',
        margin: '0 auto',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
        padding: '8px 0',
      }}
    >
      {/* Mobile Header Banner */}
      <div className="card" style={{ borderLeft: '6px solid var(--accent-blue)', padding: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
            {assignment.assignment_id}
          </span>
          <StatusBadge status={assignment.status} />
        </div>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 800, marginTop: '4px' }}>
          Driver Dispatch Order
        </h2>
        <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          Driver Assigned: <strong>{assignment.driver_name}</strong> ({assignment.driver_id})
        </div>
      </div>

      {/* Cargo & Safety Alert Card */}
      <section className="card" aria-label="Cargo and Emergency Safety Instructions">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
          <ThermometerIcon size={20} color="var(--accent-cyan)" />
          <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>Critical Cargo Summary</h3>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border-subtle)', fontSize: '0.9rem' }}>
          <span style={{ color: 'var(--text-secondary)' }}>Cargo Type:</span>
          <strong>{incident.cargo.cargo_type}</strong>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border-subtle)', fontSize: '0.9rem' }}>
          <span style={{ color: 'var(--text-secondary)' }}>Cargo Weight:</span>
          <strong>{assignment.cargo_kg.toLocaleString()} kg</strong>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', fontSize: '0.9rem' }}>
          <span style={{ color: 'var(--text-secondary)' }}>Safe Temperature Range:</span>
          <strong style={{ color: 'var(--accent-cyan)' }}>
            {incident.cargo.safe_temperature_min}°C to {incident.cargo.safe_temperature_max}°C
          </strong>
        </div>

        {/* Safety Handling Instructions */}
        <div style={{ marginTop: '12px', backgroundColor: 'var(--bg-elevated)', padding: '12px', borderRadius: 'var(--radius-sm)' }}>
          <strong style={{ fontSize: '0.8rem', color: 'var(--status-warning)', display: 'block', marginBottom: '6px' }}>
            ⚠️ DRIVER SAFETY HANDLING PROTOCOL:
          </strong>
          <ul style={{ paddingLeft: '18px', fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {assignment.safety_instructions.map((inst, i) => (
              <li key={i}>{inst}</li>
            ))}
          </ul>
        </div>
      </section>

      {/* Route & Locations */}
      <section className="card" aria-label="Route and Delivery Location">
        <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <MapPinIcon size={18} /> Route Information
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.85rem' }}>
          <div style={{ borderLeft: '2px solid var(--border-strong)', paddingLeft: '10px' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>PICKUP LOCATION (TRUCK BREAKDOWN):</span>
            <div style={{ fontWeight: 600 }}>{assignment.pickup_location}</div>
          </div>

          <div style={{ borderLeft: '2px solid var(--status-safe-border)', paddingLeft: '10px' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>DESTINATION (COLD STORAGE VAULT):</span>
            <div style={{ fontWeight: 600, color: 'var(--status-safe)' }}>{assignment.destination_location}</div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '6px', fontSize: '0.8rem' }}>
            <span style={{ color: 'var(--text-secondary)' }}>Estimated Travel Time:</span>
            <strong>{assignment.estimated_arrival}</strong>
          </div>

          {assignment.contact_phone && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-cyan)', fontSize: '0.85rem', marginTop: '4px' }}>
              <PhoneIcon size={16} /> Contact Dispatch: {assignment.contact_phone}
            </div>
          )}
        </div>
      </section>

      {/* Journey Step Actions (Mobile First Buttons >= 44px touch targets) */}
      <section className="card" aria-label="Driver Journey Actions">
        <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '12px' }}>Operational Action</h3>

        {/* State 1: Awaiting Acknowledgment */}
        {assignment.status === 'approved' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <button
              className="btn btn-primary"
              onClick={() => onAcknowledge(assignment.assignment_id)}
              style={{ width: '100%', minHeight: '48px', fontSize: '1rem' }}
            >
              <CheckCircleIcon size={20} /> Acknowledge & Accept Assignment
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => setShowDeclineModal(true)}
              style={{ width: '100%', minHeight: '44px', color: 'var(--status-critical)' }}
            >
              Decline Assignment
            </button>
          </div>
        )}

        {/* State 2: Acknowledged -> Mark Departed */}
        {isAcknowledged && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <p style={{ fontSize: '0.85rem', color: 'var(--status-safe)' }}>
              ✅ Assignment acknowledged. Proceed to pickup site and depart toward receiving dock.
            </p>
            <button
              className="btn btn-primary"
              onClick={() => onUpdateProgress(assignment.assignment_id, 'departed')}
              style={{ width: '100%', minHeight: '48px', fontSize: '1rem' }}
            >
              <TruckIcon size={20} /> Mark Departed / En Route
            </button>
          </div>
        )}

        {/* State 3: En Route -> Mark Arrived */}
        {isEnRoute && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Status: In Transit</span>
              <span className="badge badge-pending">EN ROUTE</span>
            </div>
            <button
              className="btn btn-primary"
              onClick={() => onUpdateProgress(assignment.assignment_id, 'arrived')}
              style={{ width: '100%', minHeight: '48px', fontSize: '1rem' }}
            >
              <MapPinIcon size={20} /> Mark Arrived at Receiving Dock
            </button>
          </div>
        )}

        {/* State 4: Arrived -> Submit Handoff */}
        {isArrived && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <p style={{ fontSize: '0.85rem', color: 'var(--status-safe)' }}>
              📍 Arrived at facility dock. Verify seals and temperature gauge before handoff.
            </p>
            <button
              className="btn btn-primary"
              onClick={() => setShowHandoffModal(true)}
              style={{ width: '100%', minHeight: '48px', fontSize: '1rem' }}
            >
              <FileTextIcon size={20} /> Complete Delivery Handoff
            </button>
          </div>
        )}

        {/* State 5: Handoff Submitted */}
        {isHandoffSubmitted && (
          <div style={{ textAlign: 'center', padding: '12px' }}>
            <div style={{ color: 'var(--status-safe)', fontWeight: 700, fontSize: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}>
              <CheckCircleIcon size={20} /> Delivery Handoff Submitted
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
              Awaiting receiver portal intake confirmation and warehouse logging.
            </p>
          </div>
        )}

        {/* Declined State */}
        {isDeclined && (
          <div style={{ backgroundColor: 'var(--status-critical-bg)', padding: '12px', borderRadius: 'var(--radius-sm)', color: '#fca5a5' }}>
            <strong>ASSIGNMENT DECLINED</strong>
            <p style={{ fontSize: '0.8rem', marginTop: '4px' }}>
              Reason: {assignment.decline_reason || 'Driver reported mechanical issue or unavailability.'}
            </p>
          </div>
        )}
      </section>

      {/* Decline Assignment Modal */}
      <Modal
        isOpen={showDeclineModal}
        onClose={() => setShowDeclineModal(false)}
        title="Decline Emergency Assignment"
        footer={
          <>
            <button className="btn btn-secondary" onClick={() => setShowDeclineModal(false)}>
              Cancel
            </button>
            <button
              className="btn btn-danger"
              onClick={handleDeclineSubmit}
              disabled={declineReason.trim().length < 5 || isSubmitting}
            >
              Confirm Decline
            </button>
          </>
        }
      >
        <p style={{ fontSize: '0.85rem', marginBottom: '10px' }}>
          Declining this emergency recovery assignment will immediately alert dispatch to re-route another driver.
        </p>
        <label htmlFor="driver-decline-reason" className="form-label">
          Reason for Declining (Required):
        </label>
        <textarea
          id="driver-decline-reason"
          className="form-textarea"
          rows={3}
          placeholder="e.g. Hours of Service limit reached; vehicle flat tire on feeder route."
          value={declineReason}
          onChange={(e) => setDeclineReason(e.target.value)}
        />
      </Modal>

      {/* Handoff Modal */}
      <Modal
        isOpen={showHandoffModal}
        onClose={() => setShowHandoffModal(false)}
        title="Submit Delivery Handoff Log"
        footer={
          <>
            <button className="btn btn-secondary" onClick={() => setShowHandoffModal(false)}>
              Cancel
            </button>
            <button className="btn btn-primary" onClick={handleHandoffSubmit} disabled={isSubmitting}>
              Submit Handoff
            </button>
          </>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div>
            <label htmlFor="temp-reading" className="form-label">
              Arrival Temperature Gauge Reading (°C):
            </label>
            <input
              id="temp-reading"
              className="form-input"
              value={arrivalTempC}
              onChange={(e) => setArrivalTempC(e.target.value)}
            />
          </div>

          <div>
            <label htmlFor="handoff-notes" className="form-label">
              Handoff Observations & Seal Integrity:
            </label>
            <textarea
              id="handoff-notes"
              className="form-textarea"
              rows={3}
              value={handoffNotes}
              onChange={(e) => setHandoffNotes(e.target.value)}
            />
          </div>
        </div>
      </Modal>
    </div>
  );
};
