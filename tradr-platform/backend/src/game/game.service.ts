import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { MatchmakingService } from './matchmaking.service';
import { MarketSimulatorService } from './market-simulator.service';
import { AITraderService } from './ai-trader.service';

export interface GameMode {
  name: string;
  type: 'pvp' | 'pve';
  players: number;
  duration: number;
  initialCapital: number;
  market: string;
  ranking?: boolean;
  elimination?: boolean;
  survival?: boolean;
}

@Injectable()
export class GameService {
  private gameModes: Record<string, GameMode> = {
    pvp_1v1: {
      name: '1v1 Duel',
      type: 'pvp',
      players: 2,
      duration: 60,
      initialCapital: 10000,
      market: 'random',
      ranking: true,
    },
    pvp_battle_royale: {
      name: 'Battle Royale',
      type: 'pvp',
      players: 10,
      duration: 30,
      initialCapital: 10000,
      market: 'random',
      elimination: true,
      survival: true,
    },
    pve_ai_challenge: {
      name: 'AI Challenge',
      type: 'pve',
      players: 1,
      duration: 60,
      initialCapital: 10000,
      market: 'random',
    },
    pve_campaign: {
      name: 'Trading Campaign',
      type: 'pve',
      players: 1,
      duration: 60,
      initialCapital: 10000,
      market: 'random',
    },
    ranked_matchmaking: {
      name: 'Ranked Matchmaking',
      type: 'pvp',
      players: 2,
      duration: 60,
      initialCapital: 10000,
      market: 'random',
      ranking: true,
    },
  };

  constructor(
    private prisma: PrismaService,
    private matchmaking: MatchmakingService,
    private marketSimulator: MarketSimulatorService,
    private aiTrader: AITraderService,
  ) {}

  getGameModes(): Record<string, GameMode> {
    return this.gameModes;
  }

  async createMatch(mode: string, userId: string) {
    const gameMode = this.gameModes[mode];
    if (!gameMode) {
      throw new Error(`Invalid game mode: ${mode}`);
    }

    if (gameMode.type === 'pvp') {
      return this.createPVPMatch(mode, gameMode, userId);
    } else {
      return this.createPVEMatch(mode, gameMode, userId);
    }
  }

  private async createPVPMatch(mode: string, gameMode: GameMode, userId: string) {
    // Find opponent through matchmaking
    const opponent = await this.matchmaking.findOpponent(
      userId,
      gameMode.ranking || false,
    );

    if (!opponent) {
      // No opponent found, add to queue
      await this.matchmaking.addToQueue(userId, mode);
      // Create a placeholder match for queued status
      const queuedMatch = await this.prisma.match.create({
        data: {
          mode,
          status: 'waiting',
          initialCapital: gameMode.initialCapital,
          duration: gameMode.duration,
          players: {
            create: [
              {
                userId,
                isAi: false,
                cash: gameMode.initialCapital,
                totalValue: gameMode.initialCapital,
              },
            ],
          },
        },
        include: {
          players: {
            include: {
              user: true,
            },
          },
        },
      });
      return {
        match: queuedMatch,
        status: 'queued',
      };
    }

    // Create match
    const match = await this.prisma.match.create({
      data: {
        mode,
        status: 'waiting',
        initialCapital: gameMode.initialCapital,
        duration: gameMode.duration,
        players: {
          create: [
            {
              userId,
              isAi: false,
              cash: gameMode.initialCapital,
              totalValue: gameMode.initialCapital,
            },
            {
              userId: opponent.id,
              isAi: false,
              cash: gameMode.initialCapital,
              totalValue: gameMode.initialCapital,
            },
          ],
        },
      },
      include: {
        players: {
          include: {
            user: true,
          },
        },
      },
    });

    return match;
  }

  private async createPVEMatch(mode: string, gameMode: GameMode, userId: string) {
    // Select AI opponent
    const aiDifficulty = mode === 'pve_campaign' ? 'medium' : 'hard';
    const aiOpponent = await this.aiTrader.createAIOpponent(aiDifficulty);

    // Create match
    const match = await this.prisma.match.create({
      data: {
        mode,
        status: 'waiting',
        initialCapital: gameMode.initialCapital,
        duration: gameMode.duration,
        players: {
          create: [
            {
              userId,
              isAi: false,
              cash: gameMode.initialCapital,
              totalValue: gameMode.initialCapital,
            },
            {
              isAi: true,
              aiDifficulty,
              cash: gameMode.initialCapital,
              totalValue: gameMode.initialCapital,
            },
          ],
        },
      },
      include: {
        players: {
          include: {
            user: true,
          },
        },
      },
    });

    return match;
  }

  async startMatch(matchId: string) {
    const match = await this.prisma.match.findUnique({
      where: { id: matchId },
      include: { players: true },
    });

    if (!match) {
      throw new Error('Match not found');
    }

    // Initialize market simulator
    const marketData = await this.marketSimulator.createMarket(
      match.marketSymbol || 'BTC/USD',
      match.duration,
    );

    // Update match
    const updatedMatch = await this.prisma.match.update({
      where: { id: matchId },
      data: {
        status: 'running',
        startedAt: new Date(),
        marketData: marketData as any,
      },
    });

    return updatedMatch;
  }

  async endMatch(matchId: string) {
    const match = await this.prisma.match.findUnique({
      where: { id: matchId },
      include: { players: true },
    });

    if (!match) {
      throw new Error('Match not found');
    }

    // Calculate final rankings
    const rankings = match.players
      .map((player) => ({
        playerId: player.id,
        totalValue: player.totalValue,
      }))
      .sort((a, b) => b.totalValue - a.totalValue)
      .map((r, index) => ({
        ...r,
        rank: index + 1,
      }));

    // Update player ranks
    for (const ranking of rankings) {
      await this.prisma.matchPlayer.update({
        where: { id: ranking.playerId },
        data: { rank: ranking.rank },
      });
    }

    // Update match status
    const updatedMatch = await this.prisma.match.update({
      where: { id: matchId },
      data: {
        status: 'finished',
        endedAt: new Date(),
      },
    });

    return {
      match: updatedMatch,
      rankings,
    };
  }
}
