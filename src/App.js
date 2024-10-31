import React, { useState } from 'react';
import axios from 'axios';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import './App.scss';
import DailyValueChart from './DailyValueChart.js';

const strategies = ['Straddle']; // Add more strategies as needed

const App = () => {
  const [startDate, setStartDate] = useState(null);
  const [duration, setDuration] = useState(30);
  const [initialCash, setInitialCash] = useState(10000);
  const [strategy, setStrategy] = useState(strategies[0]);
  const [results, setResults] = useState(null);
  const [dailyValues, setDailyValues] = useState([]);

  const runBacktest = async () => {
    try {
      const response = await axios.post('http://localhost:5000/backtest', {
        start_date: startDate ? startDate.toISOString().split('T')[0] : '',
        duration: duration,
        cash: initialCash,
        strategy: strategy,
      });
      setResults(response.data);
      setDailyValues(response.data.daily_values);
    } catch (error) {
      console.error('Error running backtest:', error);
    }
  };

  return (
    <div className='app'>
      <h1>Options Strategy Backtest</h1>
      <div className='input-container'>
        <div className='input-group'>
          <label>Start Date:</label>
          <DatePicker
            selected={startDate}
            onChange={(date) => setStartDate(date)}
            dateFormat='yyyy-MM-dd'
            placeholderText='Select a date'
          />
        </div>
        <div className='input-group'>
          <label>Duration (Days):</label>
          <input
            type='number'
            value={duration}
            onChange={(e) => setDuration(e.target.value)}
            min='1'
          />
        </div>
        <div className='input-group'>
          <label>Initial Cash ($):</label>
          <input
            type='number'
            value={initialCash}
            onChange={(e) => setInitialCash(e.target.value)}
            min='0'
          />
        </div>
        <div className='input-group'>
          <label>Strategy:</label>
          <select
            value={strategy}
            onChange={(e) => setStrategy(e.target.value)}
          >
            {strategies.map((strat, index) => (
              <option key={index} value={strat}>
                {strat}
              </option>
            ))}
          </select>
        </div>
        <button className='run-button' onClick={runBacktest}>
          Run Backtest
        </button>
      </div>

      {results && (
        <div className='results-container'>
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
