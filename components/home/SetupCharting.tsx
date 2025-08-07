import React, { useEffect, useState } from "react";
import { Bar } from "react-chartjs-2";
import { format, startOfMonth, endOfMonth, parseISO } from "date-fns";
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

interface Execution {
  Symbol: string;
  Time: string;
  Date: string;
  Setup: string;  // Make sure your API returns this field
}

interface SetupBarChartProps {
  currentMonth: Date;
}

const ALL_SETUPS = [
  "No setup",
  "Parabolic short",
  "ORB",
  "Episodic Pivot",
  "Extreme Reversal",
  "Reversal",
  // add more setups if needed
];

const SetupBarChart: React.FC<SetupBarChartProps> = ({ currentMonth }) => {
  const [data, setData] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const response = await fetch("http://localhost:8080/api/trades");
        const executions: Execution[] = await response.json();

        const monthStart = startOfMonth(currentMonth);
        const monthEnd = endOfMonth(currentMonth);

        const counts: Record<string, number> = {};

        executions.forEach((exec) => {
          const execDate = parseISO(exec.Date);
          if (execDate >= monthStart && execDate <= monthEnd) {
            counts[exec.Setup] = (counts[exec.Setup] || 0) + 1;
          }
        });

        const fullCounts: Record<string, number> = {};
        ALL_SETUPS.forEach((setup) => {
          fullCounts[setup] = counts[setup] || 0;
        });

        setData(fullCounts);
      } catch (error) {
        console.error("Failed to fetch setup data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [currentMonth]);

  const labels = ALL_SETUPS;
  const counts = labels.map((setup) => data[setup] || 0);

  // Calculate total count
  const totalCount = counts.reduce((sum, val) => sum + val, 0);

  const chartData = {
    labels,
    datasets: [
      {
        label: "Setups Count",
        data: counts,
        backgroundColor: "rgba(53, 162, 235, 0.5)",
      },
    ],
  };

  return (
    <div className="max-w-3xl mx-auto p-4 bg-white rounded-xl shadow">
      <h3 className="text-lg font-semibold mb-4">
        Setups for {format(currentMonth, "MMMM yyyy")}
      </h3>
      {loading ? (
        <p>Loading...</p>
      ) : labels.length === 0 ? (
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
