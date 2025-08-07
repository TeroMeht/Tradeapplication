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

interface Execution {
  Symbol: string;
  Time: string;
  Date: string;
}

type DailyExecutions = {
  [date: string]: Record<string, number>;
};

interface CalendarProps {
  currentMonth: Date;
  onMonthChange: (date: Date) => void;
}

const Calendar: React.FC<CalendarProps> = ({ currentMonth, onMonthChange }) => {
  const today = new Date();
  const [executionsByDay, setExecutionsByDay] = useState<DailyExecutions>({});

  const monthStart = startOfMonth(currentMonth);
  const monthEnd = endOfMonth(monthStart);
  const startDate = startOfWeek(monthStart, { weekStartsOn: 1 });
  const endDate = endOfWeek(monthEnd, { weekStartsOn: 1 });

  useEffect(() => {
    const fetchExecutions = async () => {
      try {
        const response = await fetch("http://localhost:8080/api/executions");
        const data: Execution[] = await response.json();

        const grouped: DailyExecutions = {};

        data.forEach((exec) => {
          const dateTimeStr = `${exec.Date}T${exec.Time}`;
          const dateStr = format(new Date(dateTimeStr), "yyyy-MM-dd");
          if (!grouped[dateStr]) grouped[dateStr] = {};
          if (!grouped[dateStr][exec.Symbol]) grouped[dateStr][exec.Symbol] = 0;
          grouped[dateStr][exec.Symbol] += 1;
        });

        setExecutionsByDay(grouped);
      } catch (err) {
        console.error("Failed to fetch executions:", err);
      }
    };

    fetchExecutions();
  }, [currentMonth]);

  const handlePrevMonth = () => {
    onMonthChange(subMonths(currentMonth, 1));
  };

  const handleNextMonth = () => {
    onMonthChange(addMonths(currentMonth, 1));
  };

  const renderHeader = () => (
    <div className="flex items-center justify-between mb-2">
      <button onClick={handlePrevMonth} className="px-2 py-0.5 text-sm bg-gray-200 rounded hover:bg-gray-300">
        ←
      </button>
      <h2 className="text-base font-medium">{format(currentMonth, "MMMM yyyy")}</h2>
      <button onClick={handleNextMonth} className="px-2 py-0.5 text-sm bg-gray-200 rounded hover:bg-gray-300">
        →
      </button>
    </div>
  );

  const renderDaysOfWeek = () => {
    const daysOfWeek = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
    return (
      <div className="grid grid-cols-8 text-center text-xs font-medium text-gray-600 mb-1">
        {daysOfWeek.map((day) => (
          <div key={day}>{day}</div>
        ))}
        <div className="text-[10px] font-bold text-blue-700">Total</div>
      </div>
    );
  };

  const renderCells = () => {
    const rows = [];
    let day = startDate;

    while (day <= endDate) {
      let days: JSX.Element[] = [];
      let weeklyTotal = 0;

      for (let i = 0; i < 7; i++) {
        const cloneDay = new Date(day);
        const dateKey = format(cloneDay, "yyyy-MM-dd");
        const executions = executionsByDay[dateKey];

        if (executions) {
          const dayTotal = Object.values(executions).reduce((sum, count) => sum + count, 0);
          weeklyTotal += dayTotal;
        }

        days.push(
          <div
            key={cloneDay.toString()}
            className={`p-0.5 border rounded-lg h-16 flex flex-col justify-start items-start text-[10px] overflow-auto
              ${!isSameMonth(cloneDay, monthStart) ? "bg-gray-50 text-gray-400" : "bg-white"}
              ${isSameDay(cloneDay, today) ? "border-blue-500" : "border-gray-200"}
            `}
          >
            <div className={`font-semibold mb-0.5 ${isSameDay(cloneDay, today) ? "text-blue-600" : ""}`}>
              {format(cloneDay, "d")}
            </div>
            {executions &&
              Object.entries(executions).map(([symbol, count]) => (
                <div key={symbol} className="text-[10px]">
                  {symbol}: {count}
                </div>
              ))}
          </div>
        );

        day = addDays(day, 1);
      }

      days.push(
        <div
          key={`summary-${day.toString()}`}
          className="p-1 h-16 flex items-center justify-center text-[10px] font-semibold bg-blue-50 border border-blue-200 rounded-lg text-blue-700"
        >
          {weeklyTotal} total
        </div>
      );

      rows.push(
        <div key={`row-${day.toString()}`} className="grid grid-cols-8 gap-1 mb-1">
          {days}
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

export default Calendar;
