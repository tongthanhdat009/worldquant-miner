'use client';

import { Stats } from '@/types/pdac';

interface StatsPanelProps {
  stats: Stats;
}

export default function StatsPanel({ stats }: StatsPanelProps) {
  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <h3 className="font-bold mb-4">Stats</h3>
      
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-400">Trades:</span>
          <span>{stats.trades || 0}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">APM:</span>
          <span>{stats.apm?.toFixed(1) || '0.0'}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Accuracy:</span>
          <span>{(stats.accuracy * 100)?.toFixed(1) || '0.0'}%</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Wins:</span>
          <span>{stats.wins || 0}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Losses:</span>
          <span>{stats.losses || 0}</span>
        </div>
      </div>
    </div>
  );
}
