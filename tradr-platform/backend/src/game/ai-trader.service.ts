import { Injectable } from '@nestjs/common';

export type AIDifficulty = 'easy' | 'medium' | 'hard';

interface AIDecision {
  action: 'buy' | 'sell' | 'hold' | 'close';
  quantity?: number;
  price?: number;
  confidence: number;
}

@Injectable()
export class AITraderService {
  async createAIOpponent(difficulty: AIDifficulty) {
    return {
      id: `ai_${Date.now()}`,
      difficulty,
      name: `AI Trader (${difficulty})`,
    };
  }

  async makeDecision(
    difficulty: AIDifficulty,
    marketData: any,
    portfolio: any,
    elapsedTime: number,
  ): Promise<AIDecision> {
    const currentPrice = marketData.currentPrice || marketData.startPrice;
    const trend = this.analyzeTrend(marketData);
    const volatility = this.calculateVolatility(marketData);

    let decision: AIDecision;

    switch (difficulty) {
      case 'easy':
        decision = this.easyAI(currentPrice, trend, portfolio);
        break;
      case 'medium':
        decision = this.mediumAI(currentPrice, trend, volatility, portfolio);
        break;
      case 'hard':
        decision = this.hardAI(currentPrice, trend, volatility, portfolio, elapsedTime);
        break;
    }

    return decision;
  }

  private analyzeTrend(marketData: any): 'up' | 'down' | 'sideways' {
    if (!marketData.ticks || marketData.ticks.length < 10) {
      return 'sideways';
    }

    const recent = marketData.ticks.slice(-10);
    const first = recent[0].price;
    const last = recent[recent.length - 1].price;
    const change = (last - first) / first;

    if (change > 0.01) return 'up';
    if (change < -0.01) return 'down';
    return 'sideways';
  }

  private calculateVolatility(marketData: any): number {
    if (!marketData.ticks || marketData.ticks.length < 10) {
      return 0.01;
    }

    const recent = marketData.ticks.slice(-10);
    const prices = recent.map((t) => t.price);
    const avg = prices.reduce((a, b) => a + b, 0) / prices.length;
    const variance =
      prices.reduce((sum, p) => sum + Math.pow(p - avg, 2), 0) / prices.length;
    return Math.sqrt(variance) / avg;
  }

  private easyAI(
    price: number,
    trend: string,
    portfolio: any,
  ): AIDecision {
    // According to PDaC spec: strategy: "trend_following", reactionTime: 2000ms, riskTolerance: 0.3
    // Simple trend following
    if (trend === 'up' && portfolio.cash > price * 0.1) {
      const riskAmount = portfolio.cash * 0.3; // riskTolerance: 0.3
      return {
        action: 'buy',
        quantity: riskAmount / price,
        confidence: 0.6,
      };
    }
    if (trend === 'down' && portfolio.positions?.length > 0) {
      return {
        action: 'close',
        confidence: 0.6,
      };
    }
    return { action: 'hold', confidence: 0.5 };
  }

  private mediumAI(
    price: number,
    trend: string,
    volatility: number,
    portfolio: any,
  ): AIDecision {
    // According to PDaC spec: strategy: "trend_following + mean_reversion", reactionTime: 1000ms, riskTolerance: 0.2
    // More sophisticated with volatility consideration
    if (trend === 'up' && volatility < 0.02 && portfolio.cash > price * 0.1) {
      const riskAmount = portfolio.cash * 0.2; // riskTolerance: 0.2
      return {
        action: 'buy',
        quantity: riskAmount / price,
        confidence: 0.7,
      };
    }
    if (trend === 'down' && portfolio.positions?.length > 0) {
      return {
        action: 'close',
        confidence: 0.7,
      };
    }
    return { action: 'hold', confidence: 0.6 };
  }

  private hardAI(
    price: number,
    trend: string,
    volatility: number,
    portfolio: any,
    elapsedTime: number,
  ): AIDecision {
    // According to PDaC spec: strategy: "trend_following + mean_reversion + momentum", 
    // reactionTime: 500ms, riskTolerance: 0.1, takeProfit: 0.05
    const riskTolerance = 0.1;
    const takeProfit = 0.05; // 5% profit target
    
    // Advanced AI with timing and risk management
    const riskLevel = Math.min(volatility * 10, 1);
    const timeFactor = elapsedTime / 3600; // Normalize to hours

    // Aggressive early game, conservative late game
    const aggression = Math.max(riskTolerance, 1 - timeFactor * 0.5);

    if (trend === 'up' && riskLevel < 0.5 && portfolio.cash > price * 0.1) {
      const riskAmount = portfolio.cash * aggression;
      return {
        action: 'buy',
        quantity: riskAmount / price,
        confidence: 0.8,
      };
    }

    if (trend === 'down' && portfolio.positions?.length > 0) {
      return {
        action: 'close',
        confidence: 0.8,
      };
    }

    // Take profit logic according to PDaC spec
    if (portfolio.positions?.length > 0) {
      const avgEntry = portfolio.positions[0].entryPrice;
      const profit = (price - avgEntry) / avgEntry;
      if (profit > takeProfit) {
        // 5% profit, take it
        return {
          action: 'close',
          confidence: 0.9,
        };
      }
    }

    return { action: 'hold', confidence: 0.7 };
  }
}
