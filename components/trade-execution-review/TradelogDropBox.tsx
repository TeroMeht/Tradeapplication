"use client";  // Indicating this is a client-side component

import React, { useState } from "react";

export const TradelogDropBox = () => {
  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState("");

  // Handle file drop event
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();

    setDragging(false);  // Reset dragging state

    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles.length > 0) {
      const file = droppedFiles[0];
      if (file.name.endsWith(".tlg")) {
        setFile(file);
        setMessage(`File "${file.name}" is ready for upload.`);
      } else {
        setMessage("Please upload a file with the .tlg extension.");
      }
    }
  };

  // Handle file drag over event (when the user is dragging over the drop area)
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragging(true);
  };

  // Handle file drag leave event (when the user leaves the drop area)
  const handleDragLeave = () => {
    setDragging(false);
  };

  // Handle file upload
  const handleUpload = () => {
    if (file) {
      // Perform file upload or processing here
      setMessage(`Uploading "${file.name}"...`);
      // You can send the file to a backend here if required
      // For example, use FormData to upload the file to an API.
    }
  };

  return (
    <div
      className={`dropbox-container ${dragging ? "dragging" : ""}`}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
    >
      <div className="dropbox-content">
        <h3 className="text-center text-lg font-semibold">Drop your TLG file here</h3>
        <p className="text-center text-gray-500">Drag and drop a file or click to browse</p>

        {file && (
          <div className="file-info">
            <p><strong>File:</strong> {file.name}</p>
            <p><strong>Size:</strong> {file.size} bytes</p>
          </div>
        )}

        {message && <p className="message">{message}</p>}

        <button
          onClick={handleUpload}
          disabled={!file}
          className={`upload-button ${!file ? "disabled" : ""}`}
        >
          Upload
        </button>
      </div>

      <style jsx>{`
        .dropbox-container {
          border: 2px dashed #ccc;
          padding: 20px;
          text-align: center;
          width: 100%;
          max-width: 400px;
          margin: auto;
          border-radius: 8px;
          background-color: #f9fafb;
        }
        .dropbox-container.dragging {
          border-color: #4c9dff;
        }
        .dropbox-content {
          display: flex;
          flex-direction: column;
          align-items: center;
        }
        .file-info {
          margin-top: 10px;
          padding: 5px;
          background-color: #eef1f7;
          border-radius: 5px;
        }
        .message {
          margin-top: 10px;
          color: #f00;
        }
        .upload-button {
          margin-top: 15px;
          padding: 10px 20px;
          background-color: #4c9dff;
          color: white;
          border: none;
          border-radius: 5px;
          cursor: pointer;
        }
        .upload-button.disabled {
          background-color: #ccc;
          cursor: not-allowed;
        }
        .upload-button:hover:enabled {
          background-color: #0066cc;
        }
      `}</style>
    </div>
  );
};
