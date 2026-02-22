'use client';

import { useState } from 'react';
import { GameMode, CreateMatchRequest, CreateMatchResponse } from '@/types/pdac';

interface MatchLobbyProps {
  onMatchStart: (matchId: string) => void;
  onMatchQueued?: (matchId: string) => void;
  userId?: string;
}

export default function MatchLobby({ onMatchStart, onMatchQueued, userId = 'user-123' }: MatchLobbyProps) {
  // State according to PDaC spec
  const [selectedMode, setSelectedMode] = useState<GameMode | null>(null);
  const [isCreating, setIsCreating] = useState<boolean>(false);

  const gameModes = [
    {
      id: 'pvp_1v1' as GameMode,
      name: '1v1 Duel',
      description: 'Face off against another trader',
      type: 'PVP',
    },
    {
      id: 'pvp_battle_royale' as GameMode,
      name: 'Battle Royale',
      description: 'Last trader standing wins',
      type: 'PVP',
    },
    {
      id: 'pve_ai_challenge' as GameMode,
      name: 'AI Challenge',
      description: 'Battle against AI traders',
      type: 'PVE',
    },
    {
      id: 'ranked_matchmaking' as GameMode,
      name: 'Ranked Matchmaking',
      description: 'Competitive ranked matches',
      type: 'PVP',
    },
  ];

  // Actions according to PDaC spec
  const selectMode = (mode: GameMode) => {
    setSelectedMode(mode);
  };

  const createMatch = async () => {
    if (!selectedMode) return;

    setIsCreating(true);
    try {
      const request: CreateMatchRequest = {
        mode: selectedMode,
        userId,
      };

      const response = await fetch('http://localhost:3001/matches', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error('Failed to create match');
      }

      const data: CreateMatchResponse = await response.json();

      if (data.status === 'queued') {
        // Transition to "Waiting for Opponent"
        if (onMatchQueued) {
          onMatchQueued(data.match.id);
        }
      } else {
        // Transition to "Start Match"
        onMatchStart(data.match.id);
      }
    } catch (error) {
      console.error('Failed to create match:', error);
      alert('Failed to create match. Please try again.');
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900">
      <div className="bg-gray-800 rounded-lg p-8 max-w-4xl w-full">
        <h1 className="text-4xl font-bold mb-8 text-center">Tradr Platform</h1>
        <h2 className="text-2xl font-semibold mb-6">Select Game Mode</h2>
        
        <div className="grid grid-cols-2 gap-4 mb-6">
          {gameModes.map((mode) => (
            <button
              key={mode.id}
              onClick={() => selectMode(mode.id)}
              className={`p-4 rounded-lg border-2 transition-all ${
                selectedMode === mode.id
                  ? 'border-green-500 bg-green-900'
                  : 'border-gray-700 bg-gray-700 hover:border-gray-600'
              }`}
            >
              <div className="flex justify-between items-start mb-2">
                <h3 className="font-bold text-lg">{mode.name}</h3>
                <span
                  className={`px-2 py-1 rounded text-xs ${
                    mode.type === 'PVP'
                      ? 'bg-blue-600'
                      : 'bg-purple-600'
                  }`}
                >
                  {mode.type}
                </span>
              </div>
              <p className="text-sm text-gray-400">{mode.description}</p>
            </button>
          ))}
        </div>

        <button
          onClick={createMatch}
          disabled={isCreating || !selectedMode}
          className="w-full py-4 bg-green-600 hover:bg-green-700 rounded-lg font-bold text-lg disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isCreating ? 'Creating Match...' : 'Start Match'}
        </button>
      </div>
    </div>
  );
}
