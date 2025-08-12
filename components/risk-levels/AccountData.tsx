import React, { useEffect, useState } from "react";

interface AccountDataItem {
  AccountName: string;
  Currency: string;
  Key: string;
  Value: string;
}

interface AccountSummaryProps {
  loadData: boolean;
}

function AccountSummary({ loadData }: AccountSummaryProps) {
  const [data, setData] = useState({
    StockMarketValue: null,
    TotalCashBalance: null,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!loadData) return;

    setLoading(true);
    fetch("http://localhost:8080/api/ib_accountdata")
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch");
        return res.json();
      })
      .then((json) => {
        const stockValueObj = json.accountdata.find(
          (item: AccountDataItem) =>
            item.Key === "StockMarketValue" && item.Currency === "USD"
        );
        const cashBalanceObj = json.accountdata.find(
          (item: AccountDataItem) =>
            item.Key === "TotalCashBalance" && item.Currency === "USD"
        );

        setData({
          StockMarketValue: stockValueObj ? stockValueObj.Value : "N/A",
          TotalCashBalance: cashBalanceObj ? cashBalanceObj.Value : "N/A",
        });
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [loadData]);

  if (!loadData) return null; // don't render anything if not ready

  if (loading) return <div>Loading account data...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div style={{ padding: "1rem", maxWidth: "300px", border: "1px solid #ccc" }}>
      <h2>Account Summary (USD)</h2>
      <div>
        <strong>Stock Market Value:</strong> ${data.StockMarketValue}
      </div>
      <div>
        <strong>Total Cash Balance:</strong> ${data.TotalCashBalance}
      </div>
    </div>
  );
}

export default AccountSummary;
