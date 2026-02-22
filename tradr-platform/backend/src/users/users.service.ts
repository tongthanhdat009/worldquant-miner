import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class UsersService {
  constructor(private prisma: PrismaService) {}

  async findById(id: string) {
    return this.prisma.user.findUnique({
      where: { id },
      include: {
        stats: true,
        achievements: {
          include: {
            achievement: true,
          },
        },
      },
    });
  }

  async findByEmail(email: string) {
    return this.prisma.user.findUnique({
      where: { email },
    });
  }

  async create(data: { email: string; username: string; passwordHash: string }) {
    const user = await this.prisma.user.create({
      data: {
        ...data,
        stats: {
          create: {},
        },
      },
    });

    return user;
  }
}
