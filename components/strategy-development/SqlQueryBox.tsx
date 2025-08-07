"use client";
import React, { useState } from 'react';

interface DataItem {
    Ticker: string;
    Date: string;
    Setup: string;
  }

// Define the SQLQueryBoxProps type for the props of this component
interface SQLQueryBoxProps {
  onDataFetched: (data: DataItem[]) => void; // Pass array of DataItem
}

const SQLQueryBox: React.FC<SQLQueryBoxProps> = ({ onDataFetched }) => {
  const [userId, setUserId] = useState('');

  const handleGenerateQuery = async () => {
    if (userId.trim()) {
      try {
        console.log(userId);
        // Send the userId as a query parameter to the backend API
        const response = await fetch(`http://localhost:8080/api/query?userId=${userId}`);
        const data = await response.json();

        // Ensure data is in the correct format and pass only the data array
        if (data && data.data && Array.isArray(data.data)) {
          onDataFetched(data.data); // Pass only the data array to parent component
        } else {
          console.error('Invalid data format');
        }

      } catch (error) {
        console.error("Error fetching SQL data:", error);
      }
    } else {
      console.error("userId is required");
    }
  };

  return (
    <section className='query-box p-4 border rounded-lg shadow-lg max-w-lg ml-0'>
      <h2 className='text-xl font-bold mb-2'>SQL Query Generator</h2>
      <div className='mb-4'>
        <label className='block mb-1 font-medium'>Trade id:</label>
        <input 
          type='text' 
          value={userId} 
          onChange={(e) => setUserId(e.target.value)}
          className='w-full p-2 border rounded'
          placeholder='Enter Trade id'
        />
      </div>
      <button 
        onClick={handleGenerateQuery} 
        className='bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600'
      >
        Ask for data
      </button>
    </section>
  );
};

export default SQLQueryBox;