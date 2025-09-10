'use client';

import React, { useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export type LivestreamData = {
  Symbol: string;
  Date: string;
  Time: string;
  Open: number;
  High: number;
  Low: number;
  Close: number;
  Volume: number;
  VWAP: number;
  EMA9: number;
  Relatr: number;
};

export type LivestreamTableProps = {
  symbol: string;
  data: LivestreamData[]; // now data comes from parent
};

const LivestreamTable: React.FC<LivestreamTableProps> = ({ symbol, data }) => {
  const lastSevenRows = data.slice(-7);

  return (
    <div className="mb-6 w-full">
      <div className="flex items-center mb-4">
        <div className="w-4 h-4 rounded-full mr-2 bg-green-500" title="Displaying live data" />
        <span className="text-lg font-semibold">Symbol: {symbol}</span>
      </div>

      <Table>
        <TableHeader className="bg-[#f9fafb]">
          <TableRow>
            <TableHead>#</TableHead>
            <TableHead>Symbol</TableHead>
            <TableHead>Time</TableHead>
            <TableHead>Close</TableHead>
            <TableHead>High</TableHead>
            <TableHead>VWAP</TableHead>
            <TableHead>EMA9</TableHead>
            <TableHead>Relatr</TableHead>
          </TableRow>
        </TableHeader>

        <TableBody>
          {lastSevenRows.length === 0 ? (
            <TableRow>
              <TableCell colSpan={8} className="text-center text-gray-500">
                No live data yet
              </TableCell>
            </TableRow>
          ) : (
            lastSevenRows.map((row, index) => (
              <TableRow key={index} className="hover:bg-gray-100">
                <TableCell>{index + 1}</TableCell>
                <TableCell>{row.Symbol}</TableCell>
                <TableCell>{row.Time}</TableCell>
                <TableCell>{row.Close.toFixed(2)}</TableCell>
                <TableCell>{row.High.toFixed(2)}</TableCell>
                <TableCell>{row.VWAP.toFixed(2)}</TableCell>
                <TableCell>{row.EMA9.toFixed(2)}</TableCell>
                <TableCell>{row.Relatr.toFixed(2)}</TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
};

export default LivestreamTable;
