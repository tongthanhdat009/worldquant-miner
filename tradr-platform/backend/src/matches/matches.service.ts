import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { GameService } from '../game/game.service';
import { RankingService } from '../ranking/ranking.service';

@Injectable()
export class MatchesService {
  constructor(
    private prisma: PrismaService,
    private gameService: GameService,
    private rankingService: RankingService,
  ) {}

  async createMatch(mode: string, userId: string) {
    const result = await this.gameService.createMatch(mode, userId);
    
    // Return according to PDaC spec
    if (result.status === 'queued') {
      return {
        match: null,
        status: 'queued',
      };
    }

    return {
      match: result,
      status: 'created',
    };
  }

  async getMatch(id: string) {
    return this.prisma.match.findUnique({
      where: { id },
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
  }

  async startMatch(id: string) {
    const match = await this.prisma.match.findUnique({
      where: { id },
    });

    if (!match) {
      throw new Error('Match not found');
    }

    if (match.status !== 'waiting') {
      throw new Error('Match cannot be started');
    }

    return this.gameService.startMatch(id);
  }

  async endMatch(id: string) {
    const result = await this.gameService.endMatch(id);
    
    // Update rankings if ranked match
    const match = await this.getMatch(id);
    if (match.mode === 'ranked_matchmaking' || match.mode === 'pvp_1v1') {
      const players = match.players.filter((p) => !p.isAi);
      if (players.length === 2) {
        const winner = result.rankings[0];
        const loser = result.rankings[1];
        
        if (winner && loser) {
          const winnerPlayer = players.find((p) => p.id === winner.playerId);
          const loserPlayer = players.find((p) => p.id === loser.playerId);
          
          if (winnerPlayer?.userId && loserPlayer?.userId) {
            await this.rankingService.updateRatings(
              winnerPlayer.userId,
              loserPlayer.userId,
              'win',
            );
          }
        }
      }
    }
    
    return result;
  }
}
