import React, { useState } from 'react';
import axios from 'axios';
import DailyValueChart from './DailyValueChart.js';

const App = () => {
  const [startDate, setStartDate] = useState('');
  const [duration, setDuration] = useState(30);
  const [initialCash, setInitialCash] = useState(10000);
  const [results, setResults] = useState(null);
  const [dailyValues, setDailyValues] = useState([]);

  const runBacktest = async () => {
    try {
      const response = await axios.post('http://localhost:5000/backtest', {
        start_date: startDate,
        duration: duration,
        cash: initialCash,
      });
      setResults(response.data);
      setDailyValues(response.data.daily_values);
    } catch (error) {
      console.error('Error running backtest:', error);
    }
  };

  return (
    <div className='App'>
      <h1>Options Straddle Strategy Backtest</h1>
      <div>
        <label>Start Date (YYYY-MM-DD):</label>
        <input
          type='date'
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
        />
      </div>
      <div>
        <label>Duration (Days):</label>
        <input
          type='number'
          value={duration}
          onChange={(e) => setDuration(e.target.value)}
        />
      </div>
      <div>
        <label>Initial Cash ($):</label>
        <input
          type='number'
          value={initialCash}
          onChange={(e) => setInitialCash(e.target.value)}
        />
      </div>
      <button onClick={runBacktest}>Run Backtest</button>

      {results && (
        <div>
          <h2>Results</h2>
          <p>Final Cash: ${results.final_cash.toFixed(2)}</p>
          <p>PnL: ${results.pnl.toFixed(2)}</p>
          <DailyValueChart dailyValues={dailyValues} />
        </div>
      )}
    </div>
  );
};

export default App;
