# Tradr Platform Backend

NestJS backend for the Tradr gaming trading platform.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

3. Initialize database:
```bash
npx prisma generate
npx prisma migrate dev
```

4. Start development server:
```bash
npm run start:dev
```

## API Endpoints

### Matches
- `POST /matches` - Create a new match
- `GET /matches/:id` - Get match details
- `POST /matches/:id/start` - Start a match
- `POST /matches/:id/end` - End a match

## WebSocket Events

### Client → Server
- `join_match` - Join a match room
- `player_action` - Execute a trading action
- `request_match_state` - Request current match state

### Server → Client
- `match_state` - Initial match state
- `state_sync` - Periodic state synchronization
- `action_executed` - Confirmation of action execution
- `action_error` - Error in action execution

## Database Schema

See `prisma/schema.prisma` for the complete database schema.

## Modules

- **GameModule**: Game modes, matchmaking, market simulation
- **TradingModule**: Trade execution and position management
- **RankingModule**: ELO rating system
- **ProgressionModule**: XP, levels, achievements
- **WebSocketModule**: Real-time communication
- **MatchesModule**: Match management
- **AuthModule**: Authentication (to be implemented)
- **UsersModule**: User management
