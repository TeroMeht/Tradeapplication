'use client';

import * as React from "react";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";

type ScannerRow = {
  symbol: string;
  rank: number | null;
};

type ScannerTableProps = {
  title?: string;
  endpoint: string;
  fetchTrigger?: boolean;      // triggers fetch when true
  onFetched?: () => void;
};

const ScannerTable: React.FC<ScannerTableProps> = ({
  title = "IB Scanner Results",
  endpoint,
  fetchTrigger = false,
  onFetched,
}) => {
  const [data, setData] = React.useState<ScannerRow[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

const fetchData = React.useCallback(async () => {
  setLoading(true);
  setError(null);
  try {
    const url = endpoint.startsWith("http")
      ? endpoint
      : `http://127.0.0.1:8080${endpoint}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to fetch scanner data");
    const json = await res.json();
    const rows: ScannerRow[] = (json.results as ScannerRow[] || []).filter(
      (row) => row.symbol
    );
    setData(rows);
    onFetched?.();
  } catch (err: unknown) {
    if (err instanceof Error) setError(err.message);
    else setError(String(err));
  } finally {
    setLoading(false);
  }
}, [endpoint, onFetched]); // include dependencies used inside fetchData

React.useEffect(() => {
  if (fetchTrigger) fetchData();
}, [fetchTrigger, fetchData]);

  const displayedColumns = ["rank", "symbol"];

  return (
    <div
      className={`border rounded-md p-2 bg-white shadow-sm w-full max-w-xs transition-colors duration-300 ${
        loading ? "bg-blue-50 animate-pulse" : ""
      }`} // flash while loading
    >
      <h3 className="text-sm font-semibold mb-1">{title}</h3>

      {error && <p className="text-red-500 text-xs mb-1">{error}</p>}

      <div className="overflow-y-auto max-h-80">
        <Table className="table-auto text-xs">
          <TableHeader>
            <TableRow>
              {displayedColumns.map((col) => (
                <TableHead key={col}>{col.toUpperCase()}</TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.length === 0 && !loading && (
              <TableRow>
                <TableCell colSpan={displayedColumns.length} className="text-center text-xs">
                  No data
                </TableCell>
              </TableRow>
            )}
            {data.map((row, idx) => (
              <TableRow key={idx}>
                {displayedColumns.map((col) => (
                  <TableCell key={col} className="text-xs">
                    {String(row[col as keyof ScannerRow] ?? "-")}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
};

export default ScannerTable;
