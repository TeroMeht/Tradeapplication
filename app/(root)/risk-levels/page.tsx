"use client";
import { useState } from "react";
import HeaderBox from "@/components/HeaderBox";
import PositionTable from "@/components/risk-levels/OpenOrdersTable";
import OpenRiskTable from "@/components/risk-levels/OpenRiskTable";
import AccountSummary from "@/components/risk-levels/AccountData";

const Risklevels = () => {
  const [isPositionTableReady, setIsPositionTableReady] = useState(false);
  const [isOpenRiskLoaded, setIsOpenRiskLoaded] = useState(false);

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
          {isPositionTableReady && (
            <OpenRiskTable onLoaded={() => setIsOpenRiskLoaded(true)} />
          )}
        </header>

        {/* Pass the loadData prop here */}
        {isOpenRiskLoaded && <AccountSummary loadData={isOpenRiskLoaded} />}
      </div>
    </section>
  );
};

export default Risklevels;