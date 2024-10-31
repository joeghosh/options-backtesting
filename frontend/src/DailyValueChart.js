import React from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const DailyValueChart = ({ dailyValues }) => {
  console.log('DAILY VALUESa', dailyValues);
  const labels = dailyValues.map((day) => day.date);
  const totalValues = dailyValues.map((day) => day.total_value);
  console.log(dailyValues);

  const data = {
    labels: labels,
    datasets: [
      {
        label: 'Total Value',
        data: totalValues,
        borderColor: 'rgba(75, 192, 192, 1)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        fill: true,
      },
    ],
  };

  const options = {
    scales: {
      x: {
        title: {
          display: true,
          text: 'Date',
        },
      },
      y: {
        title: {
          display: true,
          text: 'Value ($)',
        },
      },
    },
  };

  return <Line data={data} options={options} />;
};

export default DailyValueChart;
