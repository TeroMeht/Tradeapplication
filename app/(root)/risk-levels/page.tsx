"use client"
import { useState } from "react";
import HeaderBox from "@/components/HeaderBox";
import PositionTable from "@/components/risk-levels/OpenOrdersTable";
import OpenRiskTable from "@/components/risk-levels/OpenRiskTable";
// import DailyPnl from "@/components/DailyPnL";


const Risklevels = () => {
  const [isPositionTableReady, setIsPositionTableReady] = useState(false);

  return (
    <section className="home">
      <div className="home-content">
        <header className="home-header">
          <HeaderBox
            type="greeting"
            title="Risk levels"
            subtext="Create transparency to the risk you are taking"
          />
          <PositionTable onComplete={() => setIsPositionTableReady(true)} />
          {isPositionTableReady && <OpenRiskTable />}
        </header>

                {/* Display Daily PnL */}
                {/* <section className="absolute bottom-4 right-4 bg-white shadow-lg p-4 rounded-lg border">
          <h2 className="text-xl font-semibold mb-2">Daily PnL</h2>
          <DailyPnl /> This is where Daily PnL will be shown
        </section> */}
      </div>
    </section>
  );
};

export default Risklevels;
