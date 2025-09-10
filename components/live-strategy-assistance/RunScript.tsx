'use client';

import { useState } from 'react';

type RunScriptProps = {
  onSymbolsChange: (symbols: string[]) => void;
};

export default function RunScript({ onSymbolsChange }: RunScriptProps) {
  const [symbol, setSymbol] = useState('');
  const [output, setOutput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleRun = async () => {
    if (!symbol.trim()) return;

    setLoading(true);
    setOutput('');

    try {
      const res = await fetch('http://localhost:8080/run-script', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ param: symbol.trim() }),
      });

      const data = await res.json();
      setOutput(data.output || 'Script started successfully.');

      // Split by comma only, trim, and pass to parent
      const newSymbols = symbol
        .split(',')
        .map(s => s.trim().toUpperCase())
        .filter(Boolean);

      onSymbolsChange(newSymbols);
    } catch (err) {
      console.error(err);
      setOutput('Connection error.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleRun();
  };

  return (
    <div className="w-80 p-3 bg-white rounded-lg shadow-sm border border-gray-200 text-sm space-y-2">
      <div className="font-medium text-gray-700">Start Streamer</div>
      <input
        type="text"
        value={symbol}
        onChange={(e) => setSymbol(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Enter symbol(s), e.g. TSLA,AAPL"
        className="w-full px-2 py-1 border border-gray-300 rounded focus:ring-1 focus:ring-blue-400 focus:outline-none mb-1"
      />
      <button
        onClick={handleRun}
        disabled={loading}
        className="w-full bg-blue-600 text-white py-1 rounded hover:bg-blue-700 disabled:opacity-60"
      >
        {loading ? 'Running...' : 'Run'}
      </button>

      {output && (
        <div
          className={`p-2 rounded text-xs whitespace-pre-wrap max-h-32 overflow-auto ${
            output.toLowerCase().includes('error')
              ? 'bg-red-100 text-red-700'
              : 'bg-green-100 text-green-700'
          }`}
        >
          {output}
        </div>
      )}
    </div>
  );
}
