"use client";
import React, { useEffect, useState } from "react";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table"; // Adjust path if needed

// Types for position and order
type Position = {
  Symbol: string;
  Account: string;
  AvgCost: number;
  Currency: string;
  Position: number;
};

type Order = {
  Action: string;
  AuxPrice: number;
  LmtPrice: number;
  OrderId: number;
  OrderType: string;
  Symbol: string;
  TotalQty: number;
};

type PortfolioData = {
  positions: Position[];
  orders: Order[];
};

export default function PortfolioTable() {
  const [positions, setPositions] = useState<Position[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null); // Symbol for the selected row
  const [isModalOpen, setIsModalOpen] = useState(false); // Track modal open state

  // Fetch both positions and orders from the API at once
  useEffect(() => {
    const fetchPortfolioData = async () => {
      try {
        const res = await fetch("http://localhost:8080/api/ib_portfoliodata");
        if (!res.ok) throw new Error("Failed to fetch portfolio data");
        const data: PortfolioData = await res.json();
        setPositions(data.positions); // Assuming positions are in the "positions" field
        setOrders(data.orders); // Assuming orders are in the "orders" field
      } catch (err: any) {
        setError(err.message || "An error occurred");
      } finally {
        setLoading(false);
      }
    };

    fetchPortfolioData();
  }, []);

  if (loading) return <div className="text-xs">Loading...</div>;
  if (error) return <div className="text-xs text-red-500">Error: {error}</div>;

  // Filter open orders for the selected symbol
  const filteredOrders = orders.filter(
    (order) => order.Symbol === selectedSymbol
  );

  // Handle modal open/close
  const openModal = (symbol: string) => {
    setIsModalOpen(true);
    setSelectedSymbol(symbol); // Set the symbol for the modal
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedSymbol(null); // Close the modal and reset the selected symbol
  };

  return (
    <div>
      {/* Positions Table */}
      <div className="max-h-60 overflow-y-auto border rounded-md mb-4">
        <Table className="text-xs">
          <TableHeader>
            <TableRow>
              <TableHead>Symbol</TableHead>
              <TableHead>Account</TableHead>
              <TableHead>Position</TableHead>
              <TableHead>Avg Cost</TableHead>
              <TableHead>Currency</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {positions.map((pos) => {
              // Check if the current position has any open orders
              const hasOpenOrders = orders.some(
                (order) => order.Symbol === pos.Symbol
              );
              return (
                <TableRow
                  key={pos.Symbol}
                  onClick={() => openModal(pos.Symbol)} // Open the modal for this symbol
                  className="cursor-pointer hover:bg-gray-100"
                >
                  <TableCell>
                    {hasOpenOrders ? ">" : ""} {/* Display ">" if the position has open orders */}
                    {pos.Symbol}
                  </TableCell>
                  <TableCell>{pos.Account}</TableCell>
                  <TableCell>{pos.Position}</TableCell>
                  <TableCell>{Number(pos.AvgCost).toFixed(2)}</TableCell>
                  <TableCell>{pos.Currency}</TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>

      {/* Modal for Open Orders */}
      {isModalOpen && selectedSymbol && (
        <div
          className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50"
          onClick={closeModal}
        >
          <div
            className="bg-white p-4 w-full sm:w-3/4 md:w-1/2 lg:w-1/3 xl:w-1/3 2xl:w-1/4 max-w-full"
            onClick={(e) => e.stopPropagation()} // Prevent closing the modal when clicking inside it
          >
            <div className="flex justify-between items-center mb-2">
              <h3 className="text-lg font-semibold">Open Orders for {selectedSymbol}</h3>
              <button
                onClick={closeModal}
                className="text-gray-600 hover:text-gray-900"
              >
                X
              </button>
            </div>
            <div className="overflow-y-auto border rounded-md">
              <Table className="text-xs">
                <TableHeader>
                  <TableRow>
                    <TableHead>Action</TableHead>
                    <TableHead>Order ID</TableHead>
                    <TableHead>Symbol</TableHead>
                    <TableHead>Total Qty</TableHead>
                    <TableHead>Order Type</TableHead>
                    <TableHead>Limit Price</TableHead>
                    <TableHead>Aux Price</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredOrders.length > 0 ? (
                    filteredOrders.map((order) => (
                      <TableRow key={order.OrderId}>
                        <TableCell>{order.Action}</TableCell>
                        <TableCell>{order.OrderId}</TableCell>
                        <TableCell>{order.Symbol}</TableCell>
                        <TableCell>{order.TotalQty}</TableCell>
                        <TableCell>{order.OrderType}</TableCell>
                        <TableCell>{Number(order.LmtPrice).toFixed(2)}</TableCell>
                        <TableCell>{Number(order.AuxPrice).toFixed(2)}</TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center text-xs text-gray-500">
                        No open orders for this symbol.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
