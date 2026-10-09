import React from 'react';
import { RefreshCwIcon, AlertTriangleIcon, WifiOffIcon } from './Icons';

interface ReliabilityBannerProps {
  isStale?: boolean;
  isOffline?: boolean;
  lastUpdated?: string;
  onRefresh?: () => void;
  onReconnect?: () => void;
}

export const ReliabilityBanner: React.FC<ReliabilityBannerProps> = ({
  isStale,
  isOffline,
  lastUpdated,
  onRefresh,
  onReconnect,
}) => {
  if (!isStale && !isOffline) return null;

  return (
    <aside
      aria-label="System Connectivity and Data Freshness Notice"
      style={{
        marginBottom: '16px',
        padding: '12px 16px',
        borderRadius: 'var(--radius-md)',
        background: isOffline ? 'var(--status-offline-bg)' : 'var(--status-stale-bg)',
        border: `1px solid ${isOffline ? 'var(--status-offline-border)' : 'var(--status-stale-border)'}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '12px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        {isOffline ? <WifiOffIcon size={20} /> : <AlertTriangleIcon size={20} />}
        <div>
          <strong style={{ color: isOffline ? 'var(--text-primary)' : 'var(--status-stale)' }}>
            {isOffline ? 'OFFLINE / DISCONNECTED STATE' : 'TELEMETRY DATA STALE'}
          </strong>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            {isOffline
              ? 'Network connection interrupted. Consequential dispatch and approval actions are locked for safety.'
              : `Cached data exceeds the 15-minute freshness threshold. Last synchronized: ${lastUpdated || 'Unknown'}.`}
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '8px' }}>
        {isOffline && onReconnect && (
          <button className="btn btn-secondary" onClick={onReconnect} style={{ padding: '6px 12px' }}>
            Attempt Reconnect
          </button>
        )}
        {isStale && onRefresh && (
          <button className="btn btn-secondary" onClick={onRefresh} style={{ padding: '6px 12px' }}>
            <RefreshCwIcon size={16} />
            Refresh Telemetry
          </button>
        )}
      </div>
    </aside>
  );
};

export const LoadingState: React.FC<{ message?: string }> = ({ message = 'Loading operational telemetry...' }) => (
  <div
    style={{
      padding: '48px',
      textAlign: 'center',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: '16px',
    }}
    role="status"
    aria-live="polite"
  >
    <div
      style={{
        width: '40px',
        height: '40px',
        border: '3px solid var(--border-strong)',
        borderTopColor: 'var(--accent-cyan)',
        borderRadius: '50%',
        animation: 'spin 1s linear infinite',
      }}
    />
    <span style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>{message}</span>
    <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
  </div>
);

export const ErrorState: React.FC<{
  title?: string;
  message: string;
  onRetry?: () => void;
}> = ({ title = 'Failed to Load Operational Data', message, onRetry }) => (
  <div
    className="card"
    style={{
      borderLeft: '4px solid var(--status-critical-border)',
      padding: '24px',
      margin: '16px 0',
    }}
    role="alert"
  >
    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--status-critical)' }}>
      <AlertTriangleIcon size={24} />
      <h3 style={{ fontSize: '1.1rem', margin: 0 }}>{title}</h3>
    </div>
    <p style={{ margin: '12px 0', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{message}</p>
    {onRetry && (
      <button className="btn btn-primary" onClick={onRetry} style={{ marginTop: '8px' }}>
        <RefreshCwIcon size={16} />
        Retry Operation
      </button>
    )}
  </div>
);

export const EmptyState: React.FC<{
  title: string;
  message: string;
  actionText?: string;
  onAction?: () => void;
}> = ({ title, message, actionText, onAction }) => (
  <div
    className="card"
    style={{
      padding: '40px 24px',
      textAlign: 'center',
      border: '1px dashed var(--border-strong)',
    }}
  >
    <h3 style={{ fontSize: '1.1rem', color: 'var(--text-primary)', marginBottom: '8px' }}>{title}</h3>
    <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '480px', margin: '0 auto 16px auto' }}>
      {message}
    </p>
    {actionText && onAction && (
      <button className="btn btn-secondary" onClick={onAction}>
        {actionText}
      </button>
    )}
  </div>
);
