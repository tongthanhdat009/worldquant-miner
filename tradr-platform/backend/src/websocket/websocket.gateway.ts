import {
  WebSocketGateway,
  WebSocketServer,
  SubscribeMessage,
  OnGatewayConnection,
  OnGatewayDisconnect,
  MessageBody,
  ConnectedSocket,
} from '@nestjs/websockets';
import { Server, Socket } from 'socket.io';
import { GameService } from '../game/game.service';
import { TradingService } from '../trading/trading.service';
import { MarketSimulatorService } from '../game/market-simulator.service';

@WebSocketGateway({
  cors: {
    origin: process.env.FRONTEND_URL || 'http://localhost:3000',
    credentials: true,
  },
})
export class WebSocketGateway
  implements OnGatewayConnection, OnGatewayDisconnect
{
  @WebSocketServer()
  server: Server;

  private connectedClients: Map<string, { socket: Socket; userId: string }> =
    new Map();

  constructor(
    private gameService: GameService,
    private tradingService: TradingService,
    private marketSimulator: MarketSimulatorService,
  ) {}

  handleConnection(client: Socket) {
    console.log(`Client connected: ${client.id}`);
  }

  handleDisconnect(client: Socket) {
    console.log(`Client disconnected: ${client.id}`);
    this.connectedClients.delete(client.id);
  }

  @SubscribeMessage('join_match')
  async handleJoinMatch(
    @ConnectedSocket() client: Socket,
    @MessageBody() data: { matchId: string; userId: string },
  ) {
    client.join(`match:${data.matchId}`);
    this.connectedClients.set(client.id, {
      socket: client,
      userId: data.userId,
    });

    // Send current match state
    const match = await this.gameService['prisma'].match.findUnique({
      where: { id: data.matchId },
      include: {
        players: true,
        positions: true,
        orders: true,
      },
    });

    client.emit('match_state', match);
  }

  @SubscribeMessage('player_action')
  async handlePlayerAction(
    @ConnectedSocket() client: Socket,
    @MessageBody()
    data: {
      matchId: string;
      userId: string;
      action: {
        type: string;
        [key: string]: any;
      };
    },
  ) {
    try {
      let result;

      if (data.action.type === 'trade') {
        result = await this.tradingService.executeTrade(
          data.userId,
          data.matchId,
          data.action,
        );
      } else if (data.action.type === 'close_position') {
        result = await this.tradingService.closePosition(
          data.userId,
          data.matchId,
          data.action.positionId,
        );
      }

      // Broadcast to all players in match
      this.server.to(`match:${data.matchId}`).emit('action_executed', {
        userId: data.userId,
        action: data.action,
        result,
        timestamp: new Date().toISOString(),
      });

      // Update match state
      await this.syncMatchState(data.matchId);
    } catch (error) {
      client.emit('action_error', {
        error: error.message,
        action: data.action,
      });
    }
  }

  @SubscribeMessage('request_match_state')
  async handleRequestMatchState(
    @ConnectedSocket() client: Socket,
    @MessageBody() data: { matchId: string },
  ) {
    await this.syncMatchState(data.matchId);
  }

  private async syncMatchState(matchId: string) {
    const match = await this.gameService['prisma'].match.findUnique({
      where: { id: matchId },
      include: {
        players: {
          include: {
            user: {
              select: {
                id: true,
                username: true,
                eloRating: true,
                tier: true,
              },
            },
          },
        },
        positions: true,
        orders: true,
      },
    });

    if (!match || match.status !== 'running') {
      return;
    }

    // Calculate current market price
    const marketData = match.marketData as any;
    const elapsedSeconds =
      (Date.now() - new Date(match.startedAt).getTime()) / 1000;
    const currentPrice = this.marketSimulator.getCurrentPrice(
      marketData,
      elapsedSeconds,
    );

    // Update portfolio values
    for (const player of match.players) {
      const positions = match.positions.filter(
        (p) => p.userId === player.userId && !p.closedAt,
      );

      let portfolioValue = player.cash;
      for (const position of positions) {
        const unrealizedPnl =
          (currentPrice - position.entryPrice) * position.quantity;
        portfolioValue += position.entryPrice * position.quantity + unrealizedPnl;
      }

      await this.gameService['prisma'].matchPlayer.update({
        where: { id: player.id },
        data: {
          totalValue: portfolioValue,
        },
      });
    }

    // Broadcast updated state
    const updatedMatch = await this.gameService['prisma'].match.findUnique({
      where: { id: matchId },
      include: {
        players: {
          include: {
            user: {
              select: {
                id: true,
                username: true,
                eloRating: true,
                tier: true,
              },
            },
          },
        },
        positions: true,
        orders: true,
      },
    });

    this.server.to(`match:${matchId}`).emit('state_sync', {
      match: updatedMatch,
      market: {
        currentPrice,
        elapsedSeconds,
      },
      timestamp: new Date().toISOString(),
    });
  }

  // Periodic state sync
  startMatchSync(matchId: string) {
    const interval = setInterval(async () => {
      const match = await this.gameService['prisma'].match.findUnique({
        where: { id: matchId },
      });

      if (!match || match.status !== 'running') {
        clearInterval(interval);
        return;
      }

      await this.syncMatchState(matchId);
    }, 100); // 10 updates per second

    return interval;
  }
}
