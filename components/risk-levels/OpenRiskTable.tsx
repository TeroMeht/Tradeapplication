"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

type OpenRiskLevel = {
  OrderId: string;
  Symbol: string;
  AuxPrice: number;
  AvgCost: number;
  OpenRisk: number;
  Position: number;
};

const fetchOpenRiskLevels = async (): Promise<OpenRiskLevel[]> => {
  try {
    const response = await fetch("http://localhost:8080/api/ib-positions");

    if (!response.ok) {
      const errorBody = await response.json();
    }

    const data = await response.json();
    return data.openRiskLevels as OpenRiskLevel[];
  } catch (error) {
    console.error("Error fetching open risk levels:", error);
    throw error;
  }
};

const OpenRiskTable = () => {
  const [openRiskLevels, setOpenRiskLevels] = useState<OpenRiskLevel[]>([]);
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);  // Track loading state
  const hasFetched = useRef(false);

  const updateTable = useCallback(async () => {
    if (isLoading) return; 
    setIsLoading(true);
  
    try {
      const data = await fetchOpenRiskLevels();
      if (data.length === 0) {
        setMessage("");
      } else {
        setMessage("");
      }
      setOpenRiskLevels(data);
    } catch (error: unknown) {
      if (error instanceof Error) {
        setMessage(error.message);
      } else {
        setMessage("Error loading data");
      }
      setOpenRiskLevels([]);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading]);

  // ✅ Fetch once on mount
  useEffect(() => {
    if (!hasFetched.current) {
      hasFetched.current = true;
      updateTable();
    }
  }, [updateTable]);


  return (
    <div>
      <div className="text-center text-xl font-bold my-4">Position management</div>

      <Table>
        <TableHeader className="bg-[#f9fafb]">
          <TableRow>
            <TableHead>#</TableHead>
            <TableHead>OrderId</TableHead>
            <TableHead>Symbol</TableHead>
            <TableHead>Aux Price</TableHead>
            <TableHead>Avg Cost</TableHead>
            <TableHead>Position</TableHead>
            <TableHead>Open Risk</TableHead>        
            <TableHead>Actions</TableHead> {/* New column */}
          </TableRow>
        </TableHeader>
        <TableBody>
          {openRiskLevels.length === 0 ? (
            <TableRow>
              <TableCell colSpan={7} className="text-center text-gray-500">
                {message || "No data available."}
              </TableCell>
            </TableRow>
          ) : (
            openRiskLevels.map((riskLevel, index) => (
              <TableRow key={index} className="hover:bg-gray-100">
                <TableCell>{index + 1}</TableCell>
                <TableCell>{riskLevel.OrderId}</TableCell>
                <TableCell>{riskLevel.Symbol}</TableCell>
                <TableCell>{riskLevel.AuxPrice != null ? riskLevel.AuxPrice.toFixed(2) : "N/A"}</TableCell>
                <TableCell>{riskLevel.AvgCost.toFixed(2)}</TableCell>
                <TableCell>{riskLevel.Position}</TableCell>
                <TableCell
                  style={{
                    fontWeight: 'bold',
                    color:
                      typeof riskLevel.OpenRisk !== 'number' ||
                      !isFinite(riskLevel.OpenRisk)
                        ? 'red'
                        : undefined,
                  }}
                >
                  {typeof riskLevel.OpenRisk === 'number' && isFinite(riskLevel.OpenRisk)
                    ? riskLevel.OpenRisk.toFixed(2)
                    : 'Sulla ei ole stoppia'}
                </TableCell>
                <TableCell>
                <button
                  onClick={() => {
                    const url = `/risk-levels/${riskLevel.Symbol}/manage` +
                      `?symbol=${encodeURIComponent(riskLevel.Symbol)}` +
                      `&aux=${encodeURIComponent(riskLevel.AuxPrice)}` +
                      `&orderid=${encodeURIComponent(riskLevel.OrderId)}` +
                      `&avg=${encodeURIComponent(riskLevel.AvgCost)}` +
                      `&pos=${encodeURIComponent(riskLevel.Position)}` +
                      `&risk=${encodeURIComponent(riskLevel.OpenRisk)}`;

                    window.open(url, "_blank", "width=500,height=600,left=200,top=200");
                  }}
                  className="bg-indigo-500 text-white px-3 py-1 rounded hover:bg-indigo-600"
                >
                  Manage
                </button>
              </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
      {/* Update Button */}
      <div className="text-center mb-4">
        <button
          onClick={updateTable}
          disabled={isLoading}  // Disable button if data is loading
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
        >
          {isLoading ? "Loading..." : "Update Data"}
        </button>
      </div>
    </div>
  );
};

export default OpenRiskTable;
