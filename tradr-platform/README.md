# Tradr Platform

A revolutionary gaming-inspired trading platform with RTS-style interface, PVP/PVE competition, and real-time multiplayer trading.

## Features

- **RTS-Style Interface**: Fast keyboard-driven trading with hotkeys
- **Multi-Chart Environment**: Manage multiple charts simultaneously
- **PVP/PVE Competition**: Battle against other traders or AI opponents
- **ELO Rating System**: Competitive ranking and matchmaking
- **Real-Time Synchronization**: WebSocket-based multiplayer
- **Progression System**: Levels, achievements, and unlocks

## Tech Stack

### Frontend
- Next.js 14 (App Router)
- React 18
- TypeScript
- Tailwind CSS
- Socket.io Client

### Backend
- NestJS
- Prisma ORM
- PostgreSQL
- Socket.io
- TypeScript

### Product Design as Code (PDaC)
- **PDaC Language**: Spec-driven development DSL
- **Code Generation**: Generate React/NestJS from specs
- **Validation**: Ensure implementation matches design
- See [pdac/](./pdac/) for details

## Getting Started

### Prerequisites
- Node.js 18+
- PostgreSQL
- npm or yarn

### Backend Setup

```bash
cd backend
npm install
```

Create a `.env` file:
```
DATABASE_URL="postgresql://user:password@localhost:5432/tradr_platform"
PORT=3001
FRONTEND_URL=http://localhost:3000
```

Initialize database:
```bash
npx prisma generate
npx prisma migrate dev
```

Start backend:
```bash
npm run start:dev
```

### Frontend Setup

```bash
cd frontend
npm install
```

Start frontend:
```bash
npm run dev
```

Visit `http://localhost:3000`

## RTS Keyboard Shortcuts

- `1-4`: Switch between charts
- `Tab`: Cycle through charts
- `B`: Quick buy at market
- `S`: Quick sell at market
- `C`: Close current position
- `X`: Close all positions
- `Esc`: Exit trading interface

## Game Modes

- **1v1 Duel**: Face off against another trader
- **Battle Royale**: Last trader standing wins
- **AI Challenge**: Battle against AI traders
- **Ranked Matchmaking**: Competitive ranked matches

## Architecture

The platform follows a client-server architecture with:
- Real-time WebSocket communication
- Market simulation engine
- AI trader opponents
- ELO-based matchmaking
- Progression and achievement system

### Spec-Driven Development

All features are defined in **PDaC** (Product Design as Code) specifications:
- Component designs → React components
- API contracts → NestJS controllers
- User flows → Implementation guides
- Game mechanics → Business logic

See [pdac/examples/](./pdac/examples/) for specifications.

## License

MIT
