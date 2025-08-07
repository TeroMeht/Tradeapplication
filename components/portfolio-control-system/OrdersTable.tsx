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

type Order = {
  Action: string;
  AuxPrice: number;
  LmtPrice: number;
  OrderId: number;
  OrderType: string;
  Symbol: string;
  TotalQty: number;
};

export default function OrdersTable() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchOrders = async () => {
      try {
        const res = await fetch("http://localhost:8080/api/ib_portfoliodata");
        if (!res.ok) throw new Error("Failed to fetch orders");
        const data = await res.json();
        setOrders(data.orders); // Assuming orders are in the "orders" field
      } catch (err: any) {
        setError(err.message || "An error occurred");
      } finally {
        setLoading(false);
      }
    };

    fetchOrders();
  }, []);

  if (loading) return <div className="text-xs">Loading...</div>;
  if (error) return <div className="text-xs text-red-500">Error: {error}</div>;

  return (
    <div className="max-h-60 overflow-y-auto border rounded-md">
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
          {orders.map((order) => (
            <TableRow key={order.OrderId}>
              <TableCell>{order.Action}</TableCell>
              <TableCell>{order.OrderId}</TableCell>
              <TableCell>{order.Symbol}</TableCell>
              <TableCell>{order.TotalQty}</TableCell>
              <TableCell>{order.OrderType}</TableCell>
              <TableCell>{Number(order.LmtPrice).toFixed(2)}</TableCell>
              <TableCell>{Number(order.AuxPrice).toFixed(2)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
