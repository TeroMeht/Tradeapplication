"use client";

import React from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";

type RiskLevel = {
  OrderId: number;
  Symbol: string;
  AuxPrice: number;
  AvgCost: number;
  OpenRisk: number | string;
  Position: number;
};

interface RiskTableProps {
  riskLevels: RiskLevel[];
  onUpdate: () => void; // callback to refresh data
}

const RiskTable: React.FC<RiskTableProps> = ({ riskLevels, onUpdate }) => {
  return (
    <div>
      <div className="relative flex items-center justify-center my-4">
        {/* Update Table button on the left */}
        <Button
          onClick={onUpdate}
          className="absolute left-0 bg-blue-500 text-white hover:bg-blue-600 px-4 py-2 rounded"
        >
          Update Table
        </Button>

        {/* Centered header */}
        <div className="text-xl font-bold">Position management</div>
      </div>

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
            <TableHead>Actions</TableHead>
          </TableRow>
        </TableHeader>

        <TableBody>
          {riskLevels.length === 0 ? (
            <TableRow>
              <TableCell colSpan={8} className="text-center text-gray-500">
                No risk data available.
              </TableCell>
            </TableRow>
          ) : (
            riskLevels.map((riskLevel, index) => (
              <TableRow key={index} className="cursor-pointer hover:bg-gray-100">
                <TableCell>{index + 1}</TableCell>
                <TableCell>{riskLevel.OrderId}</TableCell>
                <TableCell>{riskLevel.Symbol}</TableCell>
                <TableCell>
                  {riskLevel.AuxPrice != null
                    ? riskLevel.AuxPrice.toFixed(2)
                    : "N/A"}
                </TableCell>
                <TableCell>{riskLevel.AvgCost.toFixed(2)}</TableCell>
                <TableCell>{riskLevel.Position}</TableCell>
                <TableCell
                  style={{
                    fontWeight: "bold",
                    color:
                      typeof riskLevel.OpenRisk !== "number" ||
                      !isFinite(riskLevel.OpenRisk as number)
                        ? "red"
                        : undefined,
                  }}
                >
                  {typeof riskLevel.OpenRisk === "number" &&
                  isFinite(riskLevel.OpenRisk as number)
                    ? (riskLevel.OpenRisk as number).toFixed(2)
                    : "Sulla ei ole stoppia"}
                </TableCell>
                <TableCell>
                  <Button
                    variant="secondary"
                    size="sm"
                    className="bg-indigo-500 text-white hover:bg-indigo-600"
                    onClick={() => {
                      const url =
                        `/risk-levels/${riskLevel.Symbol}/manage` +
                        `?symbol=${encodeURIComponent(riskLevel.Symbol)}` +
                        `&aux=${encodeURIComponent(riskLevel.AuxPrice)}` +
                        `&orderid=${encodeURIComponent(riskLevel.OrderId)}` +
                        `&avg=${encodeURIComponent(riskLevel.AvgCost)}` +
                        `&pos=${encodeURIComponent(riskLevel.Position)}` +
                        `&risk=${encodeURIComponent(riskLevel.OpenRisk)}`;

                      window.open(
                        url,
                        "_blank",
                        "width=500,height=600,left=200,top=200"
                      );
                    }}
                  >
                    Manage
                  </Button>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
};

export default RiskTable;
