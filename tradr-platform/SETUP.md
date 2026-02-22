# Tradr Platform Setup Guide

Complete setup instructions for the Tradr gaming trading platform.

## Prerequisites

- Node.js 18+ and npm
- PostgreSQL database
- Git

## Quick Start

### 1. Database Setup

Create a PostgreSQL database:
```sql
CREATE DATABASE tradr_platform;
```

### 2. Backend Setup

```bash
cd backend
npm install
```

Create `.env` file in `backend/` directory:
```
DATABASE_URL="postgresql://user:password@localhost:5432/tradr_platform"
PORT=3001
FRONTEND_URL=http://localhost:3000
JWT_SECRET=your-secret-key-here-change-this
```

Initialize Prisma:
```bash
npx prisma generate
npx prisma migrate dev --name init
```

Start backend:
```bash
npm run start:dev
```

Backend will run on `http://localhost:3001`

### 3. Frontend Setup

```bash
cd frontend
npm install
```

Start frontend:
```bash
npm run dev
```

Frontend will run on `http://localhost:3000`

## Features Implemented

### ✅ RTS Keyboard Shortcuts
- `1-4`: Switch between charts
- `Tab`: Cycle through charts  
- `B`: Quick buy at market
- `S`: Quick sell at market
- `C`: Close current position
- `X`: Close all positions
- `Esc`: Exit trading interface

### ✅ PVP/PVE Game Modes
- **1v1 Duel**: Face off against another trader
- **Battle Royale**: Last trader standing wins
- **AI Challenge**: Battle against AI traders (Easy/Medium/Hard)
- **Ranked Matchmaking**: Competitive ranked matches with ELO

### ✅ Real-Time Features
- WebSocket-based real-time synchronization
- Live market updates (10 updates/second)
- Real-time position tracking
- Live leaderboard updates

### ✅ AI Trader System
- Three difficulty levels: Easy, Medium, Hard
- Trend-following strategies
- Risk management
- Adaptive difficulty

### ✅ ELO Rating System
- Standard ELO calculation (K-factor: 32)
- Tier system: Bronze, Silver, Gold, Platinum, Diamond, Master, Grandmaster
- Matchmaking based on ELO rating

### ✅ Progression System
- XP and leveling system
- Achievements
- Feature unlocks based on level

## Architecture

### Backend (NestJS)
```
src/
├── game/           # Game modes, matchmaking, market simulation, AI
├── trading/        # Trade execution, position management
├── ranking/        # ELO rating system
├── progression/    # XP, levels, achievements
├── websocket/      # Real-time communication
├── matches/        # Match management API
├── auth/           # Authentication
└── users/          # User management
```

### Frontend (Next.js)
```
src/
├── app/            # Next.js app router pages
├── components/     # React components
│   ├── TradingInterface.tsx
│   ├── MultiChartManager.tsx
│   ├── Chart.tsx
│   ├── OrderPanel.tsx
│   ├── PositionPanel.tsx
│   ├── StatsPanel.tsx
│   └── MatchLobby.tsx
└── hooks/          # Custom React hooks
    ├── useRTSShortcuts.tsx
    └── useWebSocket.ts
```

## API Endpoints

### Matches
- `POST /matches` - Create a new match
  ```json
  {
    "mode": "pvp_1v1",
    "userId": "user-id"
  }
  ```
- `GET /matches/:id` - Get match details
- `POST /matches/:id/start` - Start a match
- `POST /matches/:id/end` - End a match

## WebSocket Events

### Client → Server
- `join_match` - Join a match room
  ```json
  {
    "matchId": "match-id",
    "userId": "user-id"
  }
  ```

- `player_action` - Execute a trading action
  ```json
  {
    "matchId": "match-id",
    "userId": "user-id",
    "action": {
      "type": "trade",
      "orderType": "MARKET",
      "side": "buy",
      "quantity": 0.1,
      "symbol": "BTC/USD"
    }
  }
  ```

### Server → Client
- `match_state` - Initial match state
- `state_sync` - Periodic state synchronization (10Hz)
- `action_executed` - Confirmation of action execution
- `action_error` - Error in action execution

## Database Schema

Key models:
- **User**: Players with ELO ratings, levels, XP
- **Match**: Game matches with mode, status, market data
- **MatchPlayer**: Players in a match with portfolio
- **Position**: Open/closed trading positions
- **Order**: Trading orders
- **Achievement**: Unlockable achievements
- **UserStats**: Player statistics

## Development

### Backend Commands
```bash
npm run start:dev    # Start with hot reload
npm run build        # Build for production
npm run start:prod   # Start production server
npm run prisma:studio # Open Prisma Studio
```

### Frontend Commands
```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
```

## Next Steps

1. **Authentication**: Implement JWT-based auth
2. **User Profiles**: User profile pages
3. **Leaderboards**: Global and seasonal leaderboards
4. **Replay System**: Match replay functionality
5. **Advanced Charts**: Integration with trading chart libraries
6. **More AI Strategies**: Additional AI trading strategies
7. **Tournaments**: Tournament system
8. **Social Features**: Friends, chat, spectating

## Troubleshooting

### Database Connection Issues
- Verify PostgreSQL is running
- Check DATABASE_URL in `.env`
- Ensure database exists

### WebSocket Connection Issues
- Verify backend is running on port 3001
- Check CORS settings in backend
- Verify FRONTEND_URL in backend `.env`

### Prisma Issues
```bash
npx prisma generate
npx prisma migrate reset  # WARNING: Deletes all data
```

## License

MIT
