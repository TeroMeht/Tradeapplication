'use client';

import { useState } from 'react';
import HeaderBox from "@/components/HeaderBox";
import RunScript from '@/components/live-strategy-assistance/RunScript';

const Page = () => {
  const [, setSymbols] = useState<string[]>([]);

  // Handle symbols coming from RunScript
  const handleSymbolsChange = (newSymbols: string[]) => {
    const splitSymbols = newSymbols
      .map(s => s.split(',').map(s2 => s2.trim().toUpperCase()))
      .flat()
      .filter(Boolean);

    console.log("Symbols received:", splitSymbols);
    setSymbols(splitSymbols);
  };

  return (
    <section className="home">
      <div className="home-content">
        <header className="home-header">
          <HeaderBox
            type="greeting"
            title="Live Strategy Assistance"
            subtext=""
          />
        </header>

        <div className="flex flex-col items-start mb-6">
          <RunScript onSymbolsChange={handleSymbolsChange} />
        </div>
      </div>
    </section>
  );
};

export default Page;
