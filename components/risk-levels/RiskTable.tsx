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
  Allocation: number;
  Symbol: string;
  AuxPrice: number;
  AvgCost: number;
  OpenRisk: number | string;
  Position: number;
  Size: number;
};

interface RiskTableProps {
  riskLevels: RiskLevel[];
  onUpdate?: () => void;
}

const RiskTableRow: React.FC<{ riskLevel: RiskLevel }> = ({ riskLevel }) => {
  const { Symbol, Allocation, AuxPrice, AvgCost, Size, Position, OpenRisk } =
    riskLevel;

  const formattedAllocation =
    Allocation != null ? `${Allocation.toFixed(2)}%` : "N/A";
  const formattedAuxPrice = AuxPrice != null ? AuxPrice.toFixed(2) : "N/A";
  const formattedAvgCost = AvgCost.toFixed(2);
  const formattedOpenRisk =
    typeof OpenRisk === "number" && isFinite(OpenRisk)
      ? OpenRisk.toFixed(2)
      : "No stop set";

  const openRiskClass =
    typeof OpenRisk !== "number" || !isFinite(OpenRisk)
      ? "text-red-600 font-bold"
      : "";

  const handleManageClick = () => {
    const url = `/risk-levels/${Symbol}/manage?` +
      `symbol=${encodeURIComponent(Symbol)}` +
      `&aux=${encodeURIComponent(AuxPrice)}` +
      `&allocation=${encodeURIComponent(Allocation)}` +
      `&avg=${encodeURIComponent(AvgCost)}` +
      `&pos=${encodeURIComponent(Position)}` +
      `&risk=${encodeURIComponent(OpenRisk)}`;
    window.open(url, "_blank", "width=500,height=600,left=200,top=200");
  };

  return (
    <TableRow className="cursor-pointer hover:bg-gray-100">
      <TableCell>{Symbol}</TableCell>
      <TableCell>{formattedAllocation}</TableCell>
            <TableCell>{formattedAuxPrice}</TableCell>
      <TableCell>{formattedAvgCost}</TableCell>
      <TableCell>{Size}</TableCell>
      <TableCell>{Position}</TableCell>
      <TableCell className={openRiskClass}>{formattedOpenRisk}</TableCell>
      <TableCell>
        <Button
          variant="secondary"
          size="sm"
          className="bg-indigo-500 text-white hover:bg-indigo-600"
          onClick={handleManageClick}
        >
          Manage
        </Button>
      </TableCell>
    </TableRow>
  );
};

const RiskTable: React.FC<RiskTableProps> = ({ riskLevels }) => {
  return (
    <div>
      <div className="flex justify-center my-4">
        <div className="text-xl font-bold">Position Management</div>
      </div>

      <Table>
        <TableHeader className="bg-[#f9fafb]">
          <TableRow>
             <TableHead>Symbol</TableHead>
            <TableHead>Allocation</TableHead>
            <TableHead>Aux Price</TableHead>
            <TableHead>Avg Cost</TableHead>
            <TableHead>Size</TableHead>
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
              <RiskTableRow key={index} riskLevel={riskLevel} />
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
};

export default RiskTable;
