import { Module } from '@nestjs/common';
import { GameService } from './game.service';
import { MatchmakingService } from './matchmaking.service';
import { MarketSimulatorService } from './market-simulator.service';
import { AITraderService } from './ai-trader.service';

@Module({
  providers: [GameService, MatchmakingService, MarketSimulatorService, AITraderService],
  exports: [GameService, MatchmakingService, MarketSimulatorService, AITraderService],
})
export class GameModule {}
