"use client";

import React from "react";
import { Bar } from "react-chartjs-2";
import { format } from "date-fns";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

interface Trade {
  Symbol: string;
  Date: string;   // e.g., "2025-08-13"
  Setup: string;
  Rating: string; // not used here, but kept for type completeness
}

interface SetupBarChartProps {
  currentMonth: Date;
  trades: Trade[]; // Passed in from parent
}

const ALL_SETUPS = [
  "No setup",
  "Parabolic short",
  "ORB",
  "Extreme Reversal",
  "Reversal",
  "VWAP continuation",
  "Reversal short",
  "Swing trade",
  "Other"
];

const SetupBarChart: React.FC<SetupBarChartProps> = ({ currentMonth, trades }) => {
  const monthStart = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), 1);
  const monthEnd = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 0);

  // Count setups for this month
  const counts: Record<string, number> = {};
  trades.forEach((trade) => {
    const tradeDate = new Date(trade.Date);
    if (tradeDate >= monthStart && tradeDate <= monthEnd) {
      counts[trade.Setup] = (counts[trade.Setup] || 0) + 1;
    }
  });

  // Fill in missing setups with 0
  const fullCounts: Record<string, number> = {};
  ALL_SETUPS.forEach((setup) => {
    fullCounts[setup] = counts[setup] || 0;
  });

  const labels = ALL_SETUPS;
  const dataValues = labels.map((setup) => fullCounts[setup]);
  const totalCount = dataValues.reduce((sum, val) => sum + val, 0);

  const chartData = {
    labels,
    datasets: [
      {
        label: "Setups Count",
        data: dataValues,
        backgroundColor: "rgba(53, 162, 235, 0.5)",
      },
    ],
  };

  return (
    <div className="max-w-3xl mx-auto p-4 bg-white rounded-xl shadow">
      <h3 className="text-lg font-semibold mb-4">
        Setups for {format(currentMonth, "MMMM yyyy")}
      </h3>
      {totalCount === 0 ? (
        <p>No setups found for this month.</p>
      ) : (
        <>
          <p className="mb-4 text-right font-semibold text-gray-700">
            Total Setups: <span className="text-blue-600">{totalCount}</span>
          </p>
          <Bar data={chartData} />
        </>
      )}
    </div>
  );
};

export default SetupBarChart;
