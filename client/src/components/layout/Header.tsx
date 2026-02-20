import React from 'react';
import { useAuth } from '../../context/AuthContext';

export const Header: React.FC = () => {
    const { user } = useAuth();

    return (
        <header className="flex items-center justify-between h-20 px-6 bg-gray-800 border-b border-gray-700">
            <div className="flex items-center">
                {/* Breadcrumbs or Page Title could go here */}
                <h2 className="text-xl font-semibold text-gray-200">Overall Rankings</h2>
            </div>
            <div className="flex items-center gap-4">
                <span className="text-gray-300">Welcome, {user?.username || 'Student'}</span>
                {user?.avatarUrl && (
                    <img
                        src={user.avatarUrl}
                        alt="Profile"
                        className="w-10 h-10 rounded-full border-2 border-blue-500"
                    />
                )}
            </div>
        </header>
    );
};
