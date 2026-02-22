'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRTSShortcuts } from '@/hooks/useRTSShortcuts';
import MultiChartManager from './MultiChartManager';
import OrderPanel from './OrderPanel';
import PositionPanel from './PositionPanel';
import StatsPanel from './StatsPanel';
import { useWebSocket } from '@/hooks/useWebSocket';
import { FlashMessage, MatchState } from '@/types/pdac';

interface TradingInterfaceProps {
  matchId: string;
  onExit: () => void;
}

export default function TradingInterface({ matchId, onExit }: TradingInterfaceProps) {
  // State according to PDaC spec
  const [focusedChart, setFocusedChart] = useState<number>(0);
  const [flashMessage, setFlashMessage] = useState<FlashMessage | null>(null);
  const [matchState, setMatchState] = useState<MatchState | null>(null);
  
  const { socket, matchState: wsMatchState, connected } = useWebSocket(matchId);
  const { registerShortcut, unregisterShortcut } = useRTSShortcuts();

  // Update matchState from WebSocket
  useEffect(() => {
    if (wsMatchState) {
      setMatchState(wsMatchState);
    }
  }, [wsMatchState]);

  // Behaviors according to PDaC spec
  const connectWebSocket = useCallback(() => {
    // WebSocket connection handled by useWebSocket hook
    if (socket && !connected) {
      socket.connect();
    }
  }, [socket, connected]);

  const disconnectWebSocket = useCallback(() => {
    if (socket) {
      socket.disconnect();
    }
  }, [socket]);

  const updateFocusedChart = useCallback((index: number) => {
    setFocusedChart(index);
  }, []);

  const updateMatchState = useCallback((state: MatchState) => {
    setMatchState(state);
  }, []);

  const syncState = useCallback((data: any) => {
    if (data.match) {
      setMatchState((prev) => ({
        ...prev!,
        ...data.match,
        market: data.market,
      }));
    }
  }, []);

  // Register RTS shortcuts according to PDaC spec
  useEffect(() => {
    const switchToChart = (index: number) => () => setFocusedChart(index);
    const cycleCharts = () => setFocusedChart((prev) => (prev + 1) % 4);

    const shortcuts = {
      '1': switchToChart(0),
      '2': switchToChart(1),
      '3': switchToChart(2),
      '4': switchToChart(3),
      'Tab': cycleCharts,
      'B': handleQuickBuy,
      'S': handleQuickSell,
      'C': handleClosePosition,
      'X': handleCloseAll,
      'Esc': onExit,
    };

    Object.entries(shortcuts).forEach(([key, handler]) => {
      registerShortcut(key, handler);
    });

    return () => {
      Object.keys(shortcuts).forEach((key) => {
        unregisterShortcut(key);
      });
    };
  }, [registerShortcut, unregisterShortcut, onExit, handleQuickBuy, handleQuickSell, handleClosePosition, handleCloseAll]);

  // Events according to PDaC spec
  useEffect(() => {
    if (!socket) return;

    const handleMatchState = (state: MatchState) => {
      updateMatchState(state);
    };

    const handleStateSync = (data: any) => {
      syncState(data);
    };

    const handleActionExecuted = (data: any) => {
      showFlashMessage(`Action executed: ${data.action.type}`, 'success');
    };

    const handleActionError = (data: any) => {
      showFlashMessage(data.error || 'Action failed', 'error');
    };

    socket.on('match_state', handleMatchState);
    socket.on('state_sync', handleStateSync);
    socket.on('action_executed', handleActionExecuted);
    socket.on('action_error', handleActionError);

    return () => {
      socket.off('match_state', handleMatchState);
      socket.off('state_sync', handleStateSync);
      socket.off('action_executed', handleActionExecuted);
      socket.off('action_error', handleActionError);
    };
  }, [socket, updateMatchState, syncState]);

  // onMount/onUnmount behaviors
  useEffect(() => {
    connectWebSocket();
    return () => {
      disconnectWebSocket();
    };
  }, [connectWebSocket, disconnectWebSocket]);

  const showFlashMessage = useCallback((message: string, type: 'success' | 'error') => {
    setFlashMessage({ message, type });
    setTimeout(() => setFlashMessage(null), 2000);
  }, []);

  const executeTrade = useCallback((action: any) => {
    if (!socket || !matchState?.userId) return;
    
    socket.emit('player_action', {
      matchId,
      userId: matchState.userId,
      action,
    });
  }, [socket, matchState, matchId]);

  const closePosition = useCallback((positionId: string) => {
    if (!socket || !matchState?.userId) return;
    
    socket.emit('player_action', {
      matchId,
      userId: matchState.userId,
      action: {
        type: 'close_position',
        positionId,
      },
    });
  }, [socket, matchState, matchId]);

  const handleQuickBuy = useCallback(() => {
    if (!matchState) return;
    
    const charts = [
      { symbol: 'BTC/USD' },
      { symbol: 'ETH/USD' },
      { symbol: 'EUR/USD' },
      { symbol: 'GBP/USD' },
    ];
    const symbol = charts[focusedChart]?.symbol || 'BTC/USD';
    
    executeTrade({
      type: 'trade',
      orderType: 'MARKET',
      side: 'buy',
      quantity: 0.1,
      symbol,
    });
    
    showFlashMessage(`BUY ${symbol} @ MARKET`, 'success');
  }, [matchState, focusedChart, executeTrade, showFlashMessage]);

  const handleQuickSell = useCallback(() => {
    if (!matchState) return;
    
    const charts = [
      { symbol: 'BTC/USD' },
      { symbol: 'ETH/USD' },
      { symbol: 'EUR/USD' },
      { symbol: 'GBP/USD' },
    ];
    const symbol = charts[focusedChart]?.symbol || 'BTC/USD';
    
    executeTrade({
      type: 'trade',
      orderType: 'MARKET',
      side: 'sell',
      quantity: 0.1,
      symbol,
    });
    
    showFlashMessage(`SELL ${symbol} @ MARKET`, 'success');
  }, [matchState, focusedChart, executeTrade, showFlashMessage]);

  const handleClosePosition = useCallback(() => {
    if (!matchState) return;
    
    const positions = matchState.positions || [];
    const openPosition = positions.find((p) => !p.closedAt);
    
    if (openPosition) {
      closePosition(openPosition.id);
      showFlashMessage('Position Closed', 'success');
    } else {
      showFlashMessage('No open positions', 'error');
    }
  }, [matchState, closePosition, showFlashMessage]);

  const handleCloseAll = useCallback(() => {
    if (!matchState) return;
    
    const positions = matchState.positions || [];
    const openPositions = positions.filter((p) => !p.closedAt);
    
    if (openPositions.length === 0) {
      showFlashMessage('No open positions', 'error');
      return;
    }
    
    openPositions.forEach((position) => {
      closePosition(position.id);
    });
    
    showFlashMessage('All Positions Closed', 'success');
  }, [matchState, closePosition, showFlashMessage]);

  return (
    <div className="h-screen flex flex-col bg-gray-900">
      {/* Header */}
      <div className="bg-gray-800 p-4 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Tradr Platform</h1>
          <p className="text-sm text-gray-400">Match: {matchId.slice(0, 8)}</p>
        </div>
        <div className="flex gap-4">
          <div className="text-right">
            <div className="text-sm text-gray-400">Portfolio Value</div>
            <div className="text-xl font-bold">
              ${matchState?.portfolioValue?.toFixed(2) || '0.00'}
            </div>
          </div>
          <button
            onClick={onExit}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded"
          >
            Exit (Esc)
          </button>
        </div>
      </div>

      {/* Main Trading Area - According to PDaC layout spec */}
      <div className="flex-1 grid grid-cols-3 gap-4 p-4">
        {/* Charts - span 2 columns */}
        <div className="col-span-2">
          <MultiChartManager
            focusedChart={focusedChart}
            onChartFocus={updateFocusedChart}
            matchState={matchState}
          />
        </div>

        {/* Sidebar - span 1 column, stacked */}
        <div className="col-span-1 flex flex-col gap-4">
          <OrderPanel socket={socket} matchId={matchId} />
          <PositionPanel positions={matchState?.positions || []} />
          <StatsPanel stats={matchState?.stats || { trades: 0, apm: 0, accuracy: 0, wins: 0, losses: 0 }} />
        </div>
      </div>

      {/* Flash Messages */}
      {flashMessage && (
        <div className={`flash-message ${flashMessage.type}`}>
          {flashMessage.message}
        </div>
      )}

      {/* Shortcut Help */}
      <div className="bg-gray-800 p-2 text-xs text-gray-400">
        <span className="mr-4">1-4: Switch Chart</span>
        <span className="mr-4">B: Buy</span>
        <span className="mr-4">S: Sell</span>
        <span className="mr-4">C: Close Position</span>
        <span className="mr-4">X: Close All</span>
        <span>Esc: Exit</span>
      </div>
    </div>
  );
}
