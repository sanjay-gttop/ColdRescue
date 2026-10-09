import React from 'react';
import { StatusLevel } from '../../types';
import {
  ShieldAlertIcon,
  AlertTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  WifiOffIcon,
} from './Icons';

interface StatusBadgeProps {
  status: StatusLevel | string;
  label?: string;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, label, className = '' }) => {
  const normStatus = (status || '').toLowerCase();

  const getIcon = () => {
    switch (normStatus) {
      case 'critical':
      case 'failed':
        return <ShieldAlertIcon size={14} />;
      case 'warning':
      case 'degraded':
        return <AlertTriangleIcon size={14} />;
      case 'safe':
      case 'operational':
      case 'available':
      case 'completed':
        return <CheckCircleIcon size={14} />;
      case 'blocked':
      case 'offline':
        return <XCircleIcon size={14} />;
      case 'pending':
      case 'evaluating':
      case 'en_route':
        return <ClockIcon size={14} />;
      case 'stale':
        return <AlertTriangleIcon size={14} />;
      case 'unknown':
      default:
        return <WifiOffIcon size={14} />;
    }
  };

  const getBadgeClass = () => {
    if (normStatus === 'failed' || normStatus === 'critical') return 'badge-critical';
    if (normStatus === 'degraded' || normStatus === 'warning') return 'badge-warning';
    if (
      normStatus === 'operational' ||
      normStatus === 'available' ||
      normStatus === 'completed' ||
      normStatus === 'safe'
    )
      return 'badge-safe';
    if (normStatus === 'blocked' || normStatus === 'offline') return 'badge-blocked';
    if (normStatus === 'pending' || normStatus === 'evaluating' || normStatus === 'en_route')
      return 'badge-pending';
    if (normStatus === 'stale') return 'badge-stale';
    return 'badge-unknown';
  };

  const displayLabel = label || status.replace('_', ' ').toUpperCase();

  return (
    <span className={`badge ${getBadgeClass()} ${className}`} role="status" aria-label={`Status: ${displayLabel}`}>
      {getIcon()}
      <span>{displayLabel}</span>
    </span>
  );
};
