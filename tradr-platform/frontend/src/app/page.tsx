'use client';

import { useState } from 'react';
import TradingInterface from '@/components/TradingInterface';
import MatchLobby from '@/components/MatchLobby';
import MatchmakingQueue from '@/components/MatchmakingQueue';
import MatchReady from '@/components/MatchReady';
import MatchSummary from '@/components/MatchSummary';
import { RTSShortcutProvider } from '@/hooks/useRTSShortcuts';
import { Match, Ranking } from '@/types/pdac';

type View = 'lobby' | 'queued' | 'ready' | 'trading' | 'summary';

export default function Home() {
  const [currentMatch, setCurrentMatch] = useState<string | null>(null);
  const [matchData, setMatchData] = useState<Match | null>(null);
  const [rankings, setRankings] = useState<Ranking[]>([]);
  const [playerRank, setPlayerRank] = useState<number>(1);
  const [view, setView] = useState<View>('lobby');

  // User flow transitions according to PDaC spec
  const handleMatchCreated = (matchId: string, status: 'created' | 'queued') => {
    setCurrentMatch(matchId);
    if (status === 'queued') {
      setView('queued');
    } else {
      // Fetch match data and go to ready screen
      fetchMatchData(matchId);
      setView('ready');
    }
  };

  const handleMatchQueued = (matchId: string) => {
    setCurrentMatch(matchId);
    setView('queued');
  };

  const handleOpponentFound = (matchId: string) => {
    fetchMatchData(matchId);
    setView('ready');
  };

  const handleMatchStart = (matchId: string) => {
    setView('trading');
  };

  const handleMatchEnd = (matchId: string, finalRankings: Ranking[], rank: number) => {
    setRankings(finalRankings);
    setPlayerRank(rank);
    setView('summary');
  };

  const fetchMatchData = async (matchId: string) => {
    try {
      const response = await fetch(`http://localhost:3001/matches/${matchId}`);
      if (response.ok) {
        const data = await response.json();
        setMatchData(data);
      }
    } catch (error) {
      console.error('Failed to fetch match data:', error);
    }
  };

  return (
    <RTSShortcutProvider>
      <main className="min-h-screen bg-gray-900 text-white">
        {view === 'lobby' && (
          <MatchLobby
            onMatchStart={(matchId) => handleMatchCreated(matchId, 'created')}
            onMatchQueued={handleMatchQueued}
          />
        )}
        
        {view === 'queued' && currentMatch && (
          <MatchmakingQueue
            matchId={currentMatch}
            onOpponentFound={handleOpponentFound}
            onCancel={() => setView('lobby')}
          />
        )}

        {view === 'ready' && matchData && (
          <MatchReady
            match={matchData}
            onStart={handleMatchStart}
          />
        )}

        {view === 'trading' && currentMatch && (
          <TradingInterface
            matchId={currentMatch}
            onExit={async () => {
              // Fetch final rankings before showing summary
              try {
                const response = await fetch(`http://localhost:3001/matches/${currentMatch}`);
                if (response.ok) {
                  const data = await response.json();
                  const player = data.players?.find((p: any) => !p.isAi);
                  if (player?.rank) {
                    // Calculate rankings from match data
                    const finalRankings: Ranking[] = (data.players || [])
                      .map((p: any) => ({
                        playerId: p.id,
                        totalValue: p.totalValue,
                        rank: p.rank || 0,
                      }))
                      .sort((a: Ranking, b: Ranking) => b.totalValue - a.totalValue)
                      .map((r: Ranking, index: number) => ({ ...r, rank: index + 1 }));
                    
                    handleMatchEnd(currentMatch, finalRankings, player.rank);
                  } else {
                    setView('lobby');
                  }
                } else {
                  setView('lobby');
                }
              } catch (error) {
                setView('lobby');
              }
            }}
          />
        )}

        {view === 'summary' && matchData && (
          <MatchSummary
            match={matchData}
            rankings={rankings}
            playerRank={playerRank}
            onPlayAgain={() => {
              setCurrentMatch(null);
              setMatchData(null);
              setRankings([]);
              setView('lobby');
            }}
            onExit={() => {
              setCurrentMatch(null);
              setMatchData(null);
              setRankings([]);
              setView('lobby');
            }}
          />
        )}
      </main>
    </RTSShortcutProvider>
  );
}
