import React from "react";

interface AccountDataItem {
  AccountName: string;
  Currency: string;
  Key: string;
  Value: string;
}

interface AccountSummaryProps {
  accountdata: AccountDataItem[];
}

function AccountSummary({ accountdata }: AccountSummaryProps) {
  const stockValue = accountdata.find(
    (item) => item.Key === "StockMarketValue" && item.Currency === "USD"
  )?.Value;

  const cashBalance = accountdata.find(
    (item) => item.Key === "TotalCashBalance" && item.Currency === "USD"
  )?.Value;

  return (
    <div className="p-2 w-64 border rounded shadow bg-white text-sm">
      <h2 className="font-semibold mb-1">Account Summary (USD)</h2>
      <div className="mb-1">
        <span className="font-medium">Stock Value:</span> ${stockValue ?? "N/A"}
      </div>
      <div>
        <span className="font-medium">Cash Balance:</span> ${cashBalance ?? "N/A"}
      </div>
    </div>
  );
}

export default AccountSummary;
