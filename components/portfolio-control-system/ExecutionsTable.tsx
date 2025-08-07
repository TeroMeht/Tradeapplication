"use client";

import React, { useEffect, useState } from "react";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";

type AggregatedExecution = {
  Symbol: string;
  Time: string;
  AdjustedAvgPrice: number;
  Shares: number;
  Side: string;
  PermId: number;
  OpensPosition: boolean; // <-- Add this
};

export default function ExecutionsTable() {
  const [executions, setExecutions] = useState<AggregatedExecution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showTodayOnly, setShowTodayOnly] = useState(false);

  useEffect(() => {
    const fetchExecutions = async () => {
      try {
        const res = await fetch("http://localhost:8080/api/executions");
        if (!res.ok) throw new Error("Failed to fetch executions");
        const data = await res.json();
        setExecutions(data.reverse());
      } catch (err: any) {
        setError(err.message || "An error occurred");
      } finally {
        setLoading(false);
      }
    };

    fetchExecutions();
  }, []);

  const isToday = (dateString: string) => {
    const date = new Date(dateString);
    const today = new Date();
    return (
      date.getDate() === today.getDate() &&
      date.getMonth() === today.getMonth() &&
      date.getFullYear() === today.getFullYear()
    );
  };

  const filteredExecutions = showTodayOnly
    ? executions.filter((exec) => isToday(exec.Time))
    : executions;

  if (loading) return <div className="text-xs">Loading...</div>;
  if (error) return <div className="text-xs text-red-500">Error: {error}</div>;

  return (
    <div className="w-full border rounded-md">
      <div className="flex justify-end p-2">
        <Button
          size="sm"
          variant={showTodayOnly ? "default" : "outline"}
          onClick={() => setShowTodayOnly((prev) => !prev)}
        >
          {showTodayOnly ? "Show All" : "Show Today"}
        </Button>
      </div>

      <div className="w-full h-full border-t rounded-md flex flex-col">
        <Table className="text-xs w-full">
          <TableHeader>
            <TableRow>
              <TableHead>Symbol</TableHead>
              <TableHead>Time</TableHead>
              <TableHead>Adjusted Avg Price</TableHead>
              <TableHead>Shares</TableHead>
              <TableHead>Side</TableHead>
              <TableHead>Opens Position</TableHead> {/* New column */}
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredExecutions.map((exec, index) => (
              <TableRow
                key={`${exec.PermId}-${index}`} // Ensures unique key even if PermId repeats
                className={exec.Side === "BOT" ? "bg-blue-100" : ""}
              >
                <TableCell>{exec.Symbol}</TableCell>
                <TableCell>{new Date(exec.Time).toLocaleString()}</TableCell>
                <TableCell>{Number(exec.AdjustedAvgPrice).toFixed(2)}</TableCell>
                <TableCell>{exec.Shares}</TableCell>
                <TableCell>{exec.Side}</TableCell>
                <TableCell>{exec.OpensPosition ? "✅" : "—"}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
