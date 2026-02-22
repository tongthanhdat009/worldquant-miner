import { Module } from '@nestjs/common';
import { TradingService } from './trading.service';
import { GameModule } from '../game/game.module';

@Module({
  imports: [GameModule],
  providers: [TradingService],
  exports: [TradingService],
})
export class TradingModule {}
