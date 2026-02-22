'use client';

import { Position } from '@/types/pdac';

interface PositionPanelProps {
  positions: Position[];
}

export default function PositionPanel({ positions }: PositionPanelProps) {
  const openPositions = positions.filter((p) => !p.closedAt);

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <h3 className="font-bold mb-4">Positions</h3>
      
      {openPositions.length === 0 ? (
        <div className="text-gray-400 text-sm">No open positions</div>
      ) : (
        <div className="space-y-2">
          {openPositions.map((position) => (
            <div
              key={position.id}
              className={`p-2 rounded ${
                position.side === 'BUY' ? 'bg-green-900' : 'bg-red-900'
              }`}
            >
              <div className="flex justify-between">
                <span className="font-bold">{position.symbol}</span>
                <span>{position.side}</span>
              </div>
              <div className="text-sm text-gray-300">
                Qty: {position.quantity}
              </div>
              <div className="text-sm text-gray-300">
                Entry: ${position.entryPrice?.toFixed(2)}
              </div>
              <div className="text-sm text-gray-300">
                PnL: ${position.unrealizedPnl?.toFixed(2) || '0.00'}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
