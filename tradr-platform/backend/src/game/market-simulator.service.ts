import { Injectable } from '@nestjs/common';

interface MarketTick {
  timestamp: Date;
  price: number;
  volume: number;
  bid: number;
  ask: number;
}

@Injectable()
export class MarketSimulatorService {
  async createMarket(symbol: string, durationMinutes: number) {
    const ticks: MarketTick[] = [];
    const startPrice = this.getInitialPrice(symbol);
    const startTime = new Date();

    // According to PDaC spec: random_walk_with_trend
    // Parameters: volatility: 0.02, trend: 0.001, spread: 0.0001
    const volatility = 0.02;
    const trend = 0.001; // Slight upward bias
    const spread = 0.0001; // 0.01% spread
    const updateFrequency = 10; // 10 updates per second

    // Generate market ticks (10 ticks per second according to PDaC spec)
    const totalTicks = durationMinutes * 60 * updateFrequency;
    
    let currentPrice = startPrice;
    for (let i = 0; i < totalTicks; i++) {
      // Random walk with trend and volatility
      const randomChange = (Math.random() - 0.5) * 2 * volatility;
      const trendChange = trend;
      const change = randomChange + trendChange;
      currentPrice = currentPrice * (1 + change);
      
      const spreadAmount = currentPrice * spread;
      const bid = currentPrice - spreadAmount / 2;
      const ask = currentPrice + spreadAmount / 2;
      
      ticks.push({
        timestamp: new Date(startTime.getTime() + (i / updateFrequency) * 1000),
        price: currentPrice,
        volume: Math.random() * 1000,
        bid,
        ask,
      });
    }

    return {
      symbol,
      startPrice,
      currentPrice,
      ticks,
      duration: durationMinutes,
    };
  }

  private getInitialPrice(symbol: string): number {
    // Mock initial prices for different symbols
    const prices: Record<string, number> = {
      'BTC/USD': 45000,
      'ETH/USD': 2500,
      'EUR/USD': 1.08,
      'GBP/USD': 1.27,
      'USD/JPY': 150.0,
    };
    
    return prices[symbol] || 100;
  }

  getCurrentPrice(marketData: any, elapsedSeconds: number): number {
    if (!marketData?.ticks) {
      return marketData?.startPrice || 100;
    }

    const tickIndex = Math.floor(elapsedSeconds);
    if (tickIndex >= marketData.ticks.length) {
      return marketData.ticks[marketData.ticks.length - 1].price;
    }

    return marketData.ticks[tickIndex].price;
  }
}
