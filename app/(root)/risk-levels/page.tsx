"use client";

import HeaderBox from "@/components/HeaderBox";
import PortfolioDashboard from "@/components/risk-levels/PortfolioDashboard";
import PositionTable from "@/components/risk-levels/OpenOrdersTable";
import TablesList from "@/components/risk-levels/LiveMonitor"; // import your tables component

const Risklevels = () => {
  return (
    <section className="home">
      <div className="home-content">
        {/* Page header */}
        <header className="home-header">
          <HeaderBox
            type="greeting"
            title="Risk levels"
            subtext="Create transparency to the risk you are taking"
          />
        </header>
          {/* Right side: TablesList */}
          <div className="flex-1 w-full">
            <TablesList />
          </div>
        {/* ✅ Show Alpaca pending orders table first */}
        <div className="mt-6">
          <PositionTable onComplete={() => console.log("Alpaca table loaded")} />
        </div>

        {/* ✅ Then show IB portfolio dashboard (Account, Risk, Orders) */}
        <div className="mt-8">
          <PortfolioDashboard />
        </div>
      </div>
      
    </section>
  );
};

export default Risklevels;
