import React, { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Loader2 } from "lucide-react";

interface TableResponse {
  tables: string[];
}

const TablesList: React.FC = () => {
  const [tables, setTables] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTables = async () => {
    try {
      const response = await fetch("http://127.0.0.1:8080/api/tables");
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data: TableResponse = await response.json();
      const upperTables = data.tables.map((t) => t.toUpperCase());
      setTables(upperTables);
        setError(null); // Clear any previous error
    } catch (err: unknown) {
        if (err instanceof Error) {
        setError(err.message);
        } else {
        setError(String(err));
        }
    } finally {
        setLoading(false);
    }
    };

  useEffect(() => {
    fetchTables();
    const intervalId = setInterval(fetchTables, 10000);
    return () => clearInterval(intervalId);
  }, []);

  if (loading)
    return (
      <div className="flex items-center justify-center h-48">
        <Loader2 className="animate-spin w-6 h-6 text-gray-500" />
        <span className="ml-2 text-gray-600">Loading tables...</span>
      </div>
    );

  if (error)
    return (
      <div className="text-red-500 text-center p-4">
        ❌ Failed to load tables: {error}
      </div>
    );

  const getFontSize = (name: string) => {
    if (name.length <= 5) return "1rem";
    if (name.length <= 8) return "1rem";
    if (name.length <= 12) return "1rem";
    return "0.75rem";
  };

  return (
    <div className="p-3">
      <h2 className="text-xl font-semibold mb-4 text-gray-800 flex items-center justify-between">
        <span>LiveStreaming</span>
        <span className="text-gray-600 text-sm">{tables.length} tickers</span>
      </h2>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
        {tables.map((table) => (
          <Card
            key={table}
            className="cursor-pointer hover:scale-80 transition-transform flex items-center justify-center bg-green-100"
          >
            <CardContent
              className="text-center font-semibold text-gray-700 uppercase break-words"
              style={{ fontSize: getFontSize(table) }}
            >
              {table}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default TablesList;
