'use client';

import { useState } from 'react';
import HeaderBox from '@/components/HeaderBox';
import Calendar from '@/components/home/CalendarComponent';
import TradesCalendar from '@/components/home/TradesCalendar';
import TradeKPI from '@/components/home/TradeKPIcomponent';
import SetupBarChart from '@/components/home/SetupCharting';

const Home = () => {
  const loggedIn = { firstName: 'Tero' };
  const [currentMonth, setCurrentMonth] = useState(new Date());

  return (
    <section className="home">
      <div className="home-content">
        <header className="home-header">
          <HeaderBox
            type="greeting"
            title="Welcome"
            user={loggedIn.firstName || 'Guest'}
            subtext="Manage and review performance of Mehtanen Capital trading business"
          />
        </header>

        {/* Calendar for Executions */}
        <div className="mt-8">
          <h3 className="text-lg font-semibold mb-2">Executions Calendar</h3>
          <Calendar currentMonth={currentMonth} onMonthChange={setCurrentMonth} />
        </div>

        {/* Calendar for Trades */}
        <div className="mt-12">
          <h3 className="text-lg font-semibold mb-2">Trades Calendar</h3>
          <TradesCalendar currentMonth={currentMonth} onMonthChange={setCurrentMonth} />
        </div>

        {/* KPI & Setup Chart */}
        <div className="mt-12">
          <SetupBarChart currentMonth={currentMonth} />
          <TradeKPI />
        </div>
      </div>
    </section>
  );
};

export default Home;
