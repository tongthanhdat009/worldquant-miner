'use client';

import { useState, useEffect, useRef } from 'react';
import { io, Socket } from 'socket.io-client';

export function useWebSocket(matchId: string) {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [matchState, setMatchState] = useState<any>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const newSocket = io('http://localhost:3001', {
      transports: ['websocket'],
    });

    newSocket.on('connect', () => {
      console.log('Connected to server');
      setConnected(true);
      newSocket.emit('join_match', { matchId, userId: 'user-123' });
    });

    newSocket.on('disconnect', () => {
      console.log('Disconnected from server');
      setConnected(false);
    });

    newSocket.on('match_state', (state) => {
      setMatchState(state);
    });

    newSocket.on('state_sync', (data) => {
      setMatchState((prev: any) => ({
        ...prev,
        ...data.match,
        market: data.market,
      }));
    });

    newSocket.on('action_executed', (data) => {
      console.log('Action executed:', data);
    });

    setSocket(newSocket);

    return () => {
      newSocket.close();
    };
  }, [matchId]);

  return { socket, matchState, connected };
}
