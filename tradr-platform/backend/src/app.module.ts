import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { PrismaModule } from './prisma/prisma.module';
import { AuthModule } from './auth/auth.module';
import { UsersModule } from './users/users.module';
import { MatchesModule } from './matches/matches.module';
import { TradingModule } from './trading/trading.module';
import { GameModule } from './game/game.module';
import { RankingModule } from './ranking/ranking.module';
import { ProgressionModule } from './progression/progression.module';
import { WebSocketModule } from './websocket/websocket.module';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
    }),
    PrismaModule,
    AuthModule,
    UsersModule,
    MatchesModule,
    TradingModule,
    GameModule,
    RankingModule,
    ProgressionModule,
    WebSocketModule,
  ],
})
export class AppModule {}
