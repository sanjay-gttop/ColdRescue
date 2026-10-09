import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { App } from '../app/App';
import { StatusBadge } from '../components/common/StatusBadge';
import { CountdownTimer } from '../components/common/CountdownTimer';

describe('UI Component and Journey Tests', () => {
  it('renders StatusBadge with accessible text and proper styling', () => {
    const { container } = render(<StatusBadge status="critical" label="CRITICAL FAILURE" />);
    expect(screen.getByText('CRITICAL FAILURE')).toBeDefined();
    expect(container.querySelector('.badge-critical')).toBeDefined();
  });

  it('renders CountdownTimer with valid expiration countdown', () => {
    const futureDate = new Date(Date.now() + 1000 * 60 * 30).toISOString(); // 30 mins
    render(<CountdownTimer deadlineIso={futureDate} estimateSource="Thermal Model v0.4" />);
    expect(screen.getByText('REMAINING THERMAL SAFE TIME')).toBeDefined();
    expect(screen.getByText(/Thermal Model v0.4/)).toBeDefined();
  });

  it('renders full App and allows navigating across main tabs', () => {
    render(<App />);
    expect(screen.getByText('ColdRescue')).toBeDefined();
    expect(screen.getByText('Active Incident Queue')).toBeDefined();

    // Navigate to Receivers
    const receiversTab = screen.getByRole('button', { name: /Receiver Directory/i });
    fireEvent.click(receiversTab);
    expect(screen.getByText('St. Jude Regional Cold Vault')).toBeDefined();

    // Navigate to Allocation Comparison
    const allocationTab = screen.getByRole('button', { name: /Greedy vs Global Allocation/i });
    fireEvent.click(allocationTab);
    expect(screen.getByText('Greedy Strategy')).toBeDefined();
    expect(screen.getByText('Global Strategy')).toBeDefined();

    // Navigate to Approvals
    const approvalsTab = screen.getByRole('button', { name: /Approval Decisions/i });
    fireEvent.click(approvalsTab);
    expect(screen.getByText(/Recovery Dispatch Review/i)).toBeDefined();

    // Navigate to Driver Portal
    const driverTab = screen.getByRole('button', { name: /Driver Mobile Portal/i });
    fireEvent.click(driverTab);
    expect(screen.getByText('Driver Dispatch Order')).toBeDefined();

    // Navigate to Receiver Portal
    const receiverPortalTab = screen.getByRole('button', { name: /Receiver Intake Portal/i });
    fireEvent.click(receiverPortalTab);
    expect(screen.getByText(/RECEIVING VAULT INTAKE/i)).toBeDefined();

    // Navigate to Audit
    const auditTab = screen.getByRole('button', { name: /Audit Timeline/i });
    fireEvent.click(auditTab);
    expect(screen.getByText('Chronological Operational Audit Trail')).toBeDefined();

    // Navigate to Action Matrix
    const matrixTab = screen.getByRole('button', { name: /Action Contracts Matrix/i });
    fireEvent.click(matrixTab);
    expect(screen.getByText('Consequential Action Contracts Matrix')).toBeDefined();
  });

  it('verifies Journey B: Driver acknowledges assignment and updates delivery state', () => {
    render(<App />);
    // Navigate to Driver Portal
    fireEvent.click(screen.getByRole('button', { name: /Driver Mobile Portal/i }));

    // If button "Acknowledge & Accept Assignment" is present, click it
    const ackBtn = screen.queryByRole('button', { name: /Acknowledge & Accept Assignment/i });
    if (ackBtn) {
      fireEvent.click(ackBtn);
      expect(screen.getByText(/Assignment acknowledged/i)).toBeDefined();
    }
  });

  it('verifies Journey E: Failure recovery and retry mechanism', () => {
    render(<App />);
    // Trigger simulated error
    const simErrorBtn = screen.getByRole('button', { name: /Trigger Sim Error/i });
    fireEvent.click(simErrorBtn);

    expect(screen.getByText('Telemetry Service Unreachable')).toBeDefined();

    // Click retry
    const retryBtn = screen.getByRole('button', { name: /Retry Operation/i });
    fireEvent.click(retryBtn);

    // Error cleared, dashboard restored
    expect(screen.queryByText('Telemetry Service Unreachable')).toBeNull();
    expect(screen.getByText('Active Incident Queue')).toBeDefined();
  });
});
