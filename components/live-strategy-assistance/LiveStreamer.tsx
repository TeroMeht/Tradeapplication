"use client";

import React, { useState, useEffect , useRef,useCallback} from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"; // Assuming you have the UI components in this path

type LivestreamData = {
  Ticker: string;
  Date: string;  // Format as YYYY-MM-DD
  Time: string;  // Format as HH:mm
  Open: number;
  High: number;
  Low: number;
  Close: number;
  Volume: number;
  VWAP: number;
  EMA9: number;
  Relatr:number;
};

const fetchLivestreamData = async (): Promise<LivestreamData[]> => {
  try {
    const response = await fetch("http://localhost:8080/api/livestream");

    if (!response.ok) {
      throw new Error("Failed to fetch data");
    }

    const data = await response.json();
    return data;  // Data should already be in the required format
  } catch (error) {
    console.error("Error fetching live stream data:", error);
    throw error;
  }
};

const LivestreamTable = () => {
  const [livestreamData, setLivestreamData] = useState<LivestreamData[]>([]);
  const [message, setMessage] = useState("");
  const prevDataLengthRef = useRef(0); // Using useRef to track previous data length
  const [flashRow, setFlashRow] = useState<number | null>(null); // Store index of the row that should flash
  const [streamerRunning, setStreamerRunning] = useState(false); // Track streamer status
  const audioRef = useRef<HTMLAudioElement | null>(null); 




  // Fetch and update data
  // Check if the streamer is running
  const checkStreamerStatus = async () => {
    try {
      const statusRes = await fetch("http://localhost:8080/check-streamer");
      const statusData = await statusRes.json();
      setStreamerRunning(statusData.running);
    } catch (error) {
      console.error("Error checking streamer status:", error);
      setStreamerRunning(false);
    }
  };

  // Fetch and update data
  const updateTable = useCallback(async () => {
    if (!streamerRunning) {
      setMessage("Streamer is not running, new data not coming in.");
      return; // Don't proceed with data fetch if the streamer is not running
    }

    try {
      const data = await fetchLivestreamData();

      if (data.length === 0) {
        setMessage("No live stream data available.");
      } else {
        console.log("Data Length:", data.length);

        // Use the ref to track previous data length for comparison
        if (data.length > prevDataLengthRef.current) {
          console.log("New data detected, flashing row");

          // Set flashRow to the last index in the data
          const newRowIndex = data.length - 1;
          setFlashRow(newRowIndex); // Trigger flash effect on last row

          // Play the audio effect
          if (audioRef.current) {
            audioRef.current.currentTime = 0;
            audioRef.current.play().catch((err) => {
              console.warn("Audio play failed:", err);
            });
          }

          // Reset the flash effect after 2 seconds
          setTimeout(() => {
            setFlashRow(null);
          }, 2000);
        }

        // Update previous data length to the new length
        prevDataLengthRef.current = data.length;

        // Update livestream data with the new data
        setLivestreamData(data);
        setMessage(""); // Clear any previous message
      }
    } catch {
      setMessage("Error loading data");
    }
  }, [streamerRunning]);

  // Initial data load and set interval to update every 10 seconds
  useEffect(() => {
    checkStreamerStatus(); // Check if the streamer is running when the component mounts
    const interval = setInterval(() => {
      checkStreamerStatus(); // Check the streamer status periodically
      if (streamerRunning) {
        updateTable(); // Fetch new data every 10 seconds if streamer is running
      }
    }, 5000); // 10 seconds interval

    // Cleanup the interval on component unmount
    return () => clearInterval(interval);
  }, [streamerRunning,updateTable]);

  // To show only the last 7 rows
  const lastSevenRows = livestreamData.slice(-7); // Get the last 7 rows of the data
  return (
    <div>
      {/* 🔊 Hidden audio element */}
      <audio ref={audioRef} src='/sounds/alarm.mp3' preload="auto" />
      {/* Streamer status indicator with text */}
      <div className="flex items-center mb-4">
        <div
          className={`w-4 h-4 rounded-full mr-2 ${streamerRunning ? "bg-green-500" : "bg-red-500"}`}
          title={streamerRunning ? "Streamer is Running" : "Streamer is Offline"}
        ></div>
        <span className="text-lg font-semibold">{streamerRunning ? "Streamer Running" : "Streamer Offline"}</span>
      </div>
      <Table>
        <TableHeader className="bg-[#f9fafb]">
          <TableRow>
            <TableHead>#</TableHead>
            <TableHead>Ticker</TableHead>
            <TableHead>Time</TableHead>
            <TableHead>Close</TableHead>
            <TableHead>High</TableHead>
            <TableHead>VWAP</TableHead>
            <TableHead>EMA9</TableHead>
            <TableHead>Relatr</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {livestreamData.length === 0 ? (
            // Render an empty row with a message when there is no data
            <TableRow>
              <TableCell colSpan={8} className="text-center text-lg text-gray-500">
                {message || "No data available."}
              </TableCell>
            </TableRow>
          ) : (
            lastSevenRows.map((data, index) => (
              <TableRow
                key={index}
                className={`hover:bg-gray-100 ${flashRow === livestreamData.indexOf(data) ? "flash-effect" : ""}`}
              >
                <TableCell>{livestreamData.indexOf(data) + 1}</TableCell>
                <TableCell>{data.Ticker}</TableCell>
                <TableCell>{data.Time}</TableCell>
                <TableCell>{data.Close.toFixed(2)}</TableCell>
                <TableCell>{data.High.toFixed(2)}</TableCell> 
                <TableCell>{data.VWAP.toFixed(2)}</TableCell>
                <TableCell>{data.EMA9.toFixed(2)}</TableCell>
                <TableCell>{data.Relatr.toFixed(2)}</TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>

    </div>
  );
};

export default LivestreamTable;
