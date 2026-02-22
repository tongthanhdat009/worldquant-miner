'use client';

import { Match, Ranking, Player } from '@/types/pdac';

interface MatchSummaryProps {
  match: Match;
  rankings: Ranking[];
  playerRank: number;
  onPlayAgain: () => void;
  onViewReplay?: () => void;
  onExit: () => void;
}

export default function MatchSummary({
  match,
  rankings,
  playerRank,
  onPlayAgain,
  onViewReplay,
  onExit,
}: MatchSummaryProps) {
  const winner = rankings[0];
  const isWinner = playerRank === 1;

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900">
      <div className="bg-gray-800 rounded-lg p-8 max-w-2xl w-full">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-2">
            {isWinner ? '🎉 Victory!' : 'Match Complete'}
          </h1>
          <p className="text-gray-400">Match: {match.mode}</p>
        </div>

        {/* Rankings */}
        <div className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Final Rankings</h2>
          <div className="space-y-2">
            {rankings.map((ranking, index) => (
              <div
                key={ranking.playerId}
                className={`p-4 rounded-lg flex justify-between items-center ${
                  index === 0
                    ? 'bg-yellow-900 border-2 border-yellow-500'
                    : index === playerRank - 1
                    ? 'bg-blue-900 border-2 border-blue-500'
                    : 'bg-gray-700'
                }`}
              >
                <div className="flex items-center gap-4">
                  <div className="text-2xl font-bold w-8">#{ranking.rank}</div>
                  <div>
                    <div className="font-semibold">
                      {index === playerRank - 1 ? 'You' : `Player ${ranking.playerId.slice(0, 8)}`}
                    </div>
                    {index === 0 && (
                      <div className="text-sm text-yellow-400">🏆 Winner</div>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-bold">${ranking.totalValue.toFixed(2)}</div>
                  <div className="text-sm text-gray-400">
                    {((ranking.totalValue / match.initialCapital - 1) * 100).toFixed(2)}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Match Stats */}
        <div className="mb-8 p-4 bg-gray-700 rounded">
          <h3 className="font-semibold mb-2">Match Statistics</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <div className="text-gray-400">Duration</div>
              <div className="font-semibold">
                {match.duration} minutes
              </div>
            </div>
            <div>
              <div className="text-gray-400">Initial Capital</div>
              <div className="font-semibold">${match.initialCapital.toFixed(2)}</div>
            </div>
            <div>
              <div className="text-gray-400">Your Rank</div>
              <div className="font-semibold">#{playerRank}</div>
            </div>
            <div>
              <div className="text-gray-400">Status</div>
              <div className="font-semibold capitalize">{match.status}</div>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-4">
          <button
            onClick={onPlayAgain}
            className="flex-1 py-3 bg-green-600 hover:bg-green-700 rounded-lg font-bold"
          >
            Play Again
          </button>
          {onViewReplay && (
            <button
              onClick={onViewReplay}
              className="flex-1 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-bold"
            >
              View Replay
            </button>
          )}
          <button
            onClick={onExit}
            className="flex-1 py-3 bg-gray-600 hover:bg-gray-700 rounded-lg font-bold"
          >
            Exit
          </button>
        </div>
      </div>
    </div>
  );
}
