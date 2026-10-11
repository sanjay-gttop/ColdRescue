import React from 'react';

export type ActiveTab =
  | 'story'
  | 'dashboard'
  | 'live-trace'
  | 'incidents'
  | 'receivers'
  | 'allocation'
  | 'approvals'
  | 'driver'
  | 'receiver-portal'
  | 'audit'
  | 'architecture'
  | 'policy-block'
  | 'action-matrix';

interface NavigationProps {
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  pendingApprovalsCount: number;
  criticalIncidentsCount: number;
}

export const Navigation: React.FC<NavigationProps> = ({
  activeTab,
  onTabChange,
  pendingApprovalsCount,
  criticalIncidentsCount,
}) => {
  const tabs: Array<{ id: ActiveTab; label: string; badge?: number | string; badgeType?: 'critical' | 'pending' | 'story' }> = [
    { id: 'story', label: '✨ 3D Rescue Experience', badge: 'LIVE', badgeType: 'story' },
    { id: 'dashboard', label: 'Operator Dashboard' },
    { id: 'live-trace', label: 'AWS Live Trace' },
    { id: 'incidents', label: 'Incident & Cargo Details', badge: criticalIncidentsCount, badgeType: 'critical' },
    { id: 'receivers', label: 'Receiver Directory' },
    { id: 'allocation', label: 'Greedy vs Global Allocation' },
    { id: 'approvals', label: 'Approval Decisions', badge: pendingApprovalsCount, badgeType: 'pending' },
    { id: 'driver', label: 'Driver Mobile Portal' },
    { id: 'receiver-portal', label: 'Receiver Intake Portal' },
    { id: 'audit', label: 'Audit Timeline' },
    { id: 'architecture', label: 'AWS Architecture' },
    { id: 'policy-block', label: 'Policy Rules & Safety Block' },
    { id: 'action-matrix', label: 'Action Contracts Matrix' },
  ];

  return (
    <nav
      aria-label="Operations Navigation"
      style={{
        backgroundColor: 'var(--bg-card)',
        borderBottom: '1px solid var(--border-subtle)',
        overflowX: 'auto',
        whiteSpace: 'nowrap',
      }}
    >
      <div
        className="container"
        style={{
          display: 'flex',
          gap: '4px',
          padding: '6px 16px',
        }}
      >
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className="btn"
              style={{
                minHeight: '38px',
                padding: '6px 12px',
                fontSize: '0.85rem',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: isActive ? 'var(--bg-elevated)' : 'transparent',
                color: isActive ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                borderBottom: isActive ? '2px solid var(--accent-cyan)' : '2px solid transparent',
                fontWeight: isActive ? 700 : 500,
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
              }}
              aria-current={isActive ? 'page' : undefined}
            >
              <span>{tab.label}</span>
              {tab.badge !== undefined && (
                <span
                  style={{
                    fontSize: '0.7rem',
                    padding: '1px 6px',
                    borderRadius: 'var(--radius-full)',
                    backgroundColor:
                      tab.badgeType === 'story'
                        ? '#0C2B3A'
                        : tab.badgeType === 'critical'
                        ? 'var(--status-critical)'
                        : 'var(--accent-blue)',
                    color: tab.badgeType === 'story' ? '#19D3C5' : '#ffffff',
                    fontWeight: 700,
                  }}
                >
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
};
