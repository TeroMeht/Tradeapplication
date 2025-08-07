"use client"
import React, { useState, useEffect , useRef,useCallback} from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import PendingOrdersTable from "./PendingOrdersTable";

type Order_Alpaca ={
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
  const [selectedTiers, setSelectedTiers] = useState<Set<string>>(new Set());
  const [selectedOrder, setSelectedOrder] = useState<Order_Alpaca | null>(null); // Store selected order
  const [selectedTierValue, setSelectedTierValue] = useState<number | null>(null); // Store selected tier value
  const [message, setMessage] = useState("");
  const hasFetched = useRef(false); // Track if fetch has already happened

  // Function to fetch and update data
  const updateTable = useCallback(async () => {
    try {
      const response = await fetchPositions(); // Returns: { status, message, data? }
  
      if (response.status === "success") {
        const positions = Array.isArray(response.data) ? response.data : [];
  
        setPositions(positions);
  
        if (positions.length === 0) {
          setMessage(`${response.status}: ${response.message}`);
        } else {
          setMessage("");
        }
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


  // Handle tier selection and store the full order data
  const handleTierClick = (position: Order_Alpaca, tierNumber: number) => {
    setSelectedOrder(position); // Store the selected order
      // Retrieve the tier value dynamically based on tierNumber (tier_1, tier_2, etc.)
    const tierValue = position[`tier_${tierNumber}` as keyof Order_Alpaca];

    // If the tier value is a valid number, set it as a number; otherwise, set it as null
    const validTierValue = (typeof tierValue === "number" || tierValue === null) ? tierValue : null;
    setSelectedTierValue(validTierValue); // Set state with the validated value
    setSelectedTiers(() => {
      const updatedTiers = new Set<string>();
      const tierKey = `${position.symbol}-${tierNumber}`;
      if (updatedTiers.has(tierKey)) {
        updatedTiers.delete(tierKey); // Deselect if the tier is already selected
      } else {
        updatedTiers.add(tierKey); // Otherwise, select the tier
      }
      return updatedTiers;
    });
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
            <TableHead>Limit Price</TableHead>
            <TableHead>Stop Price</TableHead>
            <TableHead>Risk</TableHead>
            <TableHead>Tier 1</TableHead>
            <TableHead>Tier 2</TableHead>
            <TableHead>Tier 3</TableHead>
            <TableHead>Tier 4</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {positions.length === 0 ? (
            <TableRow>
              <TableCell colSpan={10} className="text-center text-lg text-gray-500">
                {message || "No orders to display."}
              </TableCell>
            </TableRow>
          ) : (
            positions.map((position, index) => (
              <TableRow key={index} className="cursor-pointer hover:bg-gray-100">
                <TableCell>{index + 1}</TableCell>
                <TableCell>{position.symbol}</TableCell>
                <TableCell>{position.latest_price}</TableCell>
                <TableCell>{position.limit_price ?? 0}</TableCell>
                <TableCell>{position.stop_price ?? 0}</TableCell>
                <TableCell>{position.risk}</TableCell>
                <TableCell
                  onClick={() => handleTierClick(position, 1)}
                  className={selectedTiers.has(`${position.symbol}-1`) ? "font-bold" : ""}
                >
                  {position.tier_1}
                </TableCell>
                <TableCell
                  onClick={() => handleTierClick(position, 2)}
                  className={selectedTiers.has(`${position.symbol}-2`) ? "font-bold" : ""}
                >
                  {position.tier_2}
                </TableCell>
                <TableCell
                  onClick={() => handleTierClick(position, 3)}
                  className={selectedTiers.has(`${position.symbol}-3`) ? "font-bold" : ""}
                >
                  {position.tier_3}
                </TableCell>
                <TableCell
                  onClick={() => handleTierClick(position, 4)}
                  className={selectedTiers.has(`${position.symbol}-4`) ? "font-bold" : ""}
                >
                  {position.tier_4}
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>

      {/* Update Table Button */}
      <div className="flex justify-center my-4">
        <button
          onClick={updateTable}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
        >
          Update Table
        </button>
      </div>
      {/* Pass selectedOrder to OrderDetails component */}
      <PendingOrdersTable selectedOrder={selectedOrder} selectedTierValue={selectedTierValue} />
    </div>
  );
};

export default PositionTable;
