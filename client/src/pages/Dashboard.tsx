import React from 'react';
import { DashboardLayout } from '../components/layout/DashboardLayout';
import { ActivityChart } from '../components/ActivityChart';

export const Dashboard: React.FC = () => {
    return (
        <DashboardLayout>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                <div className="bg-gray-800 p-6 rounded-lg shadow-md border border-gray-700">
                    <h3 className="text-xl font-semibold mb-2 text-gray-200">Total Score</h3>
                    <p className="text-4xl font-bold text-blue-500">1,234</p>
                    <p className="text-sm text-gray-400 mt-2">+120 this week</p>
                </div>
                <div className="bg-gray-800 p-6 rounded-lg shadow-md border border-gray-700">
                    <h3 className="text-xl font-semibold mb-2 text-gray-200">Global Rank</h3>
                    <p className="text-4xl font-bold text-green-500">#42</p>
                    <p className="text-sm text-gray-400 mt-2">Top 5%</p>
                </div>
                <div className="bg-gray-800 p-6 rounded-lg shadow-md border border-gray-700">
                    <h3 className="text-xl font-semibold mb-2 text-gray-200">Recent Activity</h3>
                    <ul className="space-y-2 text-gray-400">
                        <li>Opened PR in <strong>repo-a</strong></li>
                        <li>Merged 3 commits in <strong>repo-b</strong></li>
                        <li>Reviewed PR in <strong>repo-c</strong></li>
                    </ul>
                </div>
            </div>

            <div className="bg-gray-800 p-6 rounded-lg shadow-md border border-gray-700">
                <ActivityChart />
            </div>
        </DashboardLayout>
    );
};
