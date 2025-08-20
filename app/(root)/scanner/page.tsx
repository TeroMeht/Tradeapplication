"use client";

import HeaderBox from "@/components/HeaderBox";
import ScannerTable from "@/components/scanner/ScanResults"

const Scanner = () => {
  return (

      <div className="home-content">
        {/* Page header */}
        <header className="home-header">
          <HeaderBox
            type="greeting"
            title="Scanner"
            subtext="Request IB scanner results"
          />
        </header>

        {/* Scanner table component */}
        <div className="mt-6">
          <ScannerTable />
        </div>
      </div>

  );
};

export default Scanner;