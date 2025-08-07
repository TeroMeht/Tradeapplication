import React, { useEffect, useState } from "react";
import { format, parseISO } from "date-fns";
import { parse } from "date-fns"; // Add at the top

interface Trade {
  Date: string;
  Setup: string;
  Symbol: string;
  TradeId: number;
}

type SetupCountsByMonth = {
  [month: string]: { [setup: string]: number };
};

type CategoryCountsByMonth = {
  [month: string]: { [category: string]: number };
};

// Define setup categories
const setupCategories: { [category: string]: string[] } = {
  Continuation: [ 'ORB', 'Episodic Pivot'],
  Reversal: ['Extreme Reversal', 'Reversal','Parabolic short'],
  Uncategorized: ['No setup'],
};

const TradeKPI: React.FC = () => {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [countsByMonth, setCountsByMonth] = useState<SetupCountsByMonth>({});
  const [categoryCountsByMonth, setCategoryCountsByMonth] = useState<CategoryCountsByMonth>({});
  const [allSetups, setAllSetups] = useState<string[]>([]);

  useEffect(() => {
    const fetchTrades = async () => {
      try {
        const res = await fetch("http://localhost:8080/api/trades");
        const data: Trade[] = await res.json();
        setTrades(data);
      } catch (err) {
        console.error("Failed to fetch trades", err);
      }
    };

    fetchTrades();
  }, []);

  useEffect(() => {
    const counts: SetupCountsByMonth = {};
    const categoryCounts: CategoryCountsByMonth = {};
    const setupsSet = new Set<string>();

    trades.forEach(({ Date: dateStr, Setup }) => {
      const date = parseISO(dateStr);
      const month = format(date, 'MMMM yyyy');

      setupsSet.add(Setup);

      // Setup counts
      if (!counts[month]) counts[month] = {};
      counts[month][Setup] = (counts[month][Setup] || 0) + 1;

      // Category counts
      let matchedCategory = 'Other';
      for (const [category, setupList] of Object.entries(setupCategories)) {
        if (setupList.includes(Setup)) {
          matchedCategory = category;
          break;
        }
      }

      if (!categoryCounts[month]) categoryCounts[month] = {};
      categoryCounts[month][matchedCategory] = (categoryCounts[month][matchedCategory] || 0) + 1;
    });

    setCountsByMonth(counts);
    setAllSetups(Array.from(setupsSet).sort());
    setCategoryCountsByMonth(categoryCounts);
  }, [trades]);

  
    const sortedMonths = Object.keys(countsByMonth).sort((a, b) =>
    parse(a, "MMMM yyyy", new Date()).getTime() - parse(b, "MMMM yyyy", new Date()).getTime()
    );

  return (
    <div className="max-w-6xl mx-auto p-4 bg-white rounded shadow mt-10">
      <h2 className="text-2xl font-semibold mb-6">Trade KPI: Setups by Month</h2>

      {/* Setup Count Table */}
      <h3 className="text-lg font-semibold mb-2">Setups</h3>
      <table className="w-full border-collapse border border-gray-300 mb-10">
        <thead>
          <tr>
            <th className="border border-gray-300 p-2 text-left">Month</th>
            {allSetups.map((setup) => (
              <th key={setup} className="border border-gray-300 p-2 text-left">
                {setup}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedMonths.map((month) => (
            <tr key={month} className="even:bg-gray-50">
              <td className="border border-gray-300 p-2 font-medium">{month}</td>
              {allSetups.map((setup) => (
                <td key={setup} className="border border-gray-300 p-2 text-center">
                  {countsByMonth[month][setup] || 0}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      {/* Category Count Table */}
      <h3 className="text-lg font-semibold mb-2">Categories</h3>
      <table className="w-full border-collapse border border-gray-300">
        <thead>
          <tr>
            <th className="border border-gray-300 p-2 text-left">Month</th>
            {Object.keys(setupCategories).map((category) => (
              <th key={category} className="border border-gray-300 p-2 text-left">
                {category}
              </th>
            ))}
            <th className="border border-gray-300 p-2 text-left">Other</th>
          </tr>
        </thead>
        <tbody>
          {sortedMonths.map((month) => (
            <tr key={month} className="even:bg-gray-50">
              <td className="border border-gray-300 p-2 font-medium">{month}</td>
              {Object.keys(setupCategories).map((category) => (
                <td key={category} className="border border-gray-300 p-2 text-center">
                  {categoryCountsByMonth[month]?.[category] || 0}
                </td>
              ))}
              <td className="border border-gray-300 p-2 text-center">
                {categoryCountsByMonth[month]?.['Other'] || 0}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TradeKPI;
