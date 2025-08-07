"use client"
import React, { useEffect, useState } from "react";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";

type Alarm = {
  id: number;
  Message: string;
  Status: string;
  Date: string;
};

export default function PortfolioAlarmsTable() {
  const [alarms, setAlarms] = useState<Alarm[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch alarms from the API
  useEffect(() => {
    const fetchAlarms = async () => {
      try {
        const res = await fetch("http://localhost:8080/api/pcs_alarms"); // Adjust if needed
        if (!res.ok) throw new Error("Failed to fetch alarms");
        const data = await res.json();
        setAlarms(data);
      } catch (err: any) {
        setError(err.message || "An error occurred");
      } finally {
        setLoading(false);
      }
    };

    fetchAlarms();
  }, []);

  if (loading) return <div className="text-xs">Loading...</div>;
  if (error) return <div className="text-xs text-red-500">Error: {error}</div>;

  return (
    <div className="w-full overflow-y-auto border rounded-md">
      <Table className="text-xs">
        <TableHeader>
          <TableRow>
            <TableHead>ID</TableHead>
            <TableHead>Message</TableHead>
            <TableHead>Timestamp</TableHead>
            <TableHead>Status</TableHead>
            {/* Removed Actions column */}
          </TableRow>
        </TableHeader>
        <TableBody>
          {alarms.map((alarm) => (
            <TableRow key={alarm.id}>
              <TableCell>{alarm.id}</TableCell>
              <TableCell>{alarm.Message}</TableCell>
              <TableCell>{new Date(alarm.Date).toLocaleString()}</TableCell>
              <TableCell
                className={alarm.Status === "active" ? "text-red-500" : ""}
              >
                {alarm.Status}
              </TableCell>
              {/* Removed the Acknowledge button */}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
