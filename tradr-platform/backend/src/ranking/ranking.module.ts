import { Module } from '@nestjs/common';
import { RankingService } from './ranking.service';

@Module({
  providers: [RankingService],
  exports: [RankingService],
})
export class RankingModule {}
