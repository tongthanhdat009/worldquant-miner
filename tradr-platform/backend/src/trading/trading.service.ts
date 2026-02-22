import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { MarketSimulatorService } from '../game/market-simulator.service';

@Injectable()
export class TradingService {
  constructor(
    private prisma: PrismaService,
    private marketSimulator: MarketSimulatorService,
  ) {}

  async executeTrade(
    userId: string,
    matchId: string,
    action: {
      type: 'buy' | 'sell';
      orderType: 'MARKET' | 'LIMIT' | 'STOP';
      quantity: number;
      price?: number;
      symbol: string;
    },
  ) {
    const match = await this.prisma.match.findUnique({
      where: { id: matchId },
      include: {
        players: {
          where: { userId },
        },
      },
    });

    if (!match || match.status !== 'running') {
      throw new Error('Match not found or not running');
    }

    const player = match.players[0];
    if (!player) {
      throw new Error('Player not found in match');
    }

    // Get current market price
    const marketData = match.marketData as any;
    const elapsedSeconds =
      (Date.now() - new Date(match.startedAt).getTime()) / 1000;
    const currentPrice = this.marketSimulator.getCurrentPrice(
      marketData,
      elapsedSeconds,
    );

    // Calculate order price
    let executionPrice = currentPrice;
    if (action.orderType === 'LIMIT' && action.price) {
      executionPrice = action.price;
    } else if (action.orderType === 'STOP' && action.price) {
      executionPrice = action.price;
    }

    // Create order
    const order = await this.prisma.order.create({
      data: {
        userId,
        matchId,
        symbol: action.symbol,
        side: action.type === 'buy' ? 'BUY' : 'SELL',
        type: action.orderType,
        quantity: action.quantity,
        price: executionPrice,
        status: action.orderType === 'MARKET' ? 'filled' : 'pending',
        filledQuantity: action.orderType === 'MARKET' ? action.quantity : 0,
        averagePrice:
          action.orderType === 'MARKET' ? executionPrice : null,
        filledAt: action.orderType === 'MARKET' ? new Date() : null,
      },
    });

    // If market order, execute immediately
    if (action.orderType === 'MARKET') {
      await this.executeMarketOrder(order, player, executionPrice);
    }

    return order;
  }

  private async executeMarketOrder(
    order: any,
    player: any,
    price: number,
  ) {
    const cost = order.quantity * price;

    if (order.side === 'BUY') {
      if (player.cash < cost) {
        throw new Error('Insufficient funds');
      }

      // Update player cash
      await this.prisma.matchPlayer.update({
        where: { id: player.id },
        data: {
          cash: player.cash - cost,
        },
      });

      // Create position
      await this.prisma.position.create({
        data: {
          userId: order.userId,
          matchId: order.matchId,
          symbol: order.symbol,
          side: 'BUY',
          quantity: order.quantity,
          entryPrice: price,
          currentPrice: price,
        },
      });
    } else {
      // SELL - need to check if position exists
      const positions = await this.prisma.position.findMany({
        where: {
          userId: order.userId,
          matchId: order.matchId,
          symbol: order.symbol,
          side: 'BUY',
          closedAt: null,
        },
      });

      if (positions.length === 0) {
        throw new Error('No position to sell');
      }

      // Close position
      const position = positions[0];
      const profit = (price - position.entryPrice) * order.quantity;

      await this.prisma.position.update({
        where: { id: position.id },
        data: {
          closedAt: new Date(),
          currentPrice: price,
        },
      });

      // Update player cash
      await this.prisma.matchPlayer.update({
        where: { id: player.id },
        data: {
          cash: player.cash + cost,
        },
      });
    }

    // Update player stats
    await this.updatePlayerStats(order.userId, player.id);
  }

  async closePosition(userId: string, matchId: string, positionId: string) {
    const position = await this.prisma.position.findUnique({
      where: { id: positionId },
    });

    if (!position || position.userId !== userId || position.closedAt) {
      throw new Error('Position not found or already closed');
    }

    const match = await this.prisma.match.findUnique({
      where: { id: matchId },
    });

    const marketData = match.marketData as any;
    const elapsedSeconds =
      (Date.now() - new Date(match.startedAt).getTime()) / 1000;
    const currentPrice = this.marketSimulator.getCurrentPrice(
      marketData,
      elapsedSeconds,
    );

    const player = await this.prisma.matchPlayer.findFirst({
      where: { userId, matchId },
    });

    const profit = (currentPrice - position.entryPrice) * position.quantity;

    // Update position
    await this.prisma.position.update({
      where: { id: positionId },
      data: {
        closedAt: new Date(),
        currentPrice,
      },
    });

    // Update player cash
    await this.prisma.matchPlayer.update({
      where: { id: player.id },
      data: {
        cash: player.cash + currentPrice * position.quantity,
      },
    });

    return position;
  }

  private async updatePlayerStats(userId: string, playerId: string) {
    const player = await this.prisma.matchPlayer.findUnique({
      where: { id: playerId },
      include: {
        match: {
          include: {
            orders: {
              where: { userId },
            },
          },
        },
      },
    });

    const trades = player.match.orders.length;
    const startTime = new Date(player.match.startedAt);
    const elapsedMinutes = (Date.now() - startTime.getTime()) / 60000;
    const apm = trades / Math.max(elapsedMinutes, 1);

    await this.prisma.matchPlayer.update({
      where: { id: playerId },
      data: {
        trades,
        apm,
      },
    });
  }
}
