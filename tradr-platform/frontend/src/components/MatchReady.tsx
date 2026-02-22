'use client';

import { useState, useEffect } from 'react';
import { Match } from '@/types/pdac';

interface MatchReadyProps {
  match: Match;
  onStart: (matchId: string) => void;
}

export default function MatchReady({ match, onStart }: MatchReadyProps) {
  // State according to PDaC spec
  const [countdown, setCountdown] = useState<number>(3);

  // Auto-transition according to PDaC spec
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => {
        setCountdown(countdown - 1);
      }, 1000);
      return () => clearTimeout(timer);
    } else {
      // Auto-start when countdown reaches 0
      handleStart();
    }
  }, [countdown]);

  const handleStart = async () => {
    try {
      const response = await fetch(`http://localhost:3001/matches/${match.id}/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) {
        throw new Error('Failed to start match');
      }

      // Transition to "Trading Interface"
      onStart(match.id);
    } catch (error) {
      console.error('Failed to start match:', error);
      alert('Failed to start match. Please try again.');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900">
      <div className="bg-gray-800 rounded-lg p-8 max-w-md w-full text-center">
        <h1 className="text-3xl font-bold mb-4">Match Ready</h1>
        
        <div className="mb-6">
          <div className="text-6xl font-bold mb-2">
            {countdown > 0 ? countdown : 'GO!'}
          </div>
          <div className="text-sm text-gray-400">
            {countdown > 0 ? 'Starting in...' : 'Match starting...'}
          </div>
        </div>

        <div className="mb-6 p-4 bg-gray-700 rounded">
          <div className="text-sm text-gray-400 mb-2">Match Mode</div>
          <div className="text-lg font-semibold">{match.mode}</div>
        </div>

        {countdown === 0 && (
          <div className="mb-6">
            <div className="animate-pulse text-green-500 font-bold">
              Loading trading interface...
            </div>
          </div>
        )}

        {countdown > 0 && (
          <button
            onClick={handleStart}
            className="w-full py-3 bg-green-600 hover:bg-green-700 rounded-lg font-bold"
          >
            Start Now
          </button>
        )}
      </div>
    </div>
  );
}
