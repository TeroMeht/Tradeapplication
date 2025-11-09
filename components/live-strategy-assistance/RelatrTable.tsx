'use client';

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

type LastRow = Record<string, string | number>;

export const LastRowsTable: React.FC = () => {
  const [data, setData] = React.useState<LastRow[]>([]);
  const [error, setError] = React.useState<string | null>(null);

  const fetchData = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8080/api/tables/last_rows");
      if (!res.ok) throw new Error("Failed to fetch table data");
      const json = await res.json();

      // Convert object to array and sort by Relatr descending
      const rows: LastRow[] = Object.values(json.last_rows || []).filter(Boolean) as LastRow[];
      rows.sort((a, b) => (b.Relatr as number) - (a.Relatr as number));

      setData(rows);
            setError(null); // Clear any previous error
        } catch (err: unknown) {
            if (err instanceof Error) {
            setError(err.message);
            } else {
            setError(String(err));
            }

        }
        };


  React.useEffect(() => {
    // Initial fetch in the background
    fetchData();

    // Fetch every 10 seconds
    const intervalId = setInterval(fetchData, 10000);

    return () => clearInterval(intervalId);
  }, []);

  const displayedColumns = ["Symbol", "Time", "Relatr", "Rvol"];

  return (
    <>
      {error && <p className="text-red-500">Error: {error}</p>}
      <Table className="mt-4">
        <TableCaption>Last rows of all tables (sorted by Relatr ↓)</TableCaption>
        <TableHeader>
          <TableRow>
            {displayedColumns.map((col) => (
              <TableHead key={col}>{col}</TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((row, idx) => (
            <TableRow key={idx}>
              {displayedColumns.map((col) => (
                <TableCell key={col}>
                  {row[col] !== undefined ? row[col] : "-"}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </>
  );
};

export default LastRowsTable;
