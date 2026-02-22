'use client';

import { useState } from 'react';
import Chart from './Chart';
import { ChartConfig, MatchState } from '@/types/pdac';

interface MultiChartManagerProps {
  focusedChart: number;
  onChartFocus: (index: number) => void;
  matchState: MatchState | null;
}

export default function MultiChartManager({
  focusedChart,
  onChartFocus,
  matchState,
}: MultiChartManagerProps) {
  // State according to PDaC spec
  const [charts] = useState<ChartConfig[]>([
    { symbol: 'BTC/USD', timeframe: 'M1' },
    { symbol: 'ETH/USD', timeframe: 'M1' },
    { symbol: 'EUR/USD', timeframe: 'M1' },
    { symbol: 'GBP/USD', timeframe: 'M1' },
  ]);

  return (
    <div className="grid grid-cols-2 gap-4 h-full">
      {charts.map((chart, index) => (
        <div
          key={index}
          className={`rts-chart ${focusedChart === index ? 'focused' : ''}`}
          onClick={() => onChartFocus(index)}
        >
          <div className="flex justify-between items-center mb-2">
            <div>
              <div className="font-bold">{chart.symbol}</div>
              <div className="text-sm text-gray-400">Press {index + 1} to focus</div>
            </div>
            {focusedChart === index && (
              <div className="px-2 py-1 bg-green-500 rounded text-xs">FOCUSED</div>
            )}
          </div>
          <Chart
            symbol={chart.symbol}
            timeframe={chart.timeframe}
            isFocused={focusedChart === index}
            marketData={matchState?.market}
          />
        </div>
      ))}
    </div>
  );
}
