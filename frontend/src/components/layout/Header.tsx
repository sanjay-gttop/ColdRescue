import React from 'react';
import { DataSourceMode } from '../../types';
import { ShieldAlertIcon, RefreshCwIcon, WifiIcon, WifiOffIcon } from '../common/Icons';

interface HeaderProps {
  dataSource: DataSourceMode;
  isOffline: boolean;
  isStale: boolean;
  onRefresh: () => void;
  onToggleOffline: () => void;
  onToggleStale: () => void;
  onToggleDataSource: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  dataSource,
  isOffline,
  isStale,
  onRefresh,
  onToggleOffline,
  onToggleStale,
  onToggleDataSource,
}) => {
  return (
    <header
      style={{
        backgroundColor: 'var(--bg-secondary)',
        borderBottom: '1px solid var(--border-strong)',
        padding: '12px 20px',
        position: 'sticky',
        top: 0,
        zIndex: 40,
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '36px',
              height: '36px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--status-critical-bg)',
              color: 'var(--status-critical)',
              border: '1px solid var(--status-critical-border)',
            }}
          >
            <ShieldAlertIcon size={22} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h1 style={{ fontSize: '1.2rem', fontWeight: 800, letterSpacing: '-0.02em', margin: 0 }}>
                ColdRescue
              </h1>
              <span
                style={{
                  fontSize: '0.7rem',
                  padding: '2px 6px',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: 'var(--bg-elevated)',
                  border: '1px solid var(--border-strong)',
                  color: 'var(--accent-cyan)',
                  fontWeight: 700,
                }}
              >
                M1 PROTOTYPE
              </span>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Emergency Cold Chain Power Failure Decision Support
            </p>
          </div>
        </div>

        {/* Operational Telemetry & Simulation Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          {/* Explicit Data Source Labeling */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 10px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: dataSource === 'demo' ? 'rgba(59, 130, 246, 0.15)' : 'rgba(16, 185, 129, 0.15)',
              border: `1px solid ${dataSource === 'demo' ? 'var(--status-pending-border)' : 'var(--status-safe-border)'}`,
              fontSize: '0.75rem',
            }}
          >
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: dataSource === 'demo' ? '#60a5fa' : '#34d399',
              }}
            />
            <span style={{ fontWeight: 600 }}>
              {dataSource === 'demo' ? 'DATA: LOCAL DEMO (Synthetic Fixtures)' : 'DATA: LIVE AWS (Milestone 2)'}
            </span>
            <button
              onClick={onToggleDataSource}
              style={{
                marginLeft: '6px',
                fontSize: '0.7rem',
                textDecoration: 'underline',
                color: 'var(--text-secondary)',
              }}
              title="Toggle DataSource Mode"
            >
              Toggle
            </button>
          </div>

          {/* Connection state */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '0.75rem',
              color: isOffline ? 'var(--status-offline)' : 'var(--status-safe)',
            }}
          >
            {isOffline ? <WifiOffIcon size={16} /> : <WifiIcon size={16} />}
            <span style={{ fontWeight: 600 }}>{isOffline ? 'OFFLINE' : 'ONLINE'}</span>
          </div>

          {/* Simulation Tools for Journeys E & F */}
          <div style={{ display: 'flex', gap: '6px' }}>
            <button
              className="btn btn-secondary"
              onClick={onRefresh}
              title="Refresh telemetry"
              style={{ minHeight: '34px', padding: '4px 10px', fontSize: '0.75rem' }}
            >
              <RefreshCwIcon size={14} />
              Refresh
            </button>
            <button
              className="btn btn-secondary"
              onClick={onToggleOffline}
              style={{
                minHeight: '34px',
                padding: '4px 8px',
                fontSize: '0.7rem',
                borderColor: isOffline ? 'var(--status-critical)' : 'var(--border-strong)',
              }}
            >
              {isOffline ? 'Restore Net' : 'Sim Offline'}
            </button>
            <button
              className="btn btn-secondary"
              onClick={onToggleStale}
              style={{
                minHeight: '34px',
                padding: '4px 8px',
                fontSize: '0.7rem',
                borderColor: isStale ? 'var(--status-warning)' : 'var(--border-strong)',
              }}
            >
              {isStale ? 'Fresh Data' : 'Sim Stale'}
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
