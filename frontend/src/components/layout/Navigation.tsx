import React from 'react';

export type ActiveTab =
  | 'dashboard'
  | 'incidents'
  | 'receivers'
  | 'allocation'
  | 'approvals'
  | 'driver'
  | 'receiver-portal'
  | 'audit'
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
  const tabs: Array<{ id: ActiveTab; label: string; badge?: number; badgeType?: 'critical' | 'pending' }> = [
    { id: 'dashboard', label: 'Operator Dashboard' },
    { id: 'incidents', label: 'Incident & Cargo Details', badge: criticalIncidentsCount, badgeType: 'critical' },
    { id: 'receivers', label: 'Receiver Directory' },
    { id: 'allocation', label: 'Greedy vs Global Allocation' },
    { id: 'approvals', label: 'Approval Decisions', badge: pendingApprovalsCount, badgeType: 'pending' },
    { id: 'driver', label: 'Driver Mobile Portal' },
    { id: 'receiver-portal', label: 'Receiver Intake Portal' },
    { id: 'audit', label: 'Audit Timeline' },
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
              {typeof tab.badge === 'number' && tab.badge > 0 && (
                <span
                  style={{
                    fontSize: '0.7rem',
                    padding: '1px 6px',
                    borderRadius: 'var(--radius-full)',
                    backgroundColor: tab.badgeType === 'critical' ? 'var(--status-critical)' : 'var(--accent-blue)',
                    color: '#ffffff',
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
