import React from 'react';

export type ActiveTab =
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
  const tabs: Array<{ id: ActiveTab; label: string; badge?: number; badgeType?: 'critical' | 'pending' }> = [
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
        backgroundColor: 'rgba(11, 15, 25, 0.92)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        borderBottom: '1px solid var(--border-subtle)',
        overflowX: 'auto',
        whiteSpace: 'nowrap',
      }}
    >
      <div
        className="container"
        style={{
          display: 'flex',
          gap: '6px',
          padding: '8px 24px',
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
                minHeight: '36px',
                padding: '6px 14px',
                fontSize: '0.84rem',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: isActive ? 'var(--bg-elevated)' : 'transparent',
                color: isActive ? '#ffffff' : 'var(--text-secondary)',
                border: isActive ? '1px solid var(--border-violet)' : '1px solid transparent',
                borderBottom: isActive ? '2px solid var(--accent-cyan)' : '2px solid transparent',
                boxShadow: isActive ? '0 0 16px -2px rgba(56, 189, 248, 0.2)' : 'none',
                fontWeight: isActive ? 700 : 500,
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                transition: 'all 0.15s ease',
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
