import { Module } from '@nestjs/common';
import { MatchesController } from './matches.controller';
import { MatchesService } from './matches.service';
import { GameModule } from '../game/game.module';
import { RankingModule } from '../ranking/ranking.module';

@Module({
  imports: [GameModule, RankingModule],
  controllers: [MatchesController],
  providers: [MatchesService],
  exports: [MatchesService],
})
export class MatchesModule {}
