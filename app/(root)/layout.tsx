'use client'

import Sidebar from "@/components/Sidebar";
import RightSidebar from "@/components/RightSideBar";
// import DailyPnl from "@/components/DailyPnL";
import { useState, useEffect } from "react";

type AlarmData = {
  Symbol: string;
  Time: string;
  Alarm: string;
  Date: string;
};

type PortfolioControlData = {
  // Define the structure of portfolio control data here if necessary
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const [alarms, setAlarms] = useState<AlarmData[]>([]);
  const [streamerRunning, setStreamerRunning] = useState<boolean>(true); // Track streamer status

  // Check if the streamer is running
  const checkStreamer = async (): Promise<boolean> => {
    try {
      const statusRes = await fetch("http://localhost:8080/check-streamer");
      const statusData = await statusRes.json();
      return statusRes.ok && statusData.running;
    } catch (error) {
      console.error("Error checking streamer status:", error);
      return false;
    }
  };

  const fetchAlarms = async (): Promise<AlarmData[]> => {
    try {
      const response = await fetch("http://localhost:8080/api/alarms");
      if (!response.ok) throw new Error("Failed to fetch alarms");
      return await response.json();
    } catch (error) {
      console.error("Error fetching alarms:", error);
      return [];
    }
  };



  useEffect(() => {
    const updateAlarmsAndPortfolio = async () => {
      const isRunning = await checkStreamer();
      setStreamerRunning(isRunning);

      if (isRunning) {
        const fetchedAlarms = await fetchAlarms();
        setAlarms(fetchedAlarms);

      } else {
        console.warn("Streamer not running. Skipping alarm fetch.");
        setAlarms([]); // Optional: clear alarms if streamer stops
      }
    };

    updateAlarmsAndPortfolio(); // Initial check
    const intervalId = setInterval(updateAlarmsAndPortfolio, 60 * 1000); // Every minute

    return () => clearInterval(intervalId); // Clean up interval on unmount
  }, []);

  return (
    <main className="flex h-screen w-full font-inter">
      {/* Sidebar with portfolio control system data */}
      <Sidebar />
      
      {/* Main content area */}
      <div className="flex-grow p-1">{children}</div>

      {/* Right Sidebar, passing alarms data */}
      <RightSidebar alarms={alarms} pageSpecific={true} streamerRunning={streamerRunning} />
      
      {/* Daily PnL Section
      <section className="absolute bottom-4 right-4 bg-white shadow-lg p-4 rounded-lg border z-50">
        <h2 className="text-xl font-semibold mb-2">Daily PnL</h2>
        <DailyPnl />
      </section> */}
    </main>
  );
}
