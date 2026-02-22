// Type definitions from PDaC specifications

export type GameMode = 
  | "pvp_1v1" 
  | "pvp_battle_royale" 
  | "pve_ai_challenge" 
  | "pve_campaign" 
  | "ranked_matchmaking";

export type MatchStatus = "waiting" | "running" | "finished" | "cancelled";
export type PlayerStatus = "active" | "eliminated" | "finished";
export type OrderStatus = "pending" | "filled" | "cancelled" | "rejected";
export type OrderType = "MARKET" | "LIMIT" | "STOP";
export type OrderSide = "BUY" | "SELL";
export type AIDifficulty = "easy" | "medium" | "hard";

export interface Match {
  id: string;
  mode: GameMode;
  status: MatchStatus;
  initialCapital: number;
  duration: number;
  startedAt: string | null;
  endedAt: string | null;
  marketSymbol: string | null;
  marketData: MarketData | null;
  createdAt: string;
  updatedAt: string;
}

export interface Player {
  id: string;
  userId: string | null;
  isAi: boolean;
  aiDifficulty: AIDifficulty | null;
  portfolioValue: number;
  cash: number;
  totalValue: number;
  trades: number;
  apm: number;
  accuracy: number;
  status: PlayerStatus;
  rank: number | null;
  user?: {
    id: string;
    username: string;
    eloRating: number;
    tier: string;
  };
}

export interface Position {
  id: string;
  userId: string;
  matchId: string | null;
  symbol: string;
  side: OrderSide;
  quantity: number;
  entryPrice: number;
  currentPrice: number;
  unrealizedPnl: number;
  stopLoss: number | null;
  takeProfit: number | null;
  openedAt: string;
  closedAt: string | null;
}

export interface Order {
  id: string;
  userId: string;
  matchId: string | null;
  symbol: string;
  side: OrderSide;
  type: OrderType;
  quantity: number;
  price: number | null;
  status: OrderStatus;
  filledQuantity: number;
  averagePrice: number | null;
  createdAt: string;
  filledAt: string | null;
}

export interface MarketData {
  symbol: string;
  startPrice: number;
  currentPrice: number;
  ticks: MarketTick[];
  duration: number;
}

export interface MarketTick {
  timestamp: string;
  price: number;
  volume: number;
  bid: number;
  ask: number;
}

export interface Ranking {
  playerId: string;
  totalValue: number;
  rank: number;
}

export interface FlashMessage {
  message: string;
  type: "success" | "error";
}

export interface MatchState {
  match: Match;
  players: Player[];
  positions: Position[];
  orders: Order[];
  market?: {
    currentPrice: number;
    elapsedSeconds: number;
  };
  portfolioValue?: number;
  stats?: Stats;
  userId?: string;
}

export interface Stats {
  trades: number;
  apm: number;
  accuracy: number;
  wins: number;
  losses: number;
}

export interface ChartConfig {
  symbol: string;
  timeframe: string;
}

export interface CreateMatchRequest {
  mode: GameMode;
  userId: string;
}

export interface CreateMatchResponse {
  match: Match;
  status: "created" | "queued";
}
