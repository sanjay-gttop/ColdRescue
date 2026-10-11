import React from 'react';
import { ActiveTab } from './Navigation';
import {
  ShieldAlertIcon,
  LayersIcon,
  ActivityIcon,
  WarehouseIcon,
  CheckCircleIcon,
  TruckIcon,
  ClockIcon,
  SettingsIcon,
  AlertTriangleIcon,
} from '../common/Icons';

interface SidebarProps {
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  pendingApprovalsCount: number;
  criticalIncidentsCount: number;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

interface NavItem {
  id: ActiveTab;
  label: string;
  icon: React.ReactNode;
  badge?: number;
  badgeType?: 'critical' | 'pending';
}

interface NavGroup {
  groupTitle: string;
  items: NavItem[];
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onTabChange,
  pendingApprovalsCount,
  criticalIncidentsCount,
  isCollapsed,
  onToggleCollapse,
}) => {
  const groups: NavGroup[] = [
    {
      groupTitle: 'OPERATE',
      items: [
        {
          id: 'dashboard',
          label: 'Operator Dashboard',
          icon: <ActivityIcon size={18} />,
        },
        {
          id: 'incidents',
          label: 'Incident & Cargo Details',
          icon: <ShieldAlertIcon size={18} />,
          badge: criticalIncidentsCount,
          badgeType: 'critical',
        },
        {
          id: 'approvals',
          label: 'Approval Decisions',
          icon: <CheckCircleIcon size={18} />,
          badge: pendingApprovalsCount,
          badgeType: 'pending',
        },
      ],
    },
    {
      groupTitle: 'PROVE (AWS & MATH)',
      items: [
        {
          id: 'live-trace',
          label: 'AWS Live Trace',
          icon: <ActivityIcon size={18} />,
        },
        {
          id: 'allocation',
          label: 'Greedy vs Global Fleet',
          icon: <LayersIcon size={18} />,
        },
        {
          id: 'audit',
          label: 'Audit Timeline',
          icon: <ClockIcon size={18} />,
        },
        {
          id: 'architecture',
          label: 'AWS Cloud Architecture',
          icon: <SettingsIcon size={18} />,
        },
      ],
    },
    {
      groupTitle: 'PORTALS',
      items: [
        {
          id: 'receivers',
          label: 'Receiver Directory',
          icon: <WarehouseIcon size={18} />,
        },
        {
          id: 'driver',
          label: 'Driver Mobile Portal',
          icon: <TruckIcon size={18} />,
        },
        {
          id: 'receiver-portal',
          label: 'Receiver Intake Portal',
          icon: <WarehouseIcon size={18} />,
        },
        {
          id: 'action-matrix',
          label: 'Action Contracts Matrix',
          icon: <AlertTriangleIcon size={18} />,
        },
      ],
    },
  ];

  return (
    <aside
      className={`sidebar-container ${isCollapsed ? 'sidebar-collapsed' : ''}`}
      aria-label="Sidebar Navigation"
    >
      {/* Brand Header */}
      <div
        style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: isCollapsed ? 'center' : 'space-between',
        }}
      >
        {!isCollapsed && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '28px',
                height: '28px',
                borderRadius: '6px',
                backgroundColor: 'rgba(56, 189, 248, 0.15)',
                border: '1px solid #38bdf8',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#38bdf8',
              }}
            >
              ❄️
            </div>
            <div>
              <div style={{ fontWeight: 800, fontSize: '1rem', letterSpacing: '-0.02em', color: '#f8fafc' }}>
                ColdRescue
              </div>
              <div style={{ fontSize: '0.68rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Resilience Engine
              </div>
            </div>
          </div>
        )}
        <button
          onClick={onToggleCollapse}
          aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            padding: '4px',
            fontSize: '0.85rem',
          }}
          title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? '▶' : '◀'}
        </button>
      </div>

      {/* Nav List */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px 10px' }}>
        {groups.map((grp, gIdx) => (
          <div key={gIdx} style={{ marginBottom: '20px' }}>
            {!isCollapsed && (
              <div
                style={{
                  fontSize: '0.68rem',
                  fontWeight: 750,
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  color: '#64748b',
                  padding: '4px 12px 8px 12px',
                }}
              >
                {grp.groupTitle}
              </div>
            )}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {grp.items.map((item) => {
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => onTabChange(item.id)}
                    aria-current={isActive ? 'page' : undefined}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: isCollapsed ? 'center' : 'space-between',
                      width: '100%',
                      padding: isCollapsed ? '10px' : '9px 12px',
                      borderRadius: '8px',
                      border: isActive ? '1px solid rgba(56, 189, 248, 0.4)' : '1px solid transparent',
                      backgroundColor: isActive ? 'rgba(56, 189, 248, 0.12)' : 'transparent',
                      color: isActive ? '#38bdf8' : 'var(--text-secondary)',
                      cursor: 'pointer',
                      fontSize: '0.86rem',
                      fontWeight: isActive ? 700 : 500,
                      transition: 'all 0.15s ease',
                      textAlign: 'left',
                    }}
                    title={isCollapsed ? item.label : undefined}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{ color: isActive ? '#38bdf8' : 'var(--text-muted)' }}>{item.icon}</span>
                      {!isCollapsed && <span>{item.label}</span>}
                    </div>

                    {!isCollapsed && item.badge !== undefined && item.badge > 0 && (
                      <span
                        style={{
                          fontSize: '0.68rem',
                          fontWeight: 700,
                          padding: '1px 6px',
                          borderRadius: '999px',
                          backgroundColor:
                            item.badgeType === 'critical' ? 'var(--status-critical-bg)' : 'var(--status-pending-bg)',
                          color: item.badgeType === 'critical' ? 'var(--status-critical)' : '#38bdf8',
                          border:
                            item.badgeType === 'critical'
                              ? '1px solid var(--status-critical-border)'
                              : '1px solid var(--status-pending-border)',
                        }}
                      >
                        {item.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Footer Identity in Sidebar */}
      {!isCollapsed && (
        <div
          style={{
            padding: '14px 16px',
            borderTop: '1px solid var(--border-subtle)',
            fontSize: '0.72rem',
            color: '#64748b',
          }}
        >
          <div>AWS Region: ap-south-1</div>
          <div style={{ color: '#10b981', marginTop: '2px' }}>Zero Idle Cost Verified</div>
        </div>
      )}
    </aside>
  );
};
