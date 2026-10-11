import React, { useState } from 'react';
import { DataSourceMode } from '../../types';
import { RefreshCwIcon, WifiIcon, WifiOffIcon } from '../common/Icons';

interface HeaderProps {
  dataSource: DataSourceMode;
  isOffline: boolean;
  isStale: boolean;
  onRefresh: () => void;
  onToggleOffline: () => void;
  onToggleStale: () => void;
  onToggleDataSource: () => void;
  onToggleReplay?: () => void;
  isReplayMode?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  dataSource,
  isOffline,
  isStale,
  onRefresh,
  onToggleOffline,
  onToggleStale,
  onToggleDataSource,
  onToggleReplay,
  isReplayMode = false,
}) => {
  const [isSimMenuOpen, setIsSimMenuOpen] = useState(false);

  return (
    <header
      style={{
        backgroundColor: 'rgba(7, 9, 14, 0.95)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        borderBottom: '1px solid var(--border-subtle)',
        position: 'sticky',
        top: 0,
        zIndex: 40,
        height: '56px',
        display: 'flex',
        alignItems: 'center',
      }}
    >
      <div
        className="container"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '12px',
          padding: '0 20px',
        }}
      >
        {/* Left: Mobile Title / Skip Link */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <a
            href="#main-content-target"
            className="skip-link"
            style={{
              position: 'absolute',
              top: '-40px',
              left: '20px',
              backgroundColor: '#38bdf8',
              color: '#07090e',
              padding: '6px 12px',
              borderRadius: '4px',
              fontWeight: 700,
              fontSize: '0.8rem',
              zIndex: 100,
              transition: 'top 0.2s',
            }}
            onFocus={(e) => (e.currentTarget.style.top = '10px')}
            onBlur={(e) => (e.currentTarget.style.top = '-40px')}
          >
            Skip to content
          </a>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '1.05rem', fontWeight: 800, letterSpacing: '-0.02em', color: '#f8fafc' }}>
              ColdRescue
            </span>
            <span
              style={{
                fontSize: '0.65rem',
                padding: '2px 6px',
                borderRadius: '4px',
                backgroundColor: 'rgba(56, 189, 248, 0.1)',
                border: '1px solid rgba(56, 189, 248, 0.3)',
                color: '#38bdf8',
                fontWeight: 700,
              }}
            >
              V7 RESILIENCE
            </span>
          </div>
        </div>

        {/* Right: Controls & Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          {/* Data Mode Pill */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 10px',
              borderRadius: '999px',
              backgroundColor: isReplayMode ? '#3b0764' : 'rgba(59, 130, 246, 0.12)',
              border: isReplayMode ? '1px solid #a855f7' : '1px solid var(--border-subtle)',
              fontSize: '0.74rem',
            }}
          >
            <span
              style={{
                width: '6px',
                height: '6px',
                borderRadius: '50%',
                backgroundColor: isReplayMode ? '#d8b4fe' : '#60a5fa',
              }}
            />
            <span style={{ fontWeight: 600, color: isReplayMode ? '#f5d0fe' : 'var(--text-primary)' }}>
              {isReplayMode ? 'REPLAY (Recorded Real Run)' : `DATA: ${dataSource.toUpperCase()} (SYNTHETIC)`}
            </span>
            <button
              onClick={onToggleDataSource}
              style={{
                background: 'none',
                border: 'none',
                fontSize: '0.68rem',
                color: '#38bdf8',
                cursor: 'pointer',
                textDecoration: 'underline',
                padding: '0 2px',
              }}
              title="Toggle demo mode"
            >
              Toggle
            </button>
          </div>

          {/* ONLINE Status with Moving Border */}
          <div className="moving-border-pill">
            <div className="moving-border-inner" style={{ padding: '3px 10px', fontSize: '0.72rem' }}>
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#10b981' }} />
              <span>ONLINE</span>
            </div>
          </div>

          {/* Simulation Dropdown Menu */}
          <div style={{ position: 'relative' }}>
            <button
              onClick={() => setIsSimMenuOpen(!isSimMenuOpen)}
              className="btn btn-secondary"
              style={{ minHeight: '32px', padding: '4px 10px', fontSize: '0.75rem', borderRadius: '6px' }}
              aria-expanded={isSimMenuOpen}
              aria-label="Simulation state menu"
            >
              Simulation ▾
            </button>

            {isSimMenuOpen && (
              <div
                style={{
                  position: 'absolute',
                  right: 0,
                  top: '38px',
                  backgroundColor: '#111827',
                  border: '1px solid var(--border-strong)',
                  borderRadius: '8px',
                  boxShadow: '0 10px 25px rgba(0,0,0,0.6)',
                  padding: '8px',
                  minWidth: '180px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px',
                  zIndex: 60,
                }}
              >
                <button
                  onClick={() => {
                    onRefresh();
                    setIsSimMenuOpen(false);
                  }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '8px',
                    fontSize: '0.78rem',
                    color: 'var(--text-primary)',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    textAlign: 'left',
                  }}
                >
                  <RefreshCwIcon size={14} /> Refresh Telemetry
                </button>

                <button
                  onClick={() => {
                    onToggleOffline();
                    setIsSimMenuOpen(false);
                  }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '8px',
                    fontSize: '0.78rem',
                    color: isOffline ? '#f43f5e' : 'var(--text-secondary)',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    textAlign: 'left',
                  }}
                >
                  {isOffline ? <WifiOffIcon size={14} /> : <WifiIcon size={14} />}
                  {isOffline ? 'Disable Sim Offline' : 'Simulate Offline'}
                </button>

                <button
                  onClick={() => {
                    onToggleStale();
                    setIsSimMenuOpen(false);
                  }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '8px',
                    fontSize: '0.78rem',
                    color: isStale ? '#f59e0b' : 'var(--text-secondary)',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    textAlign: 'left',
                  }}
                >
                  ⏱️ {isStale ? 'Clear Sim Stale' : 'Simulate Stale Data'}
                </button>

                {onToggleReplay && (
                  <button
                    onClick={() => {
                      onToggleReplay();
                      setIsSimMenuOpen(false);
                    }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '8px',
                      fontSize: '0.78rem',
                      color: isReplayMode ? '#c084fc' : '#a855f7',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      textAlign: 'left',
                      borderTop: '1px solid var(--border-subtle)',
                    }}
                  >
                    📼 {isReplayMode ? 'Exit Replay Mode' : 'Replay Recorded Run'}
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
