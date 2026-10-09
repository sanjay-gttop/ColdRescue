import React, { useState } from 'react';
import {
  Incident,
  Receiver,
  Assignment,
  ApprovalRequest,
  AuditEvent,
  DataSourceMode,
} from '../types';
import {
  INITIAL_INCIDENTS,
  INITIAL_RECEIVERS,
  INITIAL_ASSIGNMENTS,
  INITIAL_APPROVALS,
  INITIAL_AUDIT_EVENTS,
} from '../data/mockData';
import { Header } from '../components/layout/Header';
import { Navigation, ActiveTab } from '../components/layout/Navigation';
import { ReliabilityBanner, ErrorState } from '../components/common/ReliabilityView';
import { OperatorDashboard } from '../components/dashboard/OperatorDashboard';
import { IncidentDetailView } from '../components/incidents/IncidentDetailView';
import { ReceiverDirectoryView } from '../components/receivers/ReceiverDirectoryView';
import { AllocationComparisonView } from '../components/allocation/AllocationComparisonView';
import { ApprovalDetailView } from '../components/approvals/ApprovalDetailView';
import { DriverMobilePortal } from '../components/driver/DriverMobilePortal';
import { ReceiverIntakePortal } from '../components/receiver-portal/ReceiverIntakePortal';
import { AuditTimelineView } from '../components/audit/AuditTimelineView';
import { PolicyBlockDetailView } from '../components/policy/PolicyBlockDetailView';
import { ActionMatrixView } from '../components/common/ActionMatrixView';
import { evaluateColdChainPolicy } from '../utils/policyEngine';

