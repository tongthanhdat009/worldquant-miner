'use client';

import { useState } from 'react';
import { Socket } from 'socket.io-client';

interface OrderPanelProps {
  socket: Socket | null;
  matchId: string;
}

export default function OrderPanel({ socket, matchId }: OrderPanelProps) {
  const [orderType, setOrderType] = useState<'MARKET' | 'LIMIT' | 'STOP'>('MARKET');
  const [side, setSide] = useState<'buy' | 'sell'>('buy');
  const [quantity, setQuantity] = useState('0.1');
  const [price, setPrice] = useState('');

  const handleSubmit = () => {
    if (!socket) return;

    socket.emit('player_action', {
      matchId,
      action: {
        type: 'trade',
        orderType,
        side,
        quantity: parseFloat(quantity),
        price: price ? parseFloat(price) : undefined,
        symbol: 'BTC/USD',
      },
    });
  };

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <h3 className="font-bold mb-4">Order Panel</h3>
      
      <div className="space-y-4">
        <div>
          <label className="block text-sm mb-2">Order Type</label>
          <select
            value={orderType}
            onChange={(e) => setOrderType(e.target.value as any)}
            className="w-full bg-gray-700 rounded p-2"
          >
            <option value="MARKET">Market</option>
            <option value="LIMIT">Limit</option>
            <option value="STOP">Stop</option>
          </select>
        </div>

        <div>
          <label className="block text-sm mb-2">Side</label>
          <div className="flex gap-2">
            <button
              onClick={() => setSide('buy')}
              className={`flex-1 py-2 rounded ${
                side === 'buy' ? 'bg-green-600' : 'bg-gray-700'
              }`}
            >
              Buy (B)
            </button>
            <button
              onClick={() => setSide('sell')}
              className={`flex-1 py-2 rounded ${
                side === 'sell' ? 'bg-red-600' : 'bg-gray-700'
              }`}
            >
              Sell (S)
            </button>
          </div>
        </div>

        <div>
          <label className="block text-sm mb-2">Quantity</label>
          <input
            type="number"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            className="w-full bg-gray-700 rounded p-2"
            step="0.01"
          />
        </div>

        {orderType !== 'MARKET' && (
          <div>
            <label className="block text-sm mb-2">Price</label>
            <input
              type="number"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              className="w-full bg-gray-700 rounded p-2"
              step="0.01"
            />
          </div>
        )}

        <button
          onClick={handleSubmit}
          className="w-full py-2 bg-blue-600 hover:bg-blue-700 rounded"
        >
          Submit Order
        </button>
      </div>
    </div>
  );
}
