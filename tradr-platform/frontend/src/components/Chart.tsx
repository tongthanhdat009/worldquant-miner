'use client';

import { useEffect, useRef } from 'react';
import { MarketData } from '@/types/pdac';

interface ChartProps {
  symbol: string;
  timeframe: string;
  isFocused: boolean;
  marketData: MarketData | null;
}

export default function Chart({ symbol, timeframe, isFocused, marketData }: ChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Simple chart rendering
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw grid
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 1;
    for (let i = 0; i < 5; i++) {
      const y = (canvas.height / 5) * i;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width, y);
      ctx.stroke();
    }

    // Draw price line (mock data)
    if (marketData?.currentPrice) {
      const price = marketData.currentPrice;
      const basePrice = price * 0.9; // Mock base
      const range = price * 0.2;
      
      ctx.strokeStyle = isFocused ? '#10b981' : '#3b82f6';
      ctx.lineWidth = 2;
      ctx.beginPath();
      
      for (let x = 0; x < canvas.width; x += 2) {
        const y = canvas.height - ((price - basePrice) / range) * canvas.height;
        if (x === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();

      // Draw current price
      ctx.fillStyle = isFocused ? '#10b981' : '#3b82f6';
      ctx.font = '12px monospace';
      ctx.fillText(`$${price.toFixed(2)}`, 10, 20);
    }
  }, [marketData, isFocused]);

  return (
    <div className="relative w-full h-full">
      <canvas
        ref={canvasRef}
        width={400}
        height={300}
        className="w-full h-full"
      />
      <div className="absolute bottom-2 left-2 text-xs text-gray-500">
        {timeframe}
      </div>
    </div>
  );
}
