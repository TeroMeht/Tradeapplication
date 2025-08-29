"use client";

import React, { useState, useCallback } from "react";
import AccountSummary from "./AccountSummary";
import RiskTable from "./RiskTable";

interface AccountDataItem {
  AccountName: string;
  Currency: string;
  Key: string;
  Value: string;
}

interface OpenRiskLevel {
  OrderId: number;
  Symbol: string;
  AuxPrice: number;
  AvgCost: number;
  OpenRisk: number | string;
  Position: number;
}

interface ApiResponse {
  accountdata: AccountDataItem[];
  risk_levels: OpenRiskLevel[];
  positions: any[];
  orders: any[];
}

function PortfolioDashboard() {
  const [accountdata, setAccountdata] = useState<AccountDataItem[]>([]);
  const [riskLevels, setRiskLevels] = useState<OpenRiskLevel[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPortfolioData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch("http://localhost:8080/api/ib_accountdata");
      if (!res.ok) throw new Error("Failed to fetch portfolio data");
      const json: ApiResponse = await res.json();
      setAccountdata(json.accountdata || []);
      setRiskLevels(json.risk_levels || []);
    } catch (err: any) {
      setError(err.message || "Unknown error fetching portfolio data");
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <div>
      <button
        onClick={fetchPortfolioData}
        className="bg-blue-500 text-white px-4 py-2 rounded mb-4"
        disabled={loading}
      >
        {loading ? "Loading..." : "Fetch Portfolio Data"}
      </button>

      {error && <div className="text-red-500 mb-2">Error: {error}</div>}

      {/* Open Risk Table */}
      <RiskTable riskLevels={riskLevels} onUpdate={fetchPortfolioData} />

      {/* Account Summary */}
      <AccountSummary accountdata={accountdata} />
    </div>
  );
}

export default PortfolioDashboard;
