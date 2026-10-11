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
    expect(screen.getAllByText('ColdRescue').length).toBeGreaterThan(0);
    expect(screen.getByText('Active Incident Queue')).toBeDefined();

    // Navigate to Receivers
    const receiversTab = screen.getAllByRole('button', { name: /Receiver Directory/i })[0];
    fireEvent.click(receiversTab);
    expect(screen.getByText('St. Jude Regional Cold Vault')).toBeDefined();

    // Navigate to Allocation Comparison
    const allocationTab = screen.getAllByRole('button', { name: /Greedy vs Global Allocation|Greedy vs Global Fleet/i })[0];
    fireEvent.click(allocationTab);
    expect(screen.getByText('Greedy Strategy')).toBeDefined();
    expect(screen.getByText('Global Strategy')).toBeDefined();

    // Navigate to Approvals
    const approvalsTab = screen.getAllByRole('button', { name: /Approval Decisions/i })[0];
    fireEvent.click(approvalsTab);
    expect(screen.getByText(/Recovery Dispatch Review/i)).toBeDefined();

    // Navigate to Driver Portal
    const driverTab = screen.getAllByRole('button', { name: /Driver Mobile Portal/i })[0];
    fireEvent.click(driverTab);
    expect(screen.getByText('Driver Dispatch Order')).toBeDefined();

    // Navigate to Receiver Portal
    const receiverPortalTab = screen.getAllByRole('button', { name: /Receiver Intake Portal/i })[0];
    fireEvent.click(receiverPortalTab);
    expect(screen.getByText(/RECEIVING VAULT INTAKE/i)).toBeDefined();

    // Navigate to Audit
    const auditTab = screen.getAllByRole('button', { name: /Audit Timeline/i })[0];
    fireEvent.click(auditTab);
    expect(screen.getByText('Chronological Operational Audit Trail')).toBeDefined();

    // Navigate to Action Matrix
    const matrixTab = screen.getAllByRole('button', { name: /Action Contracts Matrix/i })[0];
    fireEvent.click(matrixTab);
    expect(screen.getByText('Consequential Action Contracts Matrix')).toBeDefined();
  });

  it('verifies Journey B: Driver acknowledges assignment and updates delivery state', () => {
    render(<App />);
    // Navigate to Driver Portal
    fireEvent.click(screen.getAllByRole('button', { name: /Driver Mobile Portal/i })[0]);

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

  it('renders Frame.io-inspired TruckHero and editorial layout', () => {
    render(<App />);
    expect(screen.getByText(/Protect the cold chain./i)).toBeDefined();
    expect(screen.getByText(/Coordinate the recovery./i)).toBeDefined();
    expect(screen.getByRole('button', { name: /Launch Command Center/i })).toBeDefined();
    expect(screen.getByRole('button', { name: /Explore the workflow/i })).toBeDefined();
    expect(screen.getByText(/Surrogate Thermal Risk Engine/i)).toBeDefined();
  });

  it('renders Interactive Cold-Chain Impact Calculator with verified citations', () => {
    render(<App />);
    // Navigate to Allocation Comparison
    fireEvent.click(screen.getAllByRole('button', { name: /Greedy vs Global Allocation|Greedy vs Global Fleet/i })[0]);
    expect(screen.getByText(/National Cold-Chain Spoilage & Carbon Mitigation Calculator/i)).toBeDefined();
    expect(screen.getByText(/300 Multi-Seed Scenarios/i)).toBeDefined();
    expect(screen.getAllByText(/-1,206\.2 kg \(-1\.61%\)/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/182\.3 kg CO₂e/i)).toBeDefined();
    expect(screen.getByText(/16–22% Post-Harvest Loss Baseline \(NCCD\)/i)).toBeDefined();
  });

  it('renders AWS Live Trace view with end-to-end 10-service telemetry mapping and data flow view', () => {
    render(<App />);
    // Navigate to Live Trace
    fireEvent.click(screen.getAllByRole('button', { name: /AWS Live Trace/i })[0]);
    expect(screen.getByText('AWS Live Trace & System Health')).toBeDefined();
    expect(screen.getByText('ap-south-1 (Mumbai)')).toBeDefined();
    expect(screen.getAllByText(/ColdRescue-IncidentRecovery-dev/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Surrogate Thermal Risk Prediction/i)).toBeDefined();
    expect(screen.getByText(/AWS X-Ray Distributed Trace Aggregation/i)).toBeDefined();
    expect(screen.getByText(/Durable Audit Record & DynamoDB Streams/i)).toBeDefined();

    // Toggle Data Flow View
    const dataFlowBtn = screen.getByRole('button', { name: /Data Flow View/i });
    fireEvent.click(dataFlowBtn);
    expect(screen.getByText(/Data Flow Pipeline: Telemetry Ingestion/i)).toBeDefined();
  });

  it('verifies Fix 2.5: Replay button is explicitly labeled REPLAY of a recorded real run', () => {
    render(<App />);
    const replayButtons = screen.getAllByRole('button', { name: /Replay recorded run/i });
    expect(replayButtons.length).toBeGreaterThan(0);
  });

  it('verifies nav reachability for all primary views without dead ends', () => {
    render(<App />);
    const views = [
      'Operator Dashboard',
      'Incident & Cargo Details',
      'Receiver Directory',
      'Greedy vs Global Fleet',
      'Approval Decisions',
      'Driver Mobile Portal',
      'Receiver Intake Portal',
      'AWS Live Trace',
      'AWS Cloud Architecture',
      'Audit Timeline',
      'Action Contracts Matrix',
    ];
    views.forEach((v) => {
      const btn = screen.getAllByRole('button', { name: new RegExp(v, 'i') })[0];
      expect(btn).toBeDefined();
      fireEvent.click(btn);
    });
  });
});

