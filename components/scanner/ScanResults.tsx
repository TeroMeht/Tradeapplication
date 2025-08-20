"use client";

import * as React from "react";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  TableCaption,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button"; // shadcn/ui button

const ScannerTable = () => {
  const [data, setData] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [endTime, setEndTime] = React.useState<string | null>(null);

  const columns = [
    "Symbol",
    "Close",
    "Last",
    "% Change",
    "Mean_Rvol",
    "Start_Time",
    "Cumulative_Volume",
  ];

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("http://localhost:8080/api/ib_scanner");
      if (!res.ok) throw new Error("Failed to fetch scanner data");
      const json = await res.json();

      // Reorder object keys according to columns + keep End_Time separately
      const orderedData = json.map((row: any) => {
        const newRow: Record<string, any> = {};
        columns.forEach((col) => {
          newRow[col] = row[col] ?? row[col.replace("_", "")] ?? "-";
        });
        return newRow;
      });

      setData(orderedData);

      // Take End_Time (from first row for now)
      if (json.length > 0) {
        setEndTime(json[0].End_Time ?? null);
      }
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
      else setError("Unknown error");
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    fetchData();
  }, []);

  if (loading) return <p>Loading scanner data...</p>;
  if (error) return <p>Error: {error}</p>;
  if (data.length === 0) return <p>No scanner data available.</p>;

  return (
    <section className="home">
      <div className="home-content">

        {/* Refresh button */}
        <div className="flex justify-end mb-4">
          <Button onClick={fetchData} variant="outline">
            Refresh Data
          </Button>
        </div>

        <div className="mt-6">
          <Table>
            <TableCaption>
              IB Hot by Volume Scanner {endTime ? `(Last update: ${endTime})` : ""}
            </TableCaption>
            <TableHeader>
              <TableRow>
                {columns.map((col) => (
                  <TableHead key={col}>{col}</TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((row, idx) => (
                <TableRow key={idx}>
                  {columns.map((col) => {
                    const value = row[col];
                    const isPercentChange = col === "% Change";
                    const isMeanRvol = col === "Mean_Rvol";
                    const isNumeric =
                      ["Close", "Last", "% Change", "Mean_Rvol", "Cumulative_Volume"].includes(col);

                    let cellClass = "";

                    // Conditional styling for % Change
                    if (isPercentChange && typeof value === "number") {
                      cellClass =
                        value > 0
                          ? "bg-green-200 text-green-900 font-semibold"
                          : value < 0
                          ? "bg-red-200 text-red-900 font-semibold"
                          : "";
                    }

                    // Right-align numeric values
                    if (isNumeric) {
                      cellClass += " text-right";
                    }

                    // Conditional styling for Mean_Rvol
                    const style: React.CSSProperties = {};
                    if (isMeanRvol && typeof value === "number") {
                      const darkness = Math.min(1, (value - 1.5) / 5);
                      style.backgroundColor = `rgba(253, 230, 138, ${darkness})`;
                    }

                    return (
                      <TableCell key={col} className={cellClass.trim()} style={style}>
                        {value as React.ReactNode}
                      </TableCell>
                    );
                  })}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    </section>
  );
};

export default ScannerTable;
