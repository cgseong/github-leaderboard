import React from 'react';
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
import { Line } from 'react-chartjs-2';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
);

const options = {
    responsive: true,
    plugins: {
        legend: {
            position: 'top' as const,
            labels: {
                color: '#9ca3af',
            },
        },
        title: {
            display: true,
            text: 'Activity Last 7 Days',
            color: '#e5e7eb',
            font: {
                size: 16,
            },
        },
    },
    scales: {
        y: {
            grid: {
                color: '#374151',
            },
            ticks: {
                color: '#9ca3af',
            },
        },
        x: {
            grid: {
                color: '#374151',
            },
            ticks: {
                color: '#9ca3af',
            },
        },
    },
};

const labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

export const ActivityChart: React.FC = () => {
    // Mock data for now
    const data = {
        labels,
        datasets: [
            {
                label: 'Commits',
                data: [12, 19, 3, 5, 2, 3, 10],
                borderColor: 'rgb(59, 130, 246)', // Blue 500
                backgroundColor: 'rgba(59, 130, 246, 0.5)',
                tension: 0.3,
            },
            {
                label: 'PRs',
                data: [2, 3, 20, 5, 1, 4, 2],
                borderColor: 'rgb(16, 185, 129)', // Green 500
                backgroundColor: 'rgba(16, 185, 129, 0.5)',
                tension: 0.3,
            },
        ],
    };

    return <Line options={options} data={data} />;
};
