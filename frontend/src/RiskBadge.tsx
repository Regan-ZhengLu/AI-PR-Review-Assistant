import type { RiskLevel } from './types';

const labels: Record<RiskLevel, string> = {
  high: '高风险',
  medium: '中风险',
  low: '低风险',
};

interface RiskBadgeProps {
  level: RiskLevel;
}

export function RiskBadge({ level }: RiskBadgeProps) {
  return <span className={`risk-badge risk-badge--${level}`}>{labels[level] ?? level}</span>;
}
