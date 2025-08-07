import HeaderBox from "@/components/HeaderBox";
import ExecutionsTable from "@/components/portfolio-control-system/ExecutionsTable";
import PositionsTable from "@/components/portfolio-control-system/PositionsTable";
import OrdersTable from "@/components/portfolio-control-system/OrdersTable";
import PortfolioAlarmsTable from "@/components/portfolio-control-system/PortfolioAlarms";

const Portfoliocontrolsystem = () => {
  return (
    <section className="home">
      <div className="home-content space-y-2">
        <header className="home-header">
          <HeaderBox
            type="greeting"
            title="Portfolio Control System - PCS"
            subtext="Identify emotionally triggered state of mind and minimize its impacts"
          />
        </header>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 min-h-screen p-2 bg-gray-50">
        {/* Left: Executions Table (fills left side vertically) */}
        <div className="flex flex-col p-2 rounded-xl border bg-white shadow-md overflow-hidden">
          <h2 className="text-lg font-semibold mb-2">Executions</h2>
          <div className="flex-1 overflow-y-auto">
            <ExecutionsTable />
          </div>
        </div>

        {/* Right: Stack Positions and Alarms */}
        <div className="flex flex-col gap-2">
          {/* Positions Table */}
          <div className="flex flex-col p-2 rounded-xl border bg-white shadow-md overflow-hidden flex-1 min-h-[200px]">
            <h2 className="text-lg font-semibold mb-2">Open Positions</h2>
            <div className="flex-1 overflow-y-auto">
              <PositionsTable />
            </div>
          </div>

          {/* Alarms Table */}
          <div className="flex flex-col p-2 rounded-xl border bg-white shadow-md overflow-hidden flex-1 min-h-[200px]">
            <h2 className="text-lg font-semibold mb-2">PCS Alarms</h2>
            <div className="flex-1 overflow-y-auto">
              <PortfolioAlarmsTable />
            </div>
          </div>
        </div>
      </div>


        
      </div>

    </section>
  );
};

export default Portfoliocontrolsystem;
