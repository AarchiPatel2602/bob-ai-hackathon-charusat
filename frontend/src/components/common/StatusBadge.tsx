import React from 'react';

interface StatusBadgeProps {
  status: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const norm = (status || 'UNKNOWN').toUpperCase();

  let style = 'bg-slate-800 text-slate-300 border-slate-700';

  if (norm === 'IN_TRANSIT') {
    style = 'bg-blue-950/70 text-blue-300 border-blue-800/80';
  } else if (norm === 'DELIVERED') {
    style = 'bg-emerald-950/70 text-emerald-300 border-emerald-800/80';
  } else if (norm === 'DELAYED') {
    style = 'bg-amber-950/70 text-amber-300 border-amber-800/80';
  } else if (norm === 'AT_RISK') {
    style = 'bg-orange-950/80 text-orange-300 border-orange-800/80';
  } else if (norm === 'CRITICAL') {
    style = 'bg-rose-950/80 text-rose-300 border-rose-800/80 font-bold';
  } else if (norm === 'PLANNED') {
    style = 'bg-slate-800 text-slate-300 border-slate-700';
  } else if (norm === 'AVAILABLE') {
    style = 'bg-emerald-950/70 text-emerald-300 border-emerald-800/80';
  } else if (norm === 'IDLE') {
    style = 'bg-amber-950/70 text-amber-300 border-amber-800/80';
  } else if (norm === 'MAINTENANCE') {
    style = 'bg-purple-950/70 text-purple-300 border-purple-800/80';
  } else if (norm === 'ACTIVE') {
    style = 'bg-rose-950/80 text-rose-300 border-rose-800/80';
  } else if (norm === 'RESOLVED') {
    style = 'bg-slate-800 text-slate-400 border-slate-700';
  }

  const label = norm.replace('_', ' ');

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${style}`}>
      {label}
    </span>
  );
};
