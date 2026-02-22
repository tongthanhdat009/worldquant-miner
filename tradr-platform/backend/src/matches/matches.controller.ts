import { Controller, Get, Post, Body, Param, HttpStatus, HttpException } from '@nestjs/common';
import { MatchesService } from './matches.service';
import { CreateMatchDto } from './dto/create-match.dto';

@Controller('matches')
export class MatchesController {
  constructor(private readonly matchesService: MatchesService) {}

  // POST /matches - According to PDaC spec
  @Post()
  async createMatch(@Body() createMatchDto: CreateMatchDto) {
    try {
      const result = await this.matchesService.createMatch(
        createMatchDto.mode,
        createMatchDto.userId,
      );

      // Return according to PDaC spec
      if (result.status === 'queued') {
        return {
          match: result.match,
          status: 'queued' as const,
        };
      }

      return {
        match: result.match,
        status: 'created' as const,
      };
    } catch (error: any) {
      if (error.message === 'Invalid game mode') {
        throw new HttpException('Invalid game mode', HttpStatus.BAD_REQUEST);
      }
      throw new HttpException('Internal server error', HttpStatus.INTERNAL_SERVER_ERROR);
    }
  }

  // GET /matches/:id - According to PDaC spec
  @Get(':id')
  async getMatch(@Param('id') id: string) {
    try {
      const match = await this.matchesService.getMatch(id);
      if (!match) {
        throw new HttpException('Match not found', HttpStatus.NOT_FOUND);
      }

      // Return according to PDaC spec
      return {
        match: {
          id: match.id,
          mode: match.mode,
          status: match.status,
          initialCapital: match.initialCapital,
          duration: match.duration,
          startedAt: match.startedAt,
          endedAt: match.endedAt,
          marketSymbol: match.marketSymbol,
          marketData: match.marketData,
          createdAt: match.createdAt,
          updatedAt: match.updatedAt,
        },
        players: match.players || [],
        positions: match.positions || [],
        orders: match.orders || [],
      };
    } catch (error: any) {
      if (error.status === HttpStatus.NOT_FOUND) {
        throw error;
      }
      throw new HttpException('Match not found', HttpStatus.NOT_FOUND);
    }
  }

  // POST /matches/:id/start - According to PDaC spec
  @Post(':id/start')
  async startMatch(@Param('id') id: string) {
    try {
      const match = await this.matchesService.startMatch(id);
      
      return {
        match: {
          id: match.id,
          mode: match.mode,
          status: match.status,
          initialCapital: match.initialCapital,
          duration: match.duration,
          startedAt: match.startedAt,
          endedAt: match.endedAt,
          marketSymbol: match.marketSymbol,
          marketData: match.marketData,
          createdAt: match.createdAt,
          updatedAt: match.updatedAt,
        },
        market: match.marketData,
      };
    } catch (error: any) {
      if (error.message === 'Match not found') {
        throw new HttpException('Match not found', HttpStatus.NOT_FOUND);
      }
      if (error.message.includes('cannot be started')) {
        throw new HttpException('Match cannot be started', HttpStatus.BAD_REQUEST);
      }
      throw new HttpException('Match not found', HttpStatus.NOT_FOUND);
    }
  }

  // POST /matches/:id/end - According to PDaC spec
  @Post(':id/end')
  async endMatch(@Param('id') id: string) {
    try {
      const result = await this.matchesService.endMatch(id);
      
      // Find winner (player with rank 1)
      const winner = result.rankings.find((r) => r.rank === 1);
      const winnerPlayer = result.match.players?.find((p) => p.id === winner?.playerId);

      return {
        match: {
          id: result.match.id,
          mode: result.match.mode,
          status: result.match.status,
          initialCapital: result.match.initialCapital,
          duration: result.match.duration,
          startedAt: result.match.startedAt,
          endedAt: result.match.endedAt,
          marketSymbol: result.match.marketSymbol,
          marketData: result.match.marketData,
          createdAt: result.match.createdAt,
          updatedAt: result.match.updatedAt,
        },
        rankings: result.rankings,
        winner: winnerPlayer || null,
      };
    } catch (error: any) {
      if (error.message === 'Match not found') {
        throw new HttpException('Match not found', HttpStatus.NOT_FOUND);
      }
      throw new HttpException('Match not found', HttpStatus.NOT_FOUND);
    }
  }
}
