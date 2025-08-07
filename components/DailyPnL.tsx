import React, { useState, useEffect } from "react";

type DailyPnlData = {
  pnl: number;
  limitThreshold: number;
  limitExceeded: boolean;
  timestamp: string;
};

const DailyPnl: React.FC = () => {
  const [pnl, setPnl] = useState<number | null>(null);
  const [limitThreshold, setLimitThreshold] = useState<number | null>(null);
  const [limitExceeded, setLimitExceeded] = useState<boolean>(false);
  const [timestamp, setTimestamp] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<boolean>(false);

  const fetchDailyPnlStatus = async () => {
    setLoading(true);
    try {
      const response = await fetch("http://localhost:8080/api/dailypnl");
      if (!response.ok) {
        throw new Error("Failed to fetch Daily PnL data");
      }

      const data: DailyPnlData = await response.json();
      setPnl(data.pnl);
      setLimitThreshold(data.limitThreshold);
      setLimitExceeded(data.limitExceeded);
      setTimestamp(data.timestamp);
      setError(false);
    } catch (e) {
      setError(true);
      setPnl(null);
      setLimitThreshold(null);
      setLimitExceeded(false);
      setTimestamp(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDailyPnlStatus();
    const intervalId = setInterval(fetchDailyPnlStatus, 120000);
    return () => clearInterval(intervalId);
  }, []);

  return (
    <div className="w-full p-4 bg-white shadow-lg rounded-lg mt-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">Overview</h2>
        <div
          className={`text-sm font-semibold py-1 px-3 rounded-md ${
            error
              ? "bg-yellow-500 text-white"
              : limitExceeded
              ? "bg-red-600 text-white"
              : "bg-green-600 text-white"
          }`}
        >
          {error ? "Error" : limitExceeded ? "Limit Exceeded" : "Within Limit"}
        </div>
      </div>

      <div className="mt-4 space-y-2">
        {/* <div className="flex justify-between">
          <span className="font-medium">Daily PnL:</span>
          <span
            className={`font-semibold ${
              pnl !== null && pnl < 0
                ? "text-red-600"
                : pnl !== null
                ? "text-green-600"
                : "text-gray-500"
            }`}
          >
            {error ? "Error" : loading ? "Loading..." : pnl?.toFixed(2) ?? "N/A"}
          </span>
        </div> */}
        <div className="flex justify-between">
          <span className="font-medium">Limit Threshold:</span>
          <span className="font-semibold">
            {error ? "Error" : loading ? "Loading..." : limitThreshold?.toFixed(2) ?? "N/A"}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="font-medium">Last Updated:</span>
          <span className="text-sm text-gray-600">
            {error ? "Error" : loading ? "Loading..." : timestamp ?? "N/A"}
          </span>
        </div>
      </div>
    </div>
  );
};

export default DailyPnl;