export const App: React.FC = () => {
  // App Domain State
  const [incidents, setIncidents] = useState<Incident[]>(INITIAL_INCIDENTS);
  const [receivers, setReceivers] = useState<Receiver[]>(INITIAL_RECEIVERS);
  const [assignments, setAssignments] = useState<Assignment[]>(INITIAL_ASSIGNMENTS);
  const [approvals, setApprovals] = useState<ApprovalRequest[]>(INITIAL_APPROVALS);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>(INITIAL_AUDIT_EVENTS);

  // Navigation State
  const [activeTab, setActiveTab] = useState<ActiveTab>('dashboard');
  const [selectedIncidentId, setSelectedIncidentId] = useState<string>('INC-2026-081');
  const [selectedBlockedReceiverId, setSelectedBlockedReceiverId] = useState<string>('RCV-APEX-03');
  const [selectedAssignmentId, setSelectedAssignmentId] = useState<string>('ASN-8801');

  // Reliability & Simulation State
  const [dataSource, setDataSource] = useState<DataSourceMode>('demo');
  const [isOffline, setIsOffline] = useState<boolean>(false);
  const [isStale, setIsStale] = useState<boolean>(false);
  const [simulatedError, setSimulatedError] = useState<string | null>(null);
  const [lastSyncTime, setLastSyncTime] = useState<string>(new Date().toLocaleTimeString());
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  const addAuditEvent = (
    eventType: string,
    action: string,
    entityRef: string,
    description: string,
    outcome: 'success' | 'failure' | 'blocked' = 'success',
    incidentId?: string
  ) => {
    const newEvent: AuditEvent = {
      event_id: `EVT-AUD-${Date.now().toString().slice(-4)}`,
      event_type: eventType,
      occurred_at: new Date().toISOString(),
      schema_version: '1.0.0',
      incident_id: incidentId || selectedIncidentId,
      correlation_id: `CORR-${Math.floor(Math.random() * 9000 + 1000)}`,
      idempotency_key: `IDEM-${Date.now()}`,
      actor: 'Operator:ActiveSession',
      action,
      entity_reference: entityRef,
      description,
      source: dataSource === 'demo' ? 'simulated_local' : 'live_aws',
      outcome,
    };
    setAuditEvents((prev) => [newEvent, ...prev]);
  };

  // Helper selectors
  const activeIncident = incidents.find((i) => i.incident_id === selectedIncidentId) || incidents[0];
  const activeApproval = approvals[0] || INITIAL_APPROVALS[0];
  const activeReceiver = receivers.find((r) => r.receiver_id === activeApproval.proposed_receiver_id) || receivers[0];
  const blockedReceiver = receivers.find((r) => r.receiver_id === selectedBlockedReceiverId) || receivers[2];
  const activeAssignment = assignments.find((a) => a.assignment_id === selectedAssignmentId) || assignments[0];

  // Action handlers
  const handleSelectIncident = (id: string) => {
    setSelectedIncidentId(id);
    setActiveTab('incidents');
    showToast(`Switched view to Incident: ${id}`);
  };

  const handleSelectReceiverForIncident = (incidentId: string) => {
    setSelectedIncidentId(incidentId);
    setActiveTab('receivers');
  };

  const handleSelectReceiverProposal = (receiverId: string) => {
    if (isOffline) {
      showToast('⚠️ Action locked: System is in OFFLINE state.');
      return;
    }
    const targetReceiver = receivers.find((r) => r.receiver_id === receiverId);
    if (!targetReceiver) return;

    const policy = evaluateColdChainPolicy(activeIncident, targetReceiver);
    if (policy.is_hard_blocked) {
      setSelectedBlockedReceiverId(receiverId);
      setActiveTab('policy-block');
      addAuditEvent('POLICY_EVALUATION', 'BLOCK_PROPOSAL', receiverId, `Hard safety block triggered for ${activeIncident.incident_id}`, 'blocked', activeIncident.incident_id);
      return;
    }

    // Create or update pending approval
    const newApproval: ApprovalRequest = {
      approval_id: `APP-2026-${Math.floor(Math.random() * 900 + 100)}`,
      assignment_id: `ASN-${Math.floor(Math.random() * 9000 + 1000)}`,
      incident_id: activeIncident.incident_id,
      proposed_receiver_id: receiverId,
      status: 'pending',
      requester: 'Operator Decision Console',
      policy_assessment: policy,
    };

    setApprovals([newApproval, ...approvals]);
    addAuditEvent('PROPOSAL_DRAFTED', 'CREATE_APPROVAL_REQUEST', newApproval.approval_id, `Proposed recovery to ${targetReceiver.name}`, 'success', activeIncident.incident_id);
    setActiveTab('approvals');
    showToast(`Recovery proposal created for ${targetReceiver.name}. Routed to Approvals.`);
  };

  const handleInspectPolicyBlock = (receiverId: string) => {
    setSelectedBlockedReceiverId(receiverId);
    setActiveTab('policy-block');
  };

  const handleApproveProposal = (approvalId: string, approverName: string) => {
    if (isOffline) {
      showToast('⚠️ Cannot approve: System is currently offline.');
      return;
    }

    setApprovals((prev) =>
      prev.map((a) => (a.approval_id === approvalId ? { ...a, status: 'approved', approver: approverName } : a))
    );

    // Update assignment and incident status
    const matchingApproval = approvals.find((a) => a.approval_id === approvalId);
    if (matchingApproval) {
      setAssignments((prev) =>
        prev.map((asn) =>
          asn.assignment_id === matchingApproval.assignment_id || asn.incident_id === matchingApproval.incident_id
            ? { ...asn, status: 'approved' }
            : asn
        )
      );
      setIncidents((prev) =>
        prev.map((inc) =>
          inc.incident_id === matchingApproval.incident_id ? { ...inc, status: 'allocated' } : inc
        )
      );
      setSelectedAssignmentId(matchingApproval.assignment_id);
    }

    addAuditEvent(
      'APPROVAL_GRANTED',
      'AUTHORIZE_RECOVERY_DISPATCH',
      approvalId,
      `Authorized recovery dispatch to ${activeReceiver.name}. Assigned to Driver.`,
      'success',
      activeIncident.incident_id
    );

    showToast(`✅ Approval Granted by ${approverName}. Assignment sent to Driver.`);
    setActiveTab('driver');
  };

  const handleRejectProposal = (approvalId: string, reason: string) => {
    setApprovals((prev) =>
      prev.map((a) => (a.approval_id === approvalId ? { ...a, status: 'rejected', comments: reason } : a))
    );

    addAuditEvent(
      'APPROVAL_REJECTED',
      'REJECT_RECOVERY_DISPATCH',
      approvalId,
      `Proposal rejected. Rationale: ${reason}`,
      'failure',
      activeIncident.incident_id
    );

    showToast(`Proposal rejected. Logged to audit timeline.`);
    setActiveTab('audit');
  };

  const handleRequestReassessment = (approvalId: string) => {
    showToast(`Reassessment requested for ${approvalId}. Opening allocation comparison...`);
    setActiveTab('allocation');
  };

  // Driver actions
  const handleDriverAcknowledge = (assignmentId: string) => {
    setAssignments((prev) =>
      prev.map((a) => (a.assignment_id === assignmentId ? { ...a, status: 'acknowledged' } : a))
    );
    addAuditEvent('DRIVER_ACKNOWLEDGED', 'ACCEPT_JOB', assignmentId, 'Driver acknowledged emergency dispatch order.', 'success');
    showToast('Driver acknowledged job.');
  };

  const handleDriverDecline = (assignmentId: string, reason: string) => {
    setAssignments((prev) =>
      prev.map((a) => (a.assignment_id === assignmentId ? { ...a, status: 'declined', decline_reason: reason } : a))
    );
    addAuditEvent('DRIVER_DECLINED', 'DECLINE_JOB', assignmentId, `Driver declined. Reason: ${reason}`, 'failure');
    showToast('Driver declined job. Reassignment needed.');
  };

  const handleDriverProgress = (assignmentId: string, stage: 'departed' | 'halfway' | 'arriving' | 'arrived') => {
    const nextStatus = stage === 'arrived' ? 'arrived' : 'en_route';
    setAssignments((prev) =>
      prev.map((a) => (a.assignment_id === assignmentId ? { ...a, status: nextStatus, progress_stage: stage } : a))
    );
    addAuditEvent('DELIVERY_PROGRESS_UPDATED', `UPDATE_STAGE_${stage.toUpperCase()}`, assignmentId, `Driver progress updated: ${stage}`, 'success');
    showToast(`Driver stage updated: ${stage.toUpperCase()}`);
  };

  const handleDriverHandoff = (assignmentId: string, tempC: number, notes: string) => {
    setAssignments((prev) =>
      prev.map((a) =>
        a.assignment_id === assignmentId
          ? { ...a, status: 'handoff_submitted', handoff_notes: notes }
          : a
      )
    );
    addAuditEvent(
      'HANDOFF_SUBMITTED',
      'SUBMIT_DELIVERY_HANDOFF',
      assignmentId,
      `Driver completed handoff. Arrival temp: ${tempC}°C. Notes: ${notes}`,
      'success'
    );
    showToast('Handoff logged. Opening Receiver Portal for intake confirmation.');
    setActiveTab('receiver-portal');
  };

  // Receiver actions
  const handleReceiverAccept = (assignmentId: string, dockId: string, notes: string) => {
    setAssignments((prev) =>
      prev.map((a) => (a.assignment_id === assignmentId ? { ...a, status: 'completed' } : a))
    );
    setIncidents((prev) =>
      prev.map((i) => (i.incident_id === activeIncident.incident_id ? { ...i, status: 'delivered' } : i))
    );
    // Deduct receiver capacity
    setReceivers((prev) =>
      prev.map((r) =>
        r.receiver_id === activeReceiver.receiver_id
          ? { ...r, available_capacity_kg: Math.max(0, r.available_capacity_kg - activeIncident.cargo.cargo_kg) }
          : r
      )
    );
    addAuditEvent(
      'RECEIVER_ACCEPTED_DELIVERY',
      'INTAKE_CARGO_CONFIRMED',
      assignmentId,
      `Receiver accepted cargo at ${dockId}. Notes: ${notes}`,
      'success'
    );
    showToast('Cargo intake confirmed and safely stored. Audit record created.');
    setActiveTab('audit');
  };

  const handleReceiverReject = (assignmentId: string, reason: string) => {
    setAssignments((prev) =>
      prev.map((a) => (a.assignment_id === assignmentId ? { ...a, status: 'rejected', receiver_rejection_reason: reason } : a))
    );
    addAuditEvent(
      'RECEIVER_REJECTED_DELIVERY',
      'INTAKE_REJECTED',
      assignmentId,
      `Receiver rejected cargo. Justification: ${reason}`,
      'failure'
    );
    showToast('Intake rejected. Alert raised for emergency contingency.');
    setActiveTab('audit');
  };

  // Refresh & simulation triggers
  const handleRefresh = () => {
    setIsStale(false);
    setSimulatedError(null);
    setLastSyncTime(new Date().toLocaleTimeString());
    addAuditEvent('TELEMETRY_REFRESHED', 'SYNC_STATE', 'FLEET_CACHE', 'Refreshed telemetry across all reefer units and vault monitors.', 'success');
    showToast('Telemetry refreshed.');
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Global Header */}
      <Header
        dataSource={dataSource}
        isOffline={isOffline}
        isStale={isStale}
        onRefresh={handleRefresh}
        onToggleOffline={() => {
          setIsOffline(!isOffline);
          showToast(!isOffline ? 'Offline Mode Active' : 'Online Mode Restored');
        }}
        onToggleStale={() => {
          setIsStale(!isStale);
          showToast(!isStale ? 'Telemetry marked stale' : 'Telemetry restored to fresh');
        }}
        onToggleDataSource={() => {
          const next = dataSource === 'demo' ? 'live' : 'demo';
          setDataSource(next);
          showToast(`Data source switched to: ${next.toUpperCase()}`);
        }}
      />

      {/* Primary Navigation Tabs */}
      <Navigation
        activeTab={activeTab}
        onTabChange={(tab) => {
          setActiveTab(tab);
          setSimulatedError(null);
        }}
        pendingApprovalsCount={approvals.filter((a) => a.status === 'pending').length}
        criticalIncidentsCount={incidents.filter((i) => i.severity === 'critical').length}
      />

      {/* Main Content Area */}
      <main className="container" style={{ flex: 1, padding: '20px 16px' }}>
        {/* Toast Notification */}
        {toastMessage && (
          <div
            role="status"
            aria-live="polite"
            style={{
              position: 'fixed',
              bottom: '24px',
              right: '24px',
              zIndex: 100,
              backgroundColor: 'var(--bg-elevated)',
              color: 'var(--text-primary)',
              padding: '12px 20px',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-focus)',
              boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)',
              fontWeight: 600,
              fontSize: '0.9rem',
            }}
          >
            {toastMessage}
          </div>
        )}

        {/* Reliability Banner (Stale / Offline Notices) */}
        <ReliabilityBanner
          isStale={isStale}
          isOffline={isOffline}
          lastUpdated={lastSyncTime}
          onRefresh={handleRefresh}
          onReconnect={() => setIsOffline(false)}
        />

        {/* Simulated Failure State for Journey E Testing */}
        {simulatedError ? (
          <ErrorState
            title="Telemetry Service Unreachable"
            message={simulatedError}
            onRetry={() => {
              setSimulatedError(null);
              showToast('Service recovered. Normal operations restored.');
            }}
          />
        ) : (
          <>
            {/* View Switching */}
            {activeTab === 'dashboard' && (
              <OperatorDashboard
                incidents={incidents}
                receivers={receivers}
                approvals={approvals}
                auditEvents={auditEvents}
                onSelectIncident={handleSelectIncident}
                onNavigateToApprovals={() => setActiveTab('approvals')}
                onNavigateToReceivers={() => setActiveTab('receivers')}
                onNavigateToAllocation={() => setActiveTab('allocation')}
                onNavigateToAudit={() => setActiveTab('audit')}
              />
            )}

            {activeTab === 'incidents' && (
              <IncidentDetailView
                incident={activeIncident}
                onBack={() => setActiveTab('dashboard')}
                onSelectReceiverForIncident={handleSelectReceiverForIncident}
                onCompareAllocation={() => setActiveTab('allocation')}
              />
            )}

            {activeTab === 'receivers' && (
              <ReceiverDirectoryView
                receivers={receivers}
                activeIncident={activeIncident}
                onSelectReceiverProposal={handleSelectReceiverProposal}
                onInspectPolicyBlock={handleInspectPolicyBlock}
              />
            )}

            {activeTab === 'allocation' && (
              <AllocationComparisonView
                incidents={incidents}
                receivers={receivers}
                onSelectProposedAssignment={(incId, recvId) => {
                  setSelectedIncidentId(incId);
                  handleSelectReceiverProposal(recvId);
                }}
              />
            )}

            {activeTab === 'approvals' && (
              <ApprovalDetailView
                approval={activeApproval}
                incident={activeIncident}
                receiver={activeReceiver}
                alternativeReceivers={receivers.filter((r) => r.receiver_id !== activeReceiver.receiver_id)}
                onApprove={handleApproveProposal}
                onReject={handleRejectProposal}
                onRequestReassessment={handleRequestReassessment}
                onSelectAlternative={(altId) => handleSelectReceiverProposal(altId)}
              />
            )}

            {activeTab === 'driver' && (
              <DriverMobilePortal
                assignment={activeAssignment}
                incident={activeIncident}
                onAcknowledge={handleDriverAcknowledge}
                onDecline={handleDriverDecline}
                onUpdateProgress={handleDriverProgress}
                onSubmitHandoff={handleDriverHandoff}
              />
            )}

            {activeTab === 'receiver-portal' && (
              <ReceiverIntakePortal
                assignment={activeAssignment}
                incident={activeIncident}
                receiver={activeReceiver}
                onAcceptDelivery={handleReceiverAccept}
                onRejectDelivery={handleReceiverReject}
              />
            )}

            {activeTab === 'audit' && <AuditTimelineView events={auditEvents} />}

            {activeTab === 'policy-block' && (
              <PolicyBlockDetailView
                incident={activeIncident}
                receiver={blockedReceiver}
                alternativeReceivers={receivers.filter((r) => r.receiver_id === 'RCV-CENTRAL-01' || r.receiver_id === 'RCV-VALLEY-02')}
                onBack={() => setActiveTab('receivers')}
                onSelectAlternative={(altId) => handleSelectReceiverProposal(altId)}
                onReevaluate={() => {
                  showToast('Re-evaluated policy: Hard block remains active on current telemetry.');
                }}
              />
            )}

            {activeTab === 'action-matrix' && <ActionMatrixView />}
          </>
        )}
      </main>

      {/* Footer */}
      <footer
        style={{
          backgroundColor: 'var(--bg-secondary)',
          borderTop: '1px solid var(--border-subtle)',
          padding: '16px 20px',
          textAlign: 'center',
          fontSize: '0.8rem',
          color: 'var(--text-muted)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'center', gap: '20px', flexWrap: 'wrap', marginBottom: '6px' }}>
          <span>ColdRescue Operations v0.1.0</span>
          <span>•</span>
          <span>Milestone 1 Frontend Prototype</span>
          <span>•</span>
          <button
            onClick={() => setSimulatedError('Simulated 503 Gateway Timeout: Live AWS Endpoint unreachable.')}
            style={{ color: 'var(--status-critical)', textDecoration: 'underline' }}
          >
            Trigger Sim Error (Journey E)
          </button>
        </div>
        <div>Designed for zero-compromise emergency cold-chain decision support. All safety bounds strictly enforced.</div>
      </footer>
    </div>
  );
};
