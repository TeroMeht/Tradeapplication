'use client';

import { useState, useEffect } from 'react';
import HeaderBox from '@/components/HeaderBox';
import Calendar from '@/components/home/ExecutionsCalendar';
import TradesCalendar from '@/components/home/TradesCalendar';
import TradeKPI from '@/components/home/TradeKPIcomponent';
import SetupBarChart from '@/components/home/SetupCharting';

interface Execution {
  Symbol: string;
  Time: string;
  Date: string;
}

interface Trade {
  Symbol: string;
  Date: string;
  Setup: string;
  Rating: string;
}

const Home = () => {
  const loggedIn = { firstName: 'Tero' };
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [execRes, tradeRes] = await Promise.all([
          fetch('http://localhost:8080/api/executions'),
          fetch('http://localhost:8080/api/trades')
        ]);

        const execData = await execRes.json();
        const tradeData = await tradeRes.json();

        setExecutions(Array.isArray(execData) ? execData : []);
        setTrades(Array.isArray(tradeData) ? tradeData : []);
      } catch (err) {
        console.error('Failed to fetch data:', err);
        setExecutions([]);
        setTrades([]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

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

        {loading ? (
          <div className="mt-8 text-gray-500">Loading data...</div>
        ) : (
          <>
            {/* Calendar for Executions */}
            <div className="mt-8">
              <h3 className="text-lg font-semibold mb-2">Executions Calendar</h3>
              <Calendar
                currentMonth={currentMonth}
                onMonthChange={setCurrentMonth}
                executions={executions} // pass executions data
              />
            </div>

            {/* Calendar for Trades */}
            <div className="mt-12">
              <h3 className="text-lg font-semibold mb-2">Trades Calendar</h3>
              <TradesCalendar
                currentMonth={currentMonth}
                onMonthChange={setCurrentMonth}
                trades={trades} // pass trades data
              />
            </div>

            {/* KPI & Setup Chart */}
            <div className="mt-12">
              <SetupBarChart currentMonth={currentMonth} trades={trades} />
              <TradeKPI trades={trades} /> 
            </div>
          </>
        )}
      </div>
    </section>
  );
};

export default Home;
