import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

interface QueueEntry {
  userId: string;
  mode: string;
  eloRating: number;
  queuedAt: Date;
}

@Injectable()
export class MatchmakingService {
  private queues: Map<string, QueueEntry[]> = new Map();
  private readonly ELO_TOLERANCE = 100; // Match players within 100 ELO points

  constructor(private prisma: PrismaService) {}

  async addToQueue(userId: string, mode: string) {
    const user = await this.prisma.user.findUnique({
      where: { id: userId },
      select: { eloRating: true },
    });

    if (!user) {
      throw new Error('User not found');
    }

    const queue = this.queues.get(mode) || [];
    const entry: QueueEntry = {
      userId,
      mode,
      eloRating: user.eloRating,
      queuedAt: new Date(),
    };

    queue.push(entry);
    this.queues.set(mode, queue);

    return entry;
  }

  async findOpponent(userId: string, useElo: boolean = true) {
    const user = await this.prisma.user.findUnique({
      where: { id: userId },
      select: { eloRating: true },
    });

    if (!user) {
      return null;
    }

    // Try to find opponent in all queues
    for (const [mode, queue] of this.queues.entries()) {
      const opponentIndex = queue.findIndex((entry) => {
        if (entry.userId === userId) return false;
        
        if (useElo) {
          const eloDiff = Math.abs(entry.eloRating - user.eloRating);
          return eloDiff <= this.ELO_TOLERANCE;
        }
        
        return true;
      });

      if (opponentIndex !== -1) {
        const opponent = queue.splice(opponentIndex, 1)[0];
        this.queues.set(mode, queue);
        
        return await this.prisma.user.findUnique({
          where: { id: opponent.userId },
        });
      }
    }

    return null;
  }

  removeFromQueue(userId: string) {
    for (const [mode, queue] of this.queues.entries()) {
      const index = queue.findIndex((entry) => entry.userId === userId);
      if (index !== -1) {
        queue.splice(index, 1);
        this.queues.set(mode, queue);
        return true;
      }
    }
    return false;
  }
}
