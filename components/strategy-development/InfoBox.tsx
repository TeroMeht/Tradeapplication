"use client";

import React from "react";

interface InfoBoxProps {
    fetchedData: {
        Ticker?: string;
        Date?: string;
        Setup?: string;
        Rating?: number;
        Comment?: string;
    } | null;
}

const InfoBox: React.FC<InfoBoxProps> = ({ fetchedData }) => {
    if (!fetchedData) return null; // Don't render if no data is available

    return (
        <div className="p-4 border rounded-lg shadow-lg bg-white max-w-md">
            {/* Title */}
            <h2 className="text-xl font-bold mb-2">Strategy Info</h2>

            {/* Display Data */}
            <div className="text-gray-700">
                <p><strong>Ticker:</strong> {fetchedData.Ticker || "N/A"}</p>
                <p><strong>Date:</strong> {fetchedData.Date || "N/A"}</p>
                <p><strong>Setup:</strong> {fetchedData.Setup || "N/A"}</p>
                <p><strong>Rating:</strong> {fetchedData.Rating ?? "N/A"}</p>
                <p><strong>Comment:</strong> {fetchedData.Comment || "No comments"}</p>
            </div>
        </div>
    );
};

export default InfoBox;
