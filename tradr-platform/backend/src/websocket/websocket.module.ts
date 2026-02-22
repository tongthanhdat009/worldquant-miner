import { Module } from '@nestjs/common';
import { WebSocketGateway } from './websocket.gateway';
import { GameModule } from '../game/game.module';
import { TradingModule } from '../trading/trading.module';

@Module({
  imports: [GameModule, TradingModule],
  providers: [WebSocketGateway],
  exports: [WebSocketGateway],
})
export class WebSocketModule {}
