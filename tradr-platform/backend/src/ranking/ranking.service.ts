import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class RankingService {
  private readonly K_FACTOR = 32;
  private readonly INITIAL_RATING = 1000;

  constructor(private prisma: PrismaService) {}

  calculateExpectedScore(ratingA: number, ratingB: number): number {
    return 1 / (1 + Math.pow(10, (ratingB - ratingA) / 400));
  }

  async updateRatings(
    playerAId: string,
    playerBId: string,
    result: 'win' | 'loss' | 'draw',
  ) {
    const playerA = await this.prisma.user.findUnique({
      where: { id: playerAId },
      select: { eloRating: true },
    });

    const playerB = await this.prisma.user.findUnique({
      where: { id: playerBId },
      select: { eloRating: true },
    });

    if (!playerA || !playerB) {
      throw new Error('Player not found');
    }

    const expectedA = this.calculateExpectedScore(
      playerA.eloRating,
      playerB.eloRating,
    );
    const expectedB = 1 - expectedA;

    // Determine actual scores
    let actualA: number, actualB: number;
    if (result === 'win') {
      actualA = 1.0;
      actualB = 0.0;
    } else if (result === 'loss') {
      actualA = 0.0;
      actualB = 1.0;
    } else {
      actualA = 0.5;
      actualB = 0.5;
    }

    // Calculate new ratings
    const newRatingA =
      playerA.eloRating + this.K_FACTOR * (actualA - expectedA);
    const newRatingB =
      playerB.eloRating + this.K_FACTOR * (actualB - expectedB);

    // Update ratings
    const updatedA = await this.prisma.user.update({
      where: { id: playerAId },
      data: {
        eloRating: Math.round(newRatingA),
        tier: this.getTier(newRatingA),
      },
    });

    const updatedB = await this.prisma.user.update({
      where: { id: playerBId },
      data: {
        eloRating: Math.round(newRatingB),
        tier: this.getTier(newRatingB),
      },
    });

    return {
      playerA: updatedA,
      playerB: updatedB,
      ratingChangeA: Math.round(newRatingA - playerA.eloRating),
      ratingChangeB: Math.round(newRatingB - playerB.eloRating),
    };
  }

  getTier(rating: number): string {
    if (rating >= 2500) return 'Grandmaster';
    if (rating >= 2000) return 'Master';
    if (rating >= 1800) return 'Diamond';
    if (rating >= 1600) return 'Platinum';
    if (rating >= 1400) return 'Gold';
    if (rating >= 1200) return 'Silver';
    return 'Bronze';
  }

  async getLeaderboard(limit: number = 100) {
    return this.prisma.user.findMany({
      orderBy: { eloRating: 'desc' },
      take: limit,
      select: {
        id: true,
        username: true,
        eloRating: true,
        tier: true,
        level: true,
        stats: {
          select: {
            totalMatches: true,
            wins: true,
            winRate: true,
          },
        },
      },
    });
  }
}
