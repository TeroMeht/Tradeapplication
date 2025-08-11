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
import { Button } from "@/components/ui/button";

type Order_Alpaca = {
  symbol: string;
  latest_price: number;
  limit_price: number | null;
  stop_price: number | null;
  risk: number;
  tier_1: number;
};

type ApiResponse = {
  status: string;
  message: string;
  data: Order_Alpaca[];
};

const fetchPositions = async (): Promise<ApiResponse> => {
  const res = await fetch("http://localhost:8080/api/openorders");
  const json = await res.json();
  return json as ApiResponse;
};

const PositionTable = ({ onComplete }: { onComplete: () => void }) => {
  const [positions, setPositions] = useState<Order_Alpaca[]>([]);
  const [message, setMessage] = useState("");
  const [sentOrders, setSentOrders] = useState<Set<number>>(new Set());
  const hasFetched = useRef(false);

  const updateTable = useCallback(async () => {
    try {
      const response = await fetchPositions();

      if (response.status === "success") {
        const positions = Array.isArray(response.data) ? response.data : [];
        setPositions(positions);
        setMessage(positions.length === 0 ? `${response.status}: ${response.message}` : "");
        setSentOrders(new Set()); // reset sent state on refresh
      } else {
        console.error("API returned error status:", response);
        setPositions([]);
        setMessage(response.message || "API error: Unexpected response.");
      }
    } catch (err) {
      console.error("Fetch error:", err);
      setPositions([]);
      const errorMessage =
        err instanceof Error
          ? err.message
          : typeof err === "string"
          ? err
          : "Error loading data. Please try again.";
      setMessage(`Fetch error: ${errorMessage}`);
    } finally {
      onComplete();
    }
  }, [onComplete]);

  useEffect(() => {
    if (!hasFetched.current) {
      hasFetched.current = true;
      updateTable();
    }
  }, [updateTable]);

  const handleSendOrder = async (order: Order_Alpaca, index: number) => {
    if (sentOrders.has(index)) return; // already sent

    const requestBody = {
      symbol: order.symbol,
      entry_price: order.latest_price,
      lmt_price: order.limit_price,
      stp_price: order.stop_price,
      position_size: order.tier_1,
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
        setSentOrders((prev) => new Set(prev).add(index)); // mark as sent
      } else {
        const error = await response.json();
        console.error("Error:", error.message);
      }
    } catch (err) {
      console.error("Error sending order:", err);
    }
  };

  return (
    <div>
      <div className="text-center text-xl font-bold my-4">Open Alpaca Orders</div>

      <Table>
        <TableHeader className="bg-[#f9fafb]">
          <TableRow>
            <TableHead>#</TableHead>
            <TableHead>Symbol</TableHead>
            <TableHead>Latest Price</TableHead>
            <TableHead>Stop price</TableHead>
            <TableHead>Risk</TableHead>
            <TableHead>Position size</TableHead>
            <TableHead>Action</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {positions.length === 0 ? (
            <TableRow>
              <TableCell colSpan={7} className="text-center text-lg text-gray-500">
                {message || "No orders to display."}
              </TableCell>
            </TableRow>
          ) : (
            positions.map((position, index) => {
              const stopValue =
                (position.limit_price ?? 0) > 0
                  ? position.limit_price
                  : (position.stop_price ?? 0) > 0
                  ? position.stop_price
                  : 0;

              const isSent = sentOrders.has(index);

              return (
                <TableRow key={index} className="cursor-pointer hover:bg-gray-100">
                  <TableCell>{index + 1}</TableCell>
                  <TableCell>{position.symbol}</TableCell>
                  <TableCell>{position.latest_price}</TableCell>
                  <TableCell>{stopValue}</TableCell>
                  <TableCell>{position.risk}</TableCell>
                  <TableCell>{position.tier_1}</TableCell>
                  <TableCell>
                    <Button
                      variant="secondary"
                      size="sm"
                      className={isSent ? "bg-gray-400 text-white" : "bg-blue-500 hover:bg-blue-600 text-white"}
                      disabled={isSent}
                      onClick={() => handleSendOrder(position, index)}
                    >
                      {isSent ? "Sent" : "Send"}
                    </Button>
                  </TableCell>
                </TableRow>
              );
            })
          )}
        </TableBody>
      </Table>

      <div className="flex justify-center my-4">
        <button
          onClick={updateTable}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
        >
          Update Table
        </button>
      </div>
    </div>
  );
};

export default PositionTable;
