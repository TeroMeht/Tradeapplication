import React, { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";


// Interface for fetching tables
interface TableResponse {
  tables: string[];
}



const TablesList: React.FC = () => {
  const [tables, setTables] = useState<string[]>([]);
  const [, setLoading] = useState<boolean>(true);
  const [, setError] = useState<string | null>(null);
  const [selectedTable, setSelectedTable] = useState<string | null>(null); // State for selected table
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false); // State for modal visibility
  const [selectedTactic, setSelectedTactic] = useState<string>(""); // State for selected entry tactic
  const [stopLevels, setStopLevels] = useState<string[]>([]); // State for fetched stop levels
  const [apiResponse, setApiResponse] = useState<string | null>(null); // State for API response

  // Fetch tables (tickers) from backend
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
    const intervalId = setInterval(fetchTables, 10000); // Fetch every 10 seconds
    return () => clearInterval(intervalId);
  }, []);

  // Adjust font size based on the length of table name
  const getFontSize = (name: string) => {
    if (name.length <= 5) return "1rem";
    if (name.length <= 8) return "1rem";
    if (name.length <= 12) return "1rem";
    return "0.75rem";
  };

  // Handle card click (table selection)
  const handleCardClick = (table: string) => {
    setSelectedTable(table);   // Set the selected table (ticker)
    setIsModalOpen(true);      // Open the modal
    resetModalState();         // Reset modal-related states
  };

  // Reset modal states
  const resetModalState = () => {
    setSelectedTactic("");     // Clear the selected tactic
    setStopLevels([]);         // Clear the stop levels
    setApiResponse(null);      // Reset the API response message
  };

  // Toggle modal visibility
  const handleModalToggle = () => {
    setIsModalOpen(!isModalOpen);
  };

  const handleFetchStopLevels = async () => {
    if (!selectedTable) {
      setApiResponse("Please select a ticker to fetch stop levels.");
      return;
    }

    try {
      const response = await fetch(
        `http://127.0.0.1:8080/api/stoplevel?ticker=${selectedTable}`
      );
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

      const data = await response.json();
      console.log("Backend response:", data); // Log the response for debugging

      // Since the backend returns a float, you can directly use it
      if (data.stop_level !== undefined) {
        setStopLevels([data.stop_level]); // Store the stop level as a float in the state
        setApiResponse("Stop levels successfully fetched!");
      } else {
        setApiResponse("No stop levels found.");
        setStopLevels([]); // Clear stop levels if no stop level is found
      }
    } catch (error) {
      setApiResponse("Failed to fetch stop levels.");
      console.error("Error fetching stop levels:", error);
      setStopLevels([]); // Reset stop levels in case of an error
    }
  };

  // Handle order submission
  const handleOrderSubmit = () => {
    if (!selectedTactic || stopLevels.length === 0) {
      alert("Please select an entry tactic and fetch stop levels!");
      return;
    }

    // Handle the order submission logic here (e.g., call an API to create an order)
    alert(
      `Order for ${selectedTable} with tactic ${selectedTactic} and selected stop level has been generated!`
    );
    setIsModalOpen(false); // Close the modal after submitting
    setSelectedTactic(""); // Reset tactic selection
    setStopLevels([]); // Clear stop levels
  };

  return (
    <div className="p-3 w-full">
      <h2 className="text-xl font-semibold mb-4 text-gray-800 flex items-center justify-between">
        <span>LiveStreaming</span>
        <span className="text-gray-600 text-sm">{tables.length} tickers</span>
      </h2>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-10 gap-4 w-full">
        {tables.map((table) => (
          <Card
            key={table}
            className={`cursor-pointer transition-transform flex items-center justify-center bg-green-100 ${
              table === selectedTable ? "bg-green-300" : ""
            } hover:scale-50`} // Highlight selected table
            onClick={() => handleCardClick(table)} // Open the modal immediately on click
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

      {/* Modal for New Order */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-gray-800 bg-opacity-50 flex justify-center items-center z-50">
          <div className="bg-white p-6 rounded-md shadow-lg w-96">
            <h2 className="text-xl font-semibold text-gray-700 mb-4">Create New Order</h2>

            <p className="mb-4">
              Please select an entry tactic for the table <strong>{selectedTable}</strong>:
            </p>

            {/* Entry Tactic Selector */}
            <div className="mb-4">
              <label className="block text-sm font-semibold text-gray-700">
                Select Entry Tactic:
              </label>
              <select
                className="w-full p-2 border border-gray-300 rounded-md"
                value={selectedTactic}
                onChange={(e) => setSelectedTactic(e.target.value)}
              >
                <option value="">Select tactic</option>
                <option value="2barbreak">2Barbreak</option>
                <option value="ema9crossover">ema9Crossover</option>
              </select>
            </div>

            {/* Fetch Stop Levels Button */}
            <div className="mb-4">
              <button
                onClick={handleFetchStopLevels}
                className="w-full px-4 py-2 bg-blue-500 text-white rounded-md"
              >
                Fetch Stop Levels
              </button>
            </div>

            {/* Display fetched stop levels */}
            {Array.isArray(stopLevels) && stopLevels.length > 0 && (
              <div className="mb-4">
                <h3 className="text-lg font-semibold">Fetched Stop Level:</h3>
                <ul className="list-disc ml-5">
                  {stopLevels.map((level, index) => (
                    <li key={index} className="text-sm text-gray-700">
                      {level}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* API Response Message */}
            {apiResponse && <div className="mb-4 text-center text-gray-600">{apiResponse}</div>}

            <div className="flex justify-between">
              <button
                onClick={handleModalToggle}
                className="px-4 py-2 bg-gray-500 text-white rounded-md"
              >
                Cancel
              </button>
              <button
                onClick={handleOrderSubmit}
                className="px-4 py-2 bg-blue-500 text-white rounded-md"
              >
                Submit Order
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TablesList;
