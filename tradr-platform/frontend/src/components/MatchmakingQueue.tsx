'use client';

import { useState, useEffect } from 'react';

interface MatchmakingQueueProps {
  matchId: string;
  onOpponentFound: (matchId: string) => void;
  onCancel: () => void;
}

export default function MatchmakingQueue({ matchId, onOpponentFound, onCancel }: MatchmakingQueueProps) {
  // State according to PDaC spec
  const [elapsedTime, setElapsedTime] = useState<number>(0);
  const [timeoutReached, setTimeoutReached] = useState<boolean>(false);

  // Update elapsed time
  useEffect(() => {
    const interval = setInterval(() => {
      setElapsedTime((prev) => {
        const newTime = prev + 1;
        // Timeout after 5 minutes (300 seconds) according to PDaC spec
        if (newTime >= 300) {
          setTimeoutReached(true);
          return prev;
        }
        return newTime;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  // Check for opponent found event (would come from WebSocket in real implementation)
  useEffect(() => {
    // In real implementation, this would listen to WebSocket events
    // For now, we'll simulate with a timeout
    const checkOpponent = setInterval(() => {
      // This would be replaced with actual WebSocket event listener
      // socket.on('opponent_found', () => onOpponentFound(matchId));
    }, 1000);

    return () => clearInterval(checkOpponent);
  }, [matchId, onOpponentFound]);

  // Handle timeout
  useEffect(() => {
    if (timeoutReached) {
      alert('Matchmaking timeout');
      onCancel();
    }
  }, [timeoutReached, onCancel]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900">
      <div className="bg-gray-800 rounded-lg p-8 max-w-md w-full text-center">
        <h1 className="text-3xl font-bold mb-4">Finding Opponent...</h1>
        <div className="mb-6">
          <div className="text-4xl font-mono mb-2">{formatTime(elapsedTime)}</div>
          <div className="text-sm text-gray-400">Elapsed time</div>
        </div>
        
        <div className="mb-6">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500 mx-auto"></div>
        </div>

        <p className="text-gray-400 mb-6">
          Waiting for a suitable opponent...
        </p>

        <button
          onClick={onCancel}
          className="w-full py-3 bg-red-600 hover:bg-red-700 rounded-lg font-bold"
        >
          Cancel Matchmaking
        </button>
      </div>
    </div>
  );
}
