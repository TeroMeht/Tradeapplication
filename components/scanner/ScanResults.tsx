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
import { Button } from "@/components/ui/button";

const ScannerTable = () => {
  const [data, setData] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [endTime, setEndTime] = React.useState<string | null>(null);

  const fetchedRef = React.useRef(false); // track if fetch already happened

  const columns = [
    "Symbol",
    "Close",
    "Last",
    "% Change",
    "Mean_Rvol",
    "Start_Time",
    "Cumulative_Volume",
  ];

  const fetchData = React.useCallback(async () => {
    if (fetchedRef.current) return; // prevent double fetch
    fetchedRef.current = true;

    setLoading(true);
    setError(null);
    try {
      const res = await fetch("http://localhost:8080/api/ib_scanner");
      if (!res.ok) throw new Error("Failed to fetch scanner data");
      const json = await res.json();

      const orderedData = json.map((row: any) => {
        const newRow: Record<string, any> = {};
        columns.forEach((col) => {
          newRow[col] = row[col] ?? row[col.replace("_", "")] ?? "-";
        });
        return newRow;
      });

      setData(orderedData);

      if (json.length > 0) {
        setEndTime(json[0].End_Time ?? null);
      }
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
      else setError("Unknown error");
    } finally {
      setLoading(false);
    }
  }, [columns]);

  React.useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) return <p>Loading scanner data...</p>;
  if (error) return <p>Error: {error}</p>;
  if (data.length === 0) return <p>No scanner data available.</p>;

  return (
    <section className="home">
      <div className="home-content">
        <div className="flex justify-end mb-4">
          <Button
            onClick={() => {
              fetchedRef.current = false; // allow manual refresh
              fetchData();
            }}
            variant="outline"
          >
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
                      ["Close", "Last", "% Change", "Mean_Rvol", "Cumulative_Volume"].includes(
                        col
                      );

                    let cellClass = "";

                    if (isPercentChange && typeof value === "number") {
                      cellClass =
                        value > 0
                          ? "bg-green-200 text-green-900 font-semibold"
                          : value < 0
                          ? "bg-red-200 text-red-900 font-semibold"
                          : "";
                    }

                    if (isNumeric) {
                      cellClass += " text-right";
                    }

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
