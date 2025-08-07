import React, { useEffect, useState } from "react";
import {
  addMonths,
  subMonths,
  addDays,
  format,
  startOfMonth,
  endOfMonth,
  startOfWeek,
  endOfWeek,
  isSameMonth,
  isSameDay,
} from "date-fns";

interface Trade {
  Symbol: string;
  Date: string;
  Setup: string;
}

type DailyTrades = {
  [date: string]: { Symbol: string; Setup: string }[];
};

interface CalendarProps {
  currentMonth: Date;
  onMonthChange: (date: Date) => void;
}

const TradesCalendar: React.FC<CalendarProps> = ({ currentMonth, onMonthChange }) => {
  const today = new Date();
  const [tradesByDay, setTradesByDay] = useState<DailyTrades>({});

  const monthStart = startOfMonth(currentMonth);
  const monthEnd = endOfMonth(monthStart);
  const startDate = startOfWeek(monthStart, { weekStartsOn: 1 });
  const endDate = endOfWeek(monthEnd, { weekStartsOn: 1 });

  useEffect(() => {
    const fetchTrades = async () => {
      try {
        const response = await fetch("http://localhost:8080/api/trades");
        const data: Trade[] = await response.json();

        const grouped: DailyTrades = {};

        data.forEach((trade) => {
          const dateStr = format(new Date(trade.Date), "yyyy-MM-dd");
          if (!grouped[dateStr]) grouped[dateStr] = [];
          grouped[dateStr].push({ Symbol: trade.Symbol, Setup: trade.Setup });
        });

        setTradesByDay(grouped);
      } catch (err) {
        console.error("Failed to fetch trades:", err);
      }
    };

    fetchTrades();
  }, [currentMonth]);

  const handlePrevMonth = () => {
    onMonthChange(subMonths(currentMonth, 1));
  };

  const handleNextMonth = () => {
    onMonthChange(addMonths(currentMonth, 1));
  };

  const renderHeader = () => (
    <div className="flex items-center justify-between mb-2">
      <button onClick={handlePrevMonth} className="px-2 py-0.5 text-sm bg-gray-200 rounded hover:bg-gray-300">←</button>
      <h2 className="text-base font-medium">{format(currentMonth, "MMMM yyyy")}</h2>
      <button onClick={handleNextMonth} className="px-2 py-0.5 text-sm bg-gray-200 rounded hover:bg-gray-300">→</button>
    </div>
  );

  const renderDaysOfWeek = () => {
    const daysOfWeek = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
    return (
      <div className="grid grid-cols-7 text-center text-xs font-medium text-gray-600 mb-1">
        {daysOfWeek.map((day) => (
          <div key={day}>{day}</div>
        ))}
      </div>
    );
  };

  const renderCells = () => {
    const rows = [];
    let day = startDate;

    while (day <= endDate) {
      const weekCells = [];

      for (let i = 0; i < 7; i++) {
        const cloneDay = new Date(day);
        const dateKey = format(cloneDay, "yyyy-MM-dd");
        const trades = tradesByDay[dateKey];

        weekCells.push(
          <div
            key={cloneDay.toString()}
            className={`p-1 border rounded-lg h-20 flex flex-col justify-start items-start text-[10px] overflow-auto
              ${!isSameMonth(cloneDay, monthStart) ? "bg-gray-50 text-gray-400" : "bg-white"}
              ${isSameDay(cloneDay, today) ? "border-purple-500" : "border-gray-200"}
            `}
          >
            <div className={`font-semibold mb-0.5 ${isSameDay(cloneDay, today) ? "text-purple-600" : ""}`}>
              {format(cloneDay, "d")}
            </div>
            {trades &&
              trades.map((trade, index) => (
                <div key={index} className="text-[10px] whitespace-nowrap">
                  {trade.Symbol}: {trade.Setup}
                </div>
              ))}
          </div>
        );

        day = addDays(day, 1);
      }

      rows.push(
        <div key={`row-${day.toString()}`} className="grid grid-cols-7 gap-1 mb-1">
          {weekCells}
        </div>
      );
    }

    return <>{rows}</>;
  };

  return (
    <div className="max-w-3xl mx-auto p-2 bg-white rounded-xl shadow">
      {renderHeader()}
      {renderDaysOfWeek()}
      {renderCells()}
    </div>
  );
};

export default TradesCalendar;
