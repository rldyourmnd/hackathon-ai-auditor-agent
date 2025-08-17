import React from 'react';

export type RiskLevel = 'low' | 'medium' | 'high';

export function RiskBadge({ level }: { level: RiskLevel }) {
  const color = level === 'high' ? 'red' : level === 'medium' ? 'orange' : 'green';
  return (
    <div style={{ padding: 6, borderRadius: 6, background: '#fff' }}>
      <span style={{ color }}>{level.toUpperCase()}</span>
    </div>
  );
}



