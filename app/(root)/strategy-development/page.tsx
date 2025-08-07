"use client";
import React, { useState } from "react";
import SQLQueryBox from "@/components/strategy-development/SqlQueryBox";
import LightweightChart from "@/components/strategy-development/LightWeightCharts";
import HeaderBox from "@/components/HeaderBox";
import InfoBox from "@/components/strategy-development/InfoBox";

interface DataItem {
  Ticker: string;
  Date: string;
  Setup: string;
}

const StrategyDeveloper = () => {
  // State to store the fetched data (single DataItem for InfoBox)
  const [fetchedData, setFetchedData] = useState<{
    Ticker?: string;
    Date?: string;
    Setup?: string;
  } | null>(null);

  // Handle data fetched from SQLQueryBox
  const handleDataFetched = (data: DataItem[]) => {
    if (Array.isArray(data) && data.length > 0) {
      const firstItem = data[0]; // Grab the first item from the array
      setFetchedData({
        Ticker: firstItem.Ticker,
        Date: firstItem.Date,
        Setup: firstItem.Setup,
      }); // Set the first item as an object with specific keys
    } else {
      console.error("Invalid data format");
    }
  };

  return (
    <section className="home">
      <div className="home-content">
        <header className="home-header">
          <HeaderBox
            type="greeting"
            title="Strategy development"
            subtext="Track opportunities out there"
          />
        </header>

        {/* SQL Query Box & Info Box in Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
          {/* SQL Query Box */}
          <SQLQueryBox onDataFetched={handleDataFetched} />

          {/* Info Box */}
          <InfoBox fetchedData={fetchedData} />
        </div>

        {/* Conditionally render the fetched data and charts */}
        {fetchedData && fetchedData.Ticker && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-y-6 mt-1">
            {/* First Chart */}
            <div>
              <LightweightChart
                ticker={fetchedData.Ticker}
                date={fetchedData.Date || "No date available"} // Fallback value for Date
                timeframe="marketdata5"
              />
            </div>

            {/* Second Chart */}
            <div>
              <LightweightChart
                ticker={fetchedData.Ticker}
                date={fetchedData.Date || "No date available"} // Fallback value for Date
                timeframe="marketdata2"
              />
            </div>

            {/* Third Chart */}
            <div>
              <LightweightChart
                ticker={fetchedData.Ticker}
                date={fetchedData.Date || "No date available"} // Fallback value for Date
                timeframe="marketdata30"
              />
            </div>
          </div>
        )}
      </div>
    </section>
  );
};

export default StrategyDeveloper;
