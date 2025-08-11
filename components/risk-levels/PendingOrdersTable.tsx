"use client";

import React, { useState, useEffect } from "react";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";

type Order_Alpaca = {
  symbol: string;
  latest_price: number;
  limit_price: number | null;
  stop_price: number | null;
  risk: number;
  tier_1: number;
  tier_2: number;
  tier_3: number;
  tier_4: number;
};

interface PendingOrdersTableProps {
  selectedOrder: Order_Alpaca | null;
  selectedTierValue: number | null;
}

const PendingOrdersTable: React.FC<PendingOrdersTableProps> = ({
  selectedOrder,
  selectedTierValue,
}) => {
  const [entryPrice, setEntryPrice] = useState<number | null>(null);
  const [lastTier, setLastTier] = useState<number | null>(null);
  const [calculatedRisk, setCalculatedRisk] = useState<number | null>(null);

  useEffect(() => {
    if (selectedOrder) {
      setEntryPrice(null);
      setLastTier(selectedTierValue);
      setCalculatedRisk(null);
    }
  }, [selectedOrder]);
  
  useEffect(() => {
    if (selectedTierValue !== lastTier) {
      setEntryPrice(null);
      setLastTier(selectedTierValue);
      setCalculatedRisk(null);
    }
  }, [selectedTierValue, lastTier]);
  
  useEffect(() => {
    if (!selectedOrder) {
      setCalculatedRisk(null);
      return;
    }
  
    const price = entryPrice !== null ? entryPrice : selectedOrder.latest_price;
  
    const riskLevel =
      selectedOrder.stop_price !== null && selectedOrder.stop_price !== 0
        ? selectedOrder.stop_price
        : selectedOrder.limit_price;
  
    const size = selectedTierValue;
  
    if (price !== null && riskLevel !== null && size !== null) {
      const risk = Math.abs((price - riskLevel) * size);
      setCalculatedRisk(Number(risk.toFixed(2)));
    } else {
      setCalculatedRisk(null);
    }
  }, [entryPrice, selectedOrder, selectedTierValue]);

  const handleSendOrder = async (order: Order_Alpaca) => {
    const priceToUse = entryPrice !== null ? entryPrice : order.latest_price;

    const requestBody = {
      symbol: order.symbol,
      entry_price: priceToUse,
      lmt_price: order.limit_price,
      stp_price: order.stop_price,
      position_size: selectedTierValue,
    };

    try {
      console.log("Sending Order:", JSON.stringify(requestBody, null, 2));
      const response = await fetch("http://localhost:8080/api/place-order", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      });

      if (response.ok) {
        const data = await response.json();
        console.log("Order sent successfully!", data);
      } else {
        const error = await response.json();
        console.error("Error:", error.message);
      }
    } catch (err) {
      console.error("Error sending order:", err);
    }
  };

  if (!selectedOrder) return null;

  return (
    <div className="w-full max-w-4xl mx-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Symbol</TableHead>
            <TableHead>Entry Price</TableHead>
            {selectedOrder.limit_price !== 0 && selectedOrder.limit_price !== null && (
              <TableHead>Stop price</TableHead>
            )}
            {selectedOrder.stop_price !== 0 && selectedOrder.stop_price !== null && (
              <TableHead>Stop price</TableHead>
            )}
            {selectedTierValue !== 0 && selectedTierValue !== null && (
              <TableHead>Position Size</TableHead>
            )}
            <TableHead>Action</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell>{selectedOrder.symbol}</TableCell>
            <TableCell>
              <input
                type="number"
                className="border px-2 py-1 w-24 rounded text-sm"
                value={
                  entryPrice !== null ? entryPrice : selectedOrder.latest_price
                }
                onChange={(e) =>
                  setEntryPrice(
                    e.target.value === "" ? null : parseFloat(e.target.value)
                  )
                }
              />
            </TableCell>
            {selectedOrder.limit_price !== 0 && selectedOrder.limit_price !== null && (
              <TableCell>{selectedOrder.limit_price}</TableCell>
            )}
            {selectedOrder.stop_price !== 0 && selectedOrder.stop_price !== null && (
              <TableCell>{selectedOrder.stop_price}</TableCell>
            )}
            {selectedTierValue !== 0 && selectedTierValue !== null && (
              <TableCell>{selectedTierValue}</TableCell>
            )}
            <TableCell className="space-y-1">
              <Button
                variant="secondary"
                size="sm"
                className="bg-blue-500 hover:bg-blue-600 text-white font-medium px-3 py-1 rounded shadow-md"
                onClick={() => handleSendOrder(selectedOrder)}
              >
                Send
              </Button>
              {calculatedRisk !== null && (
                <div className="text-xs text-gray-600 mt-1">
                  Risk: <span className="font-semibold">${calculatedRisk}</span>
                </div>
              )}
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </div>
  );
};

export default PendingOrdersTable;