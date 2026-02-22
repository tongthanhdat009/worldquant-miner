# Tradr Platform Frontend

Next.js frontend for the Tradr gaming trading platform.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start development server:
```bash
npm run dev
```

Visit `http://localhost:3000`

## Features

### RTS Keyboard Shortcuts
- `1-4`: Switch between charts
- `Tab`: Cycle through charts
- `B`: Quick buy at market
- `S`: Quick sell at market
- `C`: Close current position
- `X`: Close all positions
- `Esc`: Exit trading interface

### Components

- **TradingInterface**: Main trading interface with RTS shortcuts
- **MultiChartManager**: Multi-chart grid layout
- **Chart**: Individual chart component
- **OrderPanel**: Order placement panel
- **PositionPanel**: Open positions display
- **StatsPanel**: Trading statistics
- **MatchLobby**: Game mode selection

## Architecture

- **App Router**: Next.js 14 App Router
- **WebSocket**: Real-time communication with backend
- **RTS Shortcuts**: Global keyboard shortcut system
- **State Management**: React hooks and context
