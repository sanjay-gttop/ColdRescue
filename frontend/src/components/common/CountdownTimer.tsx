import React, { useState, useEffect } from 'react';
import { ClockIcon, AlertTriangleIcon } from './Icons';

interface CountdownTimerProps {
  deadlineIso: string | null;
  estimateSource?: string;
  confidence?: 'high' | 'medium' | 'approximate' | 'unknown';
}

export const CountdownTimer: React.FC<CountdownTimerProps> = ({
  deadlineIso,
  estimateSource = 'Arrhenius Decay Model v0.4',
  confidence = 'approximate',
}) => {
  const [timeLeftMs, setTimeLeftMs] = useState<number | null>(() => {
    if (!deadlineIso) return null;
    return new Date(deadlineIso).getTime() - Date.now();
  });

  useEffect(() => {
    if (!deadlineIso) {
      setTimeLeftMs(null);
      return;
    }

    const timer = setInterval(() => {
      const remaining = new Date(deadlineIso).getTime() - Date.now();
      setTimeLeftMs(remaining);
    }, 1000);

    return () => clearInterval(timer);
  }, [deadlineIso]);

  if (!deadlineIso || timeLeftMs === null) {
    return (
      <div className="card" style={{ borderLeft: '4px solid var(--status-unknown-border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--status-unknown)' }}>
          <AlertTriangleIcon size={18} />
          <strong>Spoilage Countdown: UNKNOWN / DATA MISSING</strong>
        </div>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
          Missing calibrated telemetry or thermal model coefficients. Do not assume cargo is safe.
        </p>
      </div>
    );
  }

  const isExpired = timeLeftMs <= 0;
  const absSeconds = Math.floor(Math.abs(timeLeftMs) / 1000);
  const hours = Math.floor(absSeconds / 3600);
  const minutes = Math.floor((absSeconds % 3600) / 60);
  const seconds = absSeconds % 60;

  const formattedTime = `${hours.toString().padStart(2, '0')}:${minutes
    .toString()
    .padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

  const isCritical = !isExpired && timeLeftMs < 60 * 60 * 1000; // < 1 hour
  const borderCol = isExpired
    ? 'var(--status-critical-border)'
    : isCritical
    ? 'var(--status-critical-border)'
    : 'var(--status-warning-border)';

  return (
    <div className="card" style={{ borderLeft: `4px solid ${borderCol}`, background: 'var(--bg-card)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ClockIcon size={20} className={isCritical || isExpired ? 'pulse-icon' : ''} />
          <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
            REMAINING THERMAL SAFE TIME
          </span>
        </div>
        <span
          className={`badge ${
            isExpired ? 'badge-critical' : isCritical ? 'badge-critical' : 'badge-warning'
          }`}
        >
          {isExpired ? 'EXPIRED' : isCritical ? 'CRITICAL MARGIN' : 'MONITORING'}
        </span>
      </div>

      <div style={{ margin: '10px 0' }}>
        <span
          style={{
            fontFamily: 'monospace',
            fontSize: '2rem',
            fontWeight: 700,
            color: isExpired ? 'var(--status-critical)' : 'var(--text-primary)',
          }}
          aria-live="polite"
        >
          {isExpired ? `+${formattedTime} OVERDUE` : formattedTime}
        </span>
      </div>

      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', borderTop: '1px solid var(--border-subtle)', paddingTop: '6px' }}>
        <span>Model Source: <strong>{estimateSource}</strong> (Confidence: {confidence})</span>
        <div style={{ fontStyle: 'italic', marginTop: '2px', color: '#94a3b8' }}>
          ⚠️ Estimated projection based on ambient gradient. Does not guarantee biological stability without active sensor validation.
        </div>
      </div>
    </div>
  );
};
