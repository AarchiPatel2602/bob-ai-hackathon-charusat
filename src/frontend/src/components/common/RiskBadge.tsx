import React from 'react';

interface RiskBadgeProps {
  score: number;
  level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | string;
  showScore?: boolean;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ score, level, showScore = true }) => {
  const normLevel = (level || 'LOW').toUpperCase();

  let colorClasses = 'bg-emerald-950/70 text-emerald-400 border-emerald-800/80';
  let dotColor = 'bg-emerald-500';

  if (normLevel === 'CRITICAL' || score >= 81) {
    colorClasses = 'bg-rose-950/80 text-rose-300 border-rose-700/90 shadow-sm shadow-rose-900/30';
    dotColor = 'bg-rose-500 animate-pulse';
  } else if (normLevel === 'HIGH' || score >= 61) {
    colorClasses = 'bg-orange-950/80 text-orange-300 border-orange-700/80';
    dotColor = 'bg-orange-500';
  } else if (normLevel === 'MEDIUM' || score >= 31) {
    colorClasses = 'bg-amber-950/70 text-amber-300 border-amber-700/70';
    dotColor = 'bg-amber-500';
  }

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold tracking-wide border ${colorClasses}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`} />
      {showScore && <span className="font-mono font-bold">{score}/100</span>}
      <span>{normLevel}</span>
    </span>
  );
};
