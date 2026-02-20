import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { DashboardLayout } from '../components/layout/DashboardLayout';

interface User {
    username: string;
    avatarUrl: string;
    totalScore: number;
    major: string | null;
}

export const Leaderboard: React.FC = () => {
    const [users, setUsers] = useState<User[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchLeaderboard = async () => {
            try {
                const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:3000';
                const response = await axios.get(`${apiUrl}/api/leaderboard/overall`);
                setUsers(response.data);
            } catch (error) {
                console.error('Failed to fetch leaderboard', error);
            } finally {
                setLoading(false);
            }
        };
        fetchLeaderboard();
    }, []);

    return (
        <DashboardLayout>
            <div className="bg-gray-800 rounded-lg shadow-md border border-gray-700 overflow-hidden">
                <div className="p-6 border-b border-gray-700">
                    <h2 className="text-2xl font-bold text-white">Overall Leaderboard</h2>
                </div>

                {loading ? (
                    <div className="p-8 text-center text-gray-400">Loading...</div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead>
                                <tr className="bg-gray-700 text-gray-300">
                                    <th className="px-6 py-4 font-semibold">Rank</th>
                                    <th className="px-6 py-4 font-semibold">Student</th>
                                    <th className="px-6 py-4 font-semibold">Major</th>
                                    <th className="px-6 py-4 font-semibold text-right">Score</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-700">
                                {users.map((user, index) => (
                                    <tr key={user.username} className="hover:bg-gray-750 transition-colors">
                                        <td className="px-6 py-4 text-gray-400 font-medium">#{index + 1}</td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <img
                                                    src={user.avatarUrl}
                                                    alt={user.username}
                                                    className="w-8 h-8 rounded-full border border-gray-600"
                                                />
                                                <span className="font-medium text-gray-200">{user.username}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-gray-400">{user.major || '-'}</td>
                                        <td className="px-6 py-4 text-right font-bold text-blue-400">{user.totalScore}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </DashboardLayout>
    );
};
