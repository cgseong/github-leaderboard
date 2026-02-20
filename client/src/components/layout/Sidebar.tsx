import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { FaChartLine, FaCode, FaUserGraduate, FaTrophy, FaSignOutAlt } from 'react-icons/fa';
import { useAuth } from '../../context/AuthContext';
import clsx from 'clsx';

export const Sidebar: React.FC = () => {
    const { logout } = useAuth();
    const location = useLocation();

    const navItems = [
        { name: 'Dashboard', path: '/', icon: FaChartLine },
        { name: 'Leaderboard', path: '/leaderboard', icon: FaTrophy },
        { name: 'Projects', path: '/projects', icon: FaCode },
        { name: 'Students', path: '/students', icon: FaUserGraduate },
    ];

    return (
        <div className="flex flex-col w-64 bg-gray-800 border-r border-gray-700">
            <div className="flex items-center justify-center h-20 border-b border-gray-700">
                <h1 className="text-2xl font-bold text-blue-400">GH Rank</h1>
            </div>
            <nav className="flex-1 overflow-y-auto py-4">
                <ul className="space-y-2 px-2">
                    {navItems.map((item) => (
                        <li key={item.name}>
                            <Link
                                to={item.path}
                                className={clsx(
                                    "flex items-center gap-3 px-4 py-3 rounded-lg transition-colors",
                                    location.pathname === item.path
                                        ? "bg-blue-600 text-white"
                                        : "text-gray-400 hover:bg-gray-700 hover:text-white"
                                )}
                            >
                                <item.icon className="text-xl" />
                                <span className="font-medium">{item.name}</span>
                            </Link>
                        </li>
                    ))}
                </ul>
            </nav>
            <div className="p-4 border-t border-gray-700">
                <button
                    onClick={logout}
                    className="flex items-center gap-3 px-4 py-3 w-full rounded-lg text-gray-400 hover:bg-gray-700 hover:text-white transition-colors"
                >
                    <FaSignOutAlt className="text-xl" />
                    <span className="font-medium">Logout</span>
                </button>
            </div>
        </div>
    );
};
