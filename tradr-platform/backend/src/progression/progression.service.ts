import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

interface LevelConfig {
  xpRequired: number;
  unlocks: string[];
}

@Injectable()
export class ProgressionService {
  private levels: Record<number, LevelConfig> = {
    1: { xpRequired: 0, unlocks: ['basic_charts'] },
    5: { xpRequired: 1000, unlocks: ['advanced_indicators'] },
    10: { xpRequired: 5000, unlocks: ['multi_chart_4x4'] },
    15: { xpRequired: 15000, unlocks: ['custom_shortcuts'] },
    20: { xpRequired: 30000, unlocks: ['ai_opponents'] },
    25: { xpRequired: 50000, unlocks: ['ranked_matches'] },
  };

  private achievements = {
    first_trade: { xp: 50, title: 'First Trade' },
    win_10_matches: { xp: 200, title: 'Decade of Wins' },
    reach_diamond: { xp: 500, title: 'Diamond Trader' },
    '1000_apm': { xp: 300, title: 'Speed Demon' },
    perfect_match: { xp: 1000, title: 'Flawless Victory' },
  };

  constructor(private prisma: PrismaService) {}

  async awardXP(userId: string, source: string, amount: number) {
    const user = await this.prisma.user.findUnique({
      where: { id: userId },
    });

    if (!user) {
      throw new Error('User not found');
    }

    const newXp = user.xp + amount;
    const newTotalXp = user.totalXp + amount;
    const newLevel = this.calculateLevel(newTotalXp);

    const updatedUser = await this.prisma.user.update({
      where: { id: userId },
      data: {
        xp: newXp,
        totalXp: newTotalXp,
        level: newLevel,
      },
    });

    // Check for level up
    if (newLevel > user.level) {
      await this.handleLevelUp(userId, newLevel);
    }

    return updatedUser;
  }

  private calculateLevel(totalXp: number): number {
    let level = 1;
    for (const [levelNum, config] of Object.entries(this.levels)) {
      const num = parseInt(levelNum);
      if (totalXp >= config.xpRequired) {
        level = num;
      } else {
        break;
      }
    }
    return level;
  }

  private async handleLevelUp(userId: string, newLevel: number) {
    const levelConfig = this.levels[newLevel];
    if (!levelConfig) return;

    // Unlock features (stored in user preferences or separate table)
    // For now, we'll just log it
    console.log(`User ${userId} leveled up to ${newLevel}, unlocked:`, levelConfig.unlocks);
  }

  async unlockAchievement(userId: string, achievementCode: string) {
    const achievement = this.achievements[achievementCode];
    if (!achievement) {
      throw new Error(`Unknown achievement: ${achievementCode}`);
    }

    // Check if already unlocked
    const existing = await this.prisma.userAchievement.findFirst({
      where: {
        userId,
        achievement: {
          code: achievementCode,
        },
      },
    });

    if (existing) {
      return existing; // Already unlocked
    }

    // Get or create achievement
    let dbAchievement = await this.prisma.achievement.findUnique({
      where: { code: achievementCode },
    });

    if (!dbAchievement) {
      dbAchievement = await this.prisma.achievement.create({
        data: {
          code: achievementCode,
          name: achievement.title,
          description: `Unlock ${achievement.title}`,
          xpReward: achievement.xp,
        },
      });
    }

    // Unlock for user
    await this.prisma.userAchievement.create({
      data: {
        userId,
        achievementId: dbAchievement.id,
      },
    });

    // Award XP
    await this.awardXP(userId, `achievement_${achievementCode}`, achievement.xp);

    return dbAchievement;
  }

  async checkAchievements(userId: string, stats: any) {
    const checks = [
      {
        code: 'first_trade',
        condition: stats.totalTrades >= 1,
      },
      {
        code: 'win_10_matches',
        condition: stats.wins >= 10,
      },
      {
        code: 'reach_diamond',
        condition: stats.tier === 'Diamond',
      },
      {
        code: '1000_apm',
        condition: stats.highestApm >= 1000,
      },
    ];

    for (const check of checks) {
      if (check.condition) {
        await this.unlockAchievement(userId, check.code);
      }
    }
  }
}
